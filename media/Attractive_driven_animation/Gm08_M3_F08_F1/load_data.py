"""Cache complex fields for F=0.8 and velocities with an authorized F=1 fallback run."""
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
from pathlib import Path
import re
import subprocess
import tarfile
import numpy as np

ROOT = Path('/run/media/sap/Seagate/Attractive_impurity_raw_data/Codes/Impurity_Thomas_Data/Delta_Impurity_optimum/Attractive_impurity/Attractive_driven/G-0.8/m0.333')
OUTPUT = Path(__file__).resolve().parent
SOURCE08 = ROOT/'F0.8/dt0.0025'
FINAL_TIME = 65.0
TIME_STEP = 0.0025
FALLBACK_TIME_STEP = 0.01
RECIPROCAL_SPACING = 6000
LENGTH = 3600.0
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



def snapshot_time(path):
    return float(re.search(r'time([0-9.]+)dt', path.name)[1])


def load08():
    directory = OUTPUT/'data_F0.8'
    directory.mkdir(exist_ok=True)
    records = []
    first = round((LENGTH/2-WINDOW)*RECIPROCAL_SPACING) + STRIDE
    stop = round((LENGTH/2+WINDOW)*RECIPROCAL_SPACING)
    positions = np.arange(first,stop,STRIDE)/RECIPROCAL_SPACING-LENGTH/2
    files = sorted(SOURCE08.glob('Phi_solution*'), key=snapshot_time)
    for path in files:
        time = snapshot_time(path)
        dt=float(re.search(r'dt([0-9.]+)dx',path.name)[1])
        dx=float(re.search(r'dx([0-9.e+-]+?)L',path.name)[1])
        assert dt==TIME_STEP and abs(dx*RECIPROCAL_SPACING-1)<GRID_TOLERANCE
        if time > FINAL_TIME:
            continue
        cache = directory/f'field_{time:g}.npz'
        if not cache.exists():
            with gzip.open(path,'rb') as stream:
                values = np.loadtxt(sampled_rows(stream,first,stop))
            assert values.shape == (len(positions),3) and np.isfinite(values).all()
            assert np.max(abs(values[:,0]-positions)) < POSITION_TOLERANCE
            np.savez_compressed(cache, positions=positions, field=values[:,1]+1j*values[:,2])
        records.append({'kind':'field','time':time,'source':str(path),'cache':cache.name})
        (directory/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
        print(f'F=0.8 field t={time:g}',flush=True)
    for index,path in enumerate(sorted(SOURCE08.glob('impurity_velocity*'))):
        with gzip.open(path,'rt') as stream:
            velocity = np.loadtxt(stream,ndmin=2)
        cache = f'velocity_{index}.npy'
        np.save(directory/cache,velocity)
        records.append({'kind':'velocity','source':str(path),'cache':cache,
                        'start':float(velocity[0,0]),'end':float(velocity[-1,0])})
    (directory/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    print('F=0.8 complete',flush=True)


def load1():
    directory = OUTPUT/'data_F1_fallback'
    directory.mkdir(exist_ok=True)
    records = []
    path = ROOT/'F1.tar.gz'
    with subprocess.Popen(['gzip','-dc',str(path)],stdout=subprocess.PIPE) as decoder:
        with tarfile.open(fileobj=decoder.stdout,mode='r|',bufsize=TAR_BUFFER_BYTES) as archive:
            for index,member in enumerate(archive):
                name = Path(member.name).name
                if not member.isfile() or not name.startswith('impurity_velocity'):
                    continue
                dt = float(re.search(r'dt([0-9.]+)L',name)[1])
                dx=float(re.search(r'dx([0-9.e+-]+?)dt',name)[1])
                if dt!=FALLBACK_TIME_STEP:
                    continue
                with archive.extractfile(member) as stream:
                    if name.endswith('.gz'):
                        with gzip.GzipFile(fileobj=stream) as uncompressed:
                            values=np.loadtxt(uncompressed,ndmin=2)
                    else:
                        values=np.loadtxt(stream,ndmin=2)
                assert np.isfinite(values).all()
                cache=f'velocity_{index}.npy'
                np.save(directory/cache,values)
                records.append({'kind':'velocity','source':str(path)+'::'+member.name,'cache':cache,
                                'dt':dt,'dx':1/round(1/dx),
                                'length':float(re.search(r'L([0-9]+)_',name)[1]),
                                'start':float(values[0,0]),'end':float(values[-1,0])})
                (directory/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
                print('F=1 velocity',records[-1],flush=True)
        while decoder.stdout.read(READ_CHUNK_BYTES):
            pass
        assert decoder.wait()==0
    assert records
    print('F=1 complete',flush=True)


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(load08),pool.submit(load1)]
        for job in jobs:
            job.result()
