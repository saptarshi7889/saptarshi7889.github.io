"""Cache selected velocity runs and every 300th density point without extraction."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess
import tarfile
import numpy as np

ROOT = Path('/run/media/sap/RIdata/Data/Repulsive_impurity_simulation_data/Repulsive_Driven/Diff_G/G0.5')
OUTPUT = Path(__file__).resolve().parent
FORCES = {'3.5': 6000, '4': 6000, '4.1': 20000}
FINAL_TIME = 80.0
DENSITY_TIME_STEP = 0.0025
DENSITY_LENGTH = 4800.0
WINDOW = 200.0
STRIDE = 300
READ_CHUNK_BYTES = 4 * 1024 * 1024
TAR_BUFFER_BYTES = 1024 * 1024
POSITION_TOLERANCE = 0.000051
GRID_TOLERANCE = 1e-5

def sampled_rows(stream, first, stop):
    """Skip large row ranges by counting newlines in chunks, not Python loops."""
    row, pending, selected = 0, b'', []
    while row < stop:
        chunk = stream.read(READ_CHUNK_BYTES)
        if not chunk:
            raise ValueError('Configuration ends before the requested window')
        data = pending + chunk
        end = data.rfind(b'\n') + 1
        complete, pending = data[:end], data[end:]
        count = complete.count(b'\n')
        if row + count > first:
            lines = complete.splitlines()
            start = max(first, row)
            offset = (-(start-first)) % STRIDE
            selected.extend(lines[index-row] for index in range(start+offset, min(stop, row+count), STRIDE))
        row += count
    return selected



def load_force(force, reciprocal):
    destination = OUTPUT / ('data_F' + force)
    destination.mkdir(exist_ok=True)
    manifest_path = destination/'manifest.json'
    records = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    cached_members = {record['member'] for record in records}
    archive_path = ROOT / ('F' + force + '.tar.gz')
    with subprocess.Popen(['gzip', '-dc', str(archive_path)], stdout=subprocess.PIPE) as decoder:
        with tarfile.open(fileobj=decoder.stdout, mode='r|', bufsize=TAR_BUFFER_BYTES) as archive:
            for index, member in enumerate(archive):
                if not member.isfile():
                    continue
                if member.name in cached_members:
                    continue
                name = Path(member.name).name
                match = re.search(r'dx([0-9.e+-]+?)(?:dt|L)', name)
                if not match or abs(float(match[1])*reciprocal - 1) > GRID_TOLERANCE:
                    continue
                dt = float(re.search(r'dt([0-9.e+-]+?)(?:dx|L)', name)[1])
                length = float(re.search(r'L([0-9.]+?)(?:_|\.)', name)[1])
                record = {'member': member.name, 'dt': dt, 'dx': 1/reciprocal, 'length': length}
                if name.startswith('impurity_velocity') and name.endswith('.dat'):
                    with archive.extractfile(member) as stream:
                        values = np.loadtxt(stream, ndmin=2)
                    assert np.isfinite(values).all()
                    cache = 'velocity_' + str(index) + '.npy'
                    np.save(destination/cache, values)
                    record.update(kind='velocity', cache=cache, start=float(values[0,0]), end=float(values[-1,0]))
                elif force == '3.5' and name.startswith('Phi_solution'):
                    time = float(re.search(r'time([0-9.]+)dt', name)[1])
                    if time > FINAL_TIME or (dt, length) != (DENSITY_TIME_STEP, DENSITY_LENGTH):
                        continue
                    first = round((length/2-WINDOW)*reciprocal) + STRIDE
                    stop = round((length/2+WINDOW)*reciprocal)
                    positions = np.arange(first, stop, STRIDE)/reciprocal-length/2
                    with archive.extractfile(member) as stream:
                        field = np.loadtxt(sampled_rows(stream, first, stop))
                    assert field.shape == (len(positions), 3) and np.isfinite(field).all()
                    assert np.max(abs(field[:,0]-positions)) < POSITION_TOLERANCE
                    cache = 'density_' + str(index) + '.npz'
                    np.savez_compressed(destination/cache, positions=positions, density=field[:,1]**2+field[:,2]**2)
                    record.update(kind='density', cache=cache, time=time)
                else:
                    continue
                records.append(record)
                (destination/'manifest.json').write_text(json.dumps(records, indent=2)+'\n')
                print(force, record, flush=True)
        while decoder.stdout.read(READ_CHUNK_BYTES):
            pass
        assert decoder.wait() == 0
    (destination/'complete.json').write_text(json.dumps({'archive': str(archive_path), 'records':len(records)})+'\n')
    print('Finished F=' + force, flush=True)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=len(FORCES)) as pool:
        list(pool.map(lambda item: load_force(*item), FORCES.items()))
