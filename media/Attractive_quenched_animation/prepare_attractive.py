"""Cache spatially sampled fields without modifying the raw data."""
import gzip
import itertools
import json
from pathlib import Path
import re
import numpy as np

ROOT = Path('/run/media/sap/Seagate/Attractive_impurity_raw_data/Codes/Impurity_Thomas_Data/Delta_Impurity_optimum/Attractive_impurity/Attractive_quenched/Soliton/G-0.8/m0.125/V2/dx10000/dt0.00025')
OUTPUT = Path(__file__).resolve().parent
FINAL_TIME = 75.0
DX = 0.0001
LENGTH = 1200.0
WINDOW = 50.0
ZOOM_WINDOW = 15.0
STRIDE = 2500
WIDE_STRIDE = 5000
TOLERANCE = 0.000051
VELOCITY_STEP = 0.1

def main():
    sources = sorted((float(re.search(r'time(.*?)dt', p.name)[1]), p) for p in ROOT.glob('Phi*'))
    sources = [(t, p) for t, p in sources if t <= FINAL_TIME]
    start = round((LENGTH/2-WINDOW)/DX)
    stop = round((LENGTH/2+WINDOW)/DX)
    positions = np.arange(start, stop+1, STRIDE)*DX-LENGTH/2
    cache = OUTPUT/'density_cache'
    cache.mkdir(exist_ok=True)
    densities = []
    for index, (time, path) in enumerate(sources):
        target = cache/f't{time:g}.npy'
        if target.exists():
            density = np.load(target)
        else:
            with gzip.open(path, 'rt') as stream:
                values = np.loadtxt(list(itertools.islice(stream, start, stop+1, STRIDE)))
            assert values.shape == (len(positions), 3)
            assert np.allclose(values[:, 0], positions, atol=TOLERANCE, rtol=0)
            density = values[:, 1]**2 + values[:, 2]**2
            assert np.isfinite(density).all()
            np.save(target, density)
        densities.append(density)
        print(f'{index+1}/{len(sources)} t={time:g}', flush=True)
    parts = []
    velocity_sources = []
    for path in ROOT.glob('impurity_velocity*'):
        values = np.loadtxt(path, ndmin=2)[:, :2]
        if values[0, 0] <= FINAL_TIME:
            parts.append((values[0, 0], path, values[values[:, 0] <= FINAL_TIME]))
    velocity = np.empty((0, 2))
    for _, path, values in sorted(parts):
        velocity = np.concatenate((velocity[velocity[:, 0] < values[0, 0]], values))
        velocity_sources.append(str(path))
    assert velocity[0, 0] == 0 and velocity[-1, 0] == FINAL_TIME
    assert np.all(np.diff(velocity[:, 0]) > 0)
    gaps = np.flatnonzero(np.diff(velocity[:, 0]) > VELOCITY_STEP*1.5)
    np.savez_compressed(OUTPUT/'plot_data.npz', positions=positions, densities=densities,
                        times=[t for t, _ in sources], velocity=velocity)
    metadata = dict(density_sources=[dict(time=t, path=str(p)) for t,p in sources],
                    velocity_sources=velocity_sources, velocity_gaps=[[float(velocity[i,0]), float(velocity[i+1,0])] for i in gaps],
                    dx=DX, wide_stride=WIDE_STRIDE, zoom_stride=STRIDE,
                    density_definition='Re(psi)^2 + Im(psi)^2')
    (OUTPUT/'source_manifest.json').write_text(json.dumps(metadata, indent=2)+'\n')

if __name__ == '__main__':
    main()
