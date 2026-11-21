"""Stream the F=0.03 archive once and cache sampled densities and logged velocities."""
import json
from pathlib import Path
import re
import subprocess
import tarfile
import numpy as np

SOURCE = Path('/run/media/sap/Seagate/Attractive_impurity_raw_data/Codes/Impurity_Thomas_Data/Delta_Impurity_optimum/Attractive_impurity/Attractive_driven/G-0.8/m0.125/F0.03.tar.gz')
OUTPUT = Path(__file__).resolve().parent
CACHE = OUTPUT/'density_cache'
VELOCITY_CACHE = OUTPUT/'velocity_cache'
LENGTH = 4200
DX = 0.00025
DT = 0.01
WINDOW = 500
STRIDE = 200
ZERO_COUNT = 3
READ_BYTES = 4 * 1024 * 1024
TAR_BUFFER_BYTES = 1024 * 1024
POSITION_TOLERANCE = 0.000051
GRID_TOLERANCE = 1e-12
SCAN_MANIFEST = OUTPUT/'archive_manifest.json'


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


def scan_archive(positions, first, stop):
    snapshots, velocity_members = [], []
    CACHE.mkdir(exist_ok=True)
    VELOCITY_CACHE.mkdir(exist_ok=True)
    with subprocess.Popen(['gzip', '-dc', str(SOURCE)], stdout=subprocess.PIPE) as decoder:
        with tarfile.open(fileobj=decoder.stdout, mode='r|', bufsize=TAR_BUFFER_BYTES) as archive:
            for member in archive:
                name = Path(member.name).name
                if not member.isfile() or name.startswith('._'):
                    continue
                if name.startswith('Phi_solution'):
                    match = re.search(r'time(.*?)dt(.*?)dx(.*?)L([0-9.]+)_', name)
                    time, dt, dx, length = map(float, match.groups())
                    assert abs(dx-DX) < GRID_TOLERANCE and dt == DT and length == LENGTH, name
                    cache = CACHE/f't{time:g}.npy'
                    if not cache.exists():
                        with archive.extractfile(member) as stream:
                            field = np.loadtxt(sampled_rows(stream, first, stop))
                        assert field.shape == (len(positions), 3) and np.isfinite(field).all(), name
                        assert np.allclose(field[:, 0], positions, atol=POSITION_TOLERANCE, rtol=0), name
                        density = field[:, 1]**2 + field[:, 2]**2
                        temporary = cache.with_suffix('.tmp.npy')
                        np.save(temporary, density)
                        temporary.replace(cache)
                    snapshots.append((time, member.name))
                    print(f'Density {len(snapshots)}: t={time:g}', flush=True)
                elif name.startswith('impurity_velocity'):
                    with archive.extractfile(member) as stream:
                        values = np.loadtxt(stream, ndmin=2)[:, :2]
                    assert np.isfinite(values).all() and np.all(np.diff(values[:, 0]) > 0), name
                    np.save(VELOCITY_CACHE/f'{len(velocity_members)}.npy', values)
                    velocity_members.append(member.name)
                    print(f'Velocity {len(velocity_members)}: t={values[0,0]:g}..{values[-1,0]:g}', flush=True)
        while decoder.stdout.read(READ_BYTES):
            pass
        assert decoder.wait() == 0, 'Archive decompression failed'
    snapshots.sort()
    assert snapshots and velocity_members
    assert np.all(np.diff([t for t, _ in snapshots]) > 0), 'Duplicate snapshot times'
    metadata = dict(source_archive=str(SOURCE), archive_bytes=SOURCE.stat().st_size,
                    snapshots=snapshots, velocity_members=velocity_members)
    SCAN_MANIFEST.write_text(json.dumps(metadata, indent=2)+'\n')
    return metadata


def main():
    first, stop = round((LENGTH/2-WINDOW)/DX), round((LENGTH/2+WINDOW)/DX)
    positions = np.arange(first, stop, STRIDE)*DX-LENGTH/2
    metadata = json.loads(SCAN_MANIFEST.read_text()) if SCAN_MANIFEST.exists() else scan_archive(positions, first, stop)
    assert metadata['source_archive'] == str(SOURCE)
    parts = sorted([(np.load(VELOCITY_CACHE/f'{i}.npy'), name)
                    for i, name in enumerate(metadata['velocity_members'])], key=lambda item: item[0][0, 0])
    stitched = []
    for i, (part, _) in enumerate(parts):
        stitched.append(part[part[:, 0] < parts[i+1][0][0, 0]] if i+1 < len(parts) else part)
    velocity = np.concatenate(stitched)
    assert np.all(np.diff(velocity[:, 0]) > 0) and np.isfinite(velocity).all()
    nonzero = np.flatnonzero(velocity[:, 1])
    crossings = []
    for left, right in zip(nonzero[:-1], nonzero[1:]):
        t0, v0 = velocity[left]
        t1, v1 = velocity[right]
        if v0*v1 < 0:
            crossings.append(float(t0-v0*(t1-t0)/(v1-v0)))
    assert len(crossings) >= ZERO_COUNT, crossings
    endpoint = crossings[ZERO_COUNT-1]
    velocity = np.vstack((velocity[velocity[:, 0] < endpoint], [endpoint, 0]))
    upper = next(t for t, _ in metadata['snapshots'] if t >= endpoint)
    snapshots = [(t, name) for t, name in metadata['snapshots'] if t <= upper]
    times = np.array([t for t, _ in snapshots])
    densities = np.array([np.load(CACHE/f't{t:g}.npy') for t in times])
    assert densities.shape == (len(times), len(positions)) and np.isfinite(densities).all()
    bracket = times[-2:].tolist()
    weight = (endpoint-times[-2])/(times[-1]-times[-2])
    densities[-1] = (1-weight)*densities[-2] + weight*densities[-1]
    saved_times = times[times <= endpoint].tolist()
    times[-1] = endpoint
    assert np.all(np.diff(times) > 0) and times[-1] == velocity[-1, 0]
    np.savez_compressed(OUTPUT/'plot_data.npz', times=times, positions=positions, densities=densities, velocity=velocity)
    manifest = dict(source_archive=str(SOURCE), snapshot_members=[name for _, name in snapshots],
                    velocity_members=[name for _, name in parts], zero_crossings=crossings,
                    endpoint_time=endpoint, endpoint_density_bracket=bracket,
                    endpoint_density_interpolation_weight=weight, saved_density_times=saved_times,
                    superseded_velocity_rows=sum(len(p) for p, _ in parts)-sum(map(len, stitched)),
                    grid_dt_dx_length=[DT, DX, LENGTH], spatial_stride=STRIDE, density_window=[-WINDOW, WINDOW],
                    mass_ratio=8, coupling=-0.8, force=0.03,
                    density_definition='Re(psi)^2 + Im(psi)^2',
                    velocity_restart_rule='Each continuation supersedes earlier records from its restart time onward')
    (OUTPUT/'source_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Prepared {len(times)} density frames through third zero at {endpoint:.9f}', flush=True)


if __name__ == '__main__':
    main()
