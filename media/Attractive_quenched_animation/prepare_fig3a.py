"""Read coarsest available Fig. 3(a) data directly from source archives."""
import gzip
import itertools
import json
from pathlib import Path
import re
import tarfile
import numpy as np

ROOT = Path('/run/media/sap/Seagate/Attractive_impurity_raw_data/Codes/Impurity_Thomas_Data/Delta_Impurity_optimum/Attractive_impurity/Attractive_quenched/Velocity_initial_vel_final/m0.333')
OUTPUT = Path(__file__).resolve().parent / 'fig3a'
INITIAL_VELOCITIES = (0.5, 1.5, 2.5, 3.5, 4.5)
FINAL_TIME = 40.0
WINDOW = 40.0
DISPLAY_SPACING = 0.05
DENSITY_INITIAL_VELOCITY = 2.0
DENSITY_INVERSE_DX = 12500
COORDINATE_TOLERANCE = 0.000051
TIME_TOLERANCE = 1e-8


def main():
    OUTPUT.mkdir(exist_ok=True)
    arrays = {}
    manifest = {'paper': 'https://arxiv.org/pdf/2602.08443', 'velocity_sources': [],
                'density_sources': [], 'density_definition': 'Re(psi)^2 + Im(psi)^2',
                'window': [-WINDOW, WINDOW], 'final_time': FINAL_TIME,
                'density_initial_velocity': DENSITY_INITIAL_VELOCITY}
    for v in INITIAL_VELOCITIES:
        folder = ROOT / f'V{v:g}'
        choices = list(folder.glob('dx*.tar.gz')) + [p for p in folder.glob('dx*') if p.is_dir()]
        archive = min(choices, key=lambda p: int(p.name.split('.')[0][2:]))
        parts = []
        if archive.is_dir():
            for path in archive.glob('impurity_velocity*'):
                values = np.loadtxt(path, ndmin=2)[:, :2]
                if values[0, 0] <= FINAL_TIME:
                    parts.append((values[0, 0], str(path.relative_to(archive)), values[values[:, 0] <= FINAL_TIME]))
        else:
            with tarfile.open(archive, 'r|gz') as tar:
                for member in tar:
                    if 'impurity_velocity' not in member.name:
                        continue
                    values = np.loadtxt(tar.extractfile(member), ndmin=2)[:, :2]
                    if values[0, 0] <= FINAL_TIME:
                        parts.append((values[0, 0], member.name, values[values[:, 0] <= FINAL_TIME]))
        velocity = np.empty((0, 2))
        for _, name, values in sorted(parts):
            velocity = np.concatenate((velocity[velocity[:, 0] < values[0, 0]], values))
            manifest['velocity_sources'].append({'initial_velocity': v, 'archive': str(archive), 'member': name})
        assert velocity[0, 0] == 0 and abs(velocity[0, 1]-v) < TIME_TOLERANCE
        assert abs(velocity[-1, 0]-FINAL_TIME) < TIME_TOLERANCE
        assert np.isfinite(velocity).all() and np.all(np.diff(velocity[:, 0]) > 0)
        assert np.max(np.diff(velocity[:, 0])) < 0.11
        arrays[f'velocity_{v:g}'] = velocity
        print(f'Velocity V0={v:g}: {archive.name}, {len(velocity)} samples', flush=True)
    cache = OUTPUT/'plot_data.npz'
    archive = ROOT / f'V{DENSITY_INITIAL_VELOCITY:g}/dx{DENSITY_INVERSE_DX}.tar.gz'
    if (cache.exists() and np.load(cache)['times'][-1] == FINAL_TIME
            and all(record['archive'] == str(archive) for record in
                    json.loads((OUTPUT/'source_manifest.json').read_text())['density_sources'])):
        old = np.load(cache)
        old_manifest = json.loads((OUTPUT/'source_manifest.json').read_text())
        arrays.update({key: old[key] for key in ('positions', 'times', 'densities')})
        manifest['density_sources'] = old_manifest['density_sources']
        np.savez_compressed(cache, **arrays)
        (OUTPUT/'source_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        print('Reused cached density snapshots', flush=True)
        return
    snapshots = []
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if 'Phi_solution' not in member.name:
                continue
            time = float(re.search(r'time(.*?)dt', member.name)[1])
            if time > FINAL_TIME:
                continue
            dx = float(re.search(r'dx(.*?)L', Path(member.name).name)[1])
            length = float(re.search(r'L([\d.]+)_', member.name)[1])
            stride = round(DISPLAY_SPACING/dx)
            start, stop = round((length/2-WINDOW)/dx), round((length/2+WINDOW)/dx)
            stream = tar.extractfile(member)
            if member.name.endswith('.gz'):
                stream = gzip.GzipFile(fileobj=stream)
            values = np.loadtxt(list(itertools.islice(stream, start, stop+1, stride)))
            positions = np.arange(start, stop+1, stride)*dx-length/2
            assert np.allclose(values[:, 0], positions, atol=COORDINATE_TOLERANCE, rtol=0)
            density = values[:, 1]**2+values[:, 2]**2
            assert np.isfinite(density).all()
            snapshots.append((time, density))
            manifest['density_sources'].append({'time': time, 'archive': str(archive), 'member': member.name, 'dx': dx, 'stride': stride})
            print(f'Density t={time:g}: dx={dx:g}, stride={stride}', flush=True)
    snapshots.sort(key=lambda pair: pair[0])
    times = np.array([t for t, _ in snapshots])
    assert len(times) and times[-1] == FINAL_TIME and np.all(np.diff(times) > 0)
    arrays.update(positions=positions, times=times, densities=np.array([d for _, d in snapshots]))
    np.savez_compressed(OUTPUT/'plot_data.npz', **arrays)
    (OUTPUT/'source_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('Saved density times:', times, flush=True)


if __name__ == '__main__':
    main()
