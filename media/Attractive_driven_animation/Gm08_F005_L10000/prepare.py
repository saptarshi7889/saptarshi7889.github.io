"""Sample local compressed configurations; retain small resumable density caches."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import numpy as np

SOURCE = Path('/run/media/sap/Seagate/Attractive_impurity_raw_data/Codes/Impurity_Thomas_Data/Delta_Impurity_optimum/Attractive_impurity/Attractive_driven/G-0.8/m0.333/F0.05_L10000')
OUTPUT = Path(__file__).resolve().parent
CACHE = OUTPUT/'density_cache'
LENGTH = 10000
DX = 0.00025
DT = 0.01
WINDOW = 500
STRIDE = 200
ZERO_COUNT = 3
DENSITY_WORKERS = 6
READ_BYTES = 4 * 1024 * 1024
POSITION_TOLERANCE = 0.000051


def sampled_rows(stream, first, stop):
    row, pending, selected = 0, b'', []
    while row < stop:
        chunk = stream.read(READ_BYTES)
        if not chunk:
            raise ValueError('Configuration ends before requested window')
        data = pending + chunk
        end = data.rfind(b'\n') + 1
        complete, pending = data[:end], data[end:]
        count = complete.count(b'\n')
        if row + count > first:
            start = max(first, row)
            offset = (-(start-first)) % STRIDE
            lines = complete.splitlines()
            selected.extend(lines[i-row] for i in range(start+offset, min(stop, row+count), STRIDE))
        row += count
    return selected


def main():
    CACHE.mkdir(exist_ok=True)
    parts = sorted([(np.loadtxt(f, ndmin=2)[:, :2], f.name)
                    for f in SOURCE.glob('impurity_velocity*.gz')], key=lambda item: item[0][0, 0])
    stitched = []
    for i, (part, _) in enumerate(parts):
        assert np.all(np.diff(part[:, 0]) > 0)
        stitched.append(part[part[:, 0] < parts[i+1][0][0, 0]] if i+1 < len(parts) else part)
    velocity = np.concatenate(stitched)
    assert np.isfinite(velocity).all() and np.all(np.diff(velocity[:, 0]) > 0)
    # Exclude the initial rest state; count subsequent sign changes, including exact zeros.
    nonzero = np.flatnonzero(velocity[:, 1])
    crossings = []
    for left, right in zip(nonzero[:-1], nonzero[1:]):
        t0, v0 = velocity[left]
        t1, v1 = velocity[right]
        if v0*v1 < 0:
            crossings.append(float(t0-v0*(t1-t0)/(v1-v0)))
    endpoint = crossings[ZERO_COUNT-1]
    velocity = np.vstack((velocity[velocity[:, 0] < endpoint], [endpoint, 0]))
    snapshots = sorted([(float(re.search(r'time(.*?)dt', f.name)[1]), f)
                        for f in SOURCE.glob('Phi_solution*.gz')])
    upper = next(t for t, _ in snapshots if t >= endpoint)
    snapshots = [(t, f) for t, f in snapshots if t <= upper]
    first, stop = round((LENGTH/2-WINDOW)/DX), round((LENGTH/2+WINDOW)/DX)
    positions = np.arange(first, stop, STRIDE)*DX-LENGTH/2
    def load_snapshot(snapshot):
        time, path = snapshot
        cache = CACHE/f't{time:g}.npy'
        if cache.exists():
            density = np.load(cache)
        else:
            with subprocess.Popen(['gzip', '-dc', str(path)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as decoder:
                field = np.loadtxt(sampled_rows(decoder.stdout, first, stop))
                decoder.stdout.close()
                decoder.terminate()  # The unneeded right half of the box is deliberately not decoded.
                decoder.wait()
            assert field.shape == (len(positions), 3)
            assert np.allclose(field[:, 0], positions, atol=POSITION_TOLERANCE, rtol=0)
            density = field[:, 1]**2 + field[:, 2]**2
            temporary = cache.with_suffix('.tmp.npy')
            np.save(temporary, density)
            temporary.replace(cache)
        assert density.shape == positions.shape and np.isfinite(density).all()
        print(f'Density cached: t={time:g}', flush=True)
        return density

    with ThreadPoolExecutor(max_workers=DENSITY_WORKERS) as pool:
        densities = list(pool.map(load_snapshot, snapshots))
    times = np.array([t for t, _ in snapshots])
    densities = np.array(densities)
    bracket = times[-2:].tolist()
    weight = (endpoint-times[-2])/(times[-1]-times[-2])
    densities[-1] = (1-weight)*densities[-2] + weight*densities[-1]
    saved_times = times[times <= endpoint].tolist()
    times[-1] = endpoint
    assert np.all(np.diff(times) > 0) and times[-1] == velocity[-1, 0]
    np.savez_compressed(OUTPUT/'plot_data.npz', times=times, positions=positions, densities=densities, velocity=velocity)
    manifest = dict(source_directory=str(SOURCE), snapshot_members=[f.name for _, f in snapshots],
                    velocity_members=[name for _, name in parts], zero_crossings=crossings,
                    endpoint_time=endpoint, endpoint_density_bracket=bracket,
                    endpoint_density_interpolation_weight=weight, saved_density_times=saved_times,
                    superseded_velocity_rows=sum(len(p) for p, _ in parts)-sum(map(len, stitched)),
                    grid_dt_dx_length=[DT, DX, LENGTH], spatial_stride=STRIDE, density_window=[-WINDOW, WINDOW],
                    density_definition='Re(psi)^2 + Im(psi)^2',
                    velocity_restart_rule='Each continuation supersedes earlier records from its restart time onward')
    (OUTPUT/'source_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Prepared {len(times)} density frames through third zero at {endpoint:.9f}', flush=True)


if __name__ == '__main__':
    main()
