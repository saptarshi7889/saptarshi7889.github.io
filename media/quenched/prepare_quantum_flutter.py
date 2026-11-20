"""Select complete, finest-grid Fig. 13/14 series from the archive caches."""
import json
from collections import defaultdict

import numpy as np

from load_quantum_flutter import (ARCHIVES, COUPLINGS, DENSITY_COUPLING, FINAL_TIME,
                                 INITIAL_VELOCITY, MASS_PARAMETER, OUTPUT, PARAMETER_TOLERANCE, ROOT)

SNAPSHOT_INTERVAL = 2.5
INITIAL_TOLERANCE = 1e-5
VELOCITY_SAMPLE_INTERVAL = 0.1
GAMMA = 0.1
ALLOWED_RESOLUTION_RANKS = 2


def merge(records):
    parts = [(record, np.load(OUTPUT / record['cache'])['values']) for record in records]
    parts = [(record, values) for record, values in parts if len(values)]
    # A restart supersedes the preceding file from its starting time onward.
    parts.sort(key=lambda item: (item[1][0, 0], item[1][-1, 0], item[0]['member']))
    if not parts:
        return np.empty((0, 2))
    values = parts[0][1]
    for _, continuation in parts[1:]:
        values = np.concatenate((values[values[:, 0] < continuation[0, 0] - PARAMETER_TOLERANCE], continuation))
    return values


def main():
    records = []
    completed_scopes = {}
    for archive in ARCHIVES:
        cached = json.loads((OUTPUT / (archive + '.json')).read_text())
        if (OUTPUT / (archive + '.complete')).exists():
            completed_scopes[archive] = ['Entire archive']
        else:
            # A finished nested archive is sufficient; unrelated masses may still be read.
            catalog = OUTPUT / (archive.removesuffix('.gz') + '_catalog.jsonl')
            last_member = json.loads(catalog.read_text().splitlines()[-1])['name']
            nested = {r['member'].split('::')[0] for r in cached if '::' in r['member']}
            finished = {name for name in nested if not last_member.startswith(name + '::')}
            cached = [r for r in cached if r['member'].split('::')[0] in finished]
            assert cached, f'Required archive scope is still being read: {archive}'
            completed_scopes[archive] = sorted(finished)
        records.extend(cached)
    arrays, sources = {}, {}
    for coupling in COUPLINGS:
        groups = defaultdict(list)
        for record in records:
            if record['kind'] == 'velocity' and record['coupling'] == coupling:
                folder = record['member'].rsplit('/', 1)[0]
                groups[(record['archive'], folder, record['dx'], record['dt'], record['length'])].append(record)
        complete = []
        for key, group in groups.items():
            values = merge(group)
            if (len(values) and abs(values[0, 0]) < PARAMETER_TOLERANCE
                    and abs(values[-1, 0] - FINAL_TIME) < PARAMETER_TOLERANCE
                    and np.all(np.diff(values[:, 0]) <= VELOCITY_SAMPLE_INTERVAL + PARAMETER_TOLERANCE)):
                assert abs(values[0, 1] - INITIAL_VELOCITY) < INITIAL_TOLERANCE
                assert np.all(np.diff(values[:, 0]) > 0) and np.isfinite(values).all()
                complete.append((key, group, values))
        assert complete, f'No complete velocity series for G={coupling}'
        # Highest dx-folder number means smallest spacing. Prefer smaller dt on ties.
        complete.sort(key=lambda item: (item[0][2], item[0][3], -item[0][4]))
        key, group, values = complete[0]
        finest_spacings = sorted({candidate[2] for candidate in groups})[:ALLOWED_RESOLUTION_RANKS]
        assert key[2] in finest_spacings, f'Neither of the two finest grids reaches t=50 for G={coupling}'
        arrays[f'g{coupling:g}'] = values
        sources[str(coupling)] = group
        print(f'G={coupling:g}: dx={key[2]:g}, dt={key[3]:g}, t={values[0,0]:g}..{values[-1,0]:g}; {key[1]}', flush=True)
    snapshots = [r for r in records if r['kind'] == 'density' and r['coupling'] == DENSITY_COUPLING]
    groups = defaultdict(list)
    for record in snapshots:
        groups[(record['archive'], record['member'].rsplit('/', 1)[0], record['dx'], record['dt'], record['length'])].append(record)
    expected_times = np.arange(SNAPSHOT_INTERVAL, FINAL_TIME + SNAPSHOT_INTERVAL, SNAPSHOT_INTERVAL)
    complete = []
    for key, group in groups.items():
        by_time = {record['time']: record for record in group}
        if all(time in by_time for time in expected_times):
            complete.append((key, [by_time[time] for time in expected_times]))
    assert complete, 'No single G=0.65 density folder contains every snapshot through t=50'
    complete.sort(key=lambda item: (item[0][2], item[0][3], -item[0][4]))
    key, snapshots = complete[0]
    fields = [np.load(OUTPUT / record['cache']) for record in snapshots]
    positions = fields[0]['positions']
    assert all(np.array_equal(positions, field['positions']) for field in fields)
    arrays.update(positions=positions, times=expected_times, densities=np.array([field['density'] for field in fields]))
    assert np.isfinite(arrays['densities']).all()
    np.savez_compressed(OUTPUT / 'plot_data.npz', **arrays)
    metadata = dict(archive_root=str(ROOT), paper='https://arxiv.org/pdf/2507.10402',
                    completed_archive_scopes=completed_scopes,
                    mass_ratio=1 / MASS_PARAMETER, initial_velocity=INITIAL_VELOCITY,
                    gamma=GAMMA, final_time=FINAL_TIME,
                    velocity_sources=sources, density_coupling=DENSITY_COUPLING,
                    density_sources=snapshots, density_definition='Re(psi)^2 + Im(psi)^2',
                    selection='Smallest spacing among folders with complete data through t=50; smallest dt on ties')
    (OUTPUT / 'source_manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'Density: {len(snapshots)} snapshots, dx={key[2]:g}, t={expected_times[0]:g}..{expected_times[-1]:g}', flush=True)


if __name__ == '__main__':
    main()
