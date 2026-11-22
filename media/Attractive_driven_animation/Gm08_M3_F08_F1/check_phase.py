"""Check the three wrapped phase plots against tenfold denser spatial samples."""
import gzip
import json
from pathlib import Path
import numpy as np
import load_data as loader

OUTPUT = Path(__file__).resolve().parent
PHASE_TIMES = (15.0, 39.0, 63.0)
AUDIT_STRIDE = 30
PLOT_STRIDE = 300
PHASE_OFFSET = -np.pi/2
TURN_TOLERANCE = 0.01
MAX_PHASE_INCREMENT = np.pi/2


def main():
    records = json.loads((OUTPUT/'data_F0.8/manifest.json').read_text())
    loader.STRIDE = AUDIT_STRIDE
    first = round((loader.LENGTH/2-loader.WINDOW)*loader.RECIPROCAL_SPACING)+PLOT_STRIDE
    stop = round((loader.LENGTH/2+loader.WINDOW)*loader.RECIPROCAL_SPACING)
    results = []
    for expected,time in enumerate(PHASE_TIMES,start=1):
        record, = [r for r in records if r['kind']=='field' and r['time']==time]
        with gzip.open(record['source'],'rb') as stream:
            values = np.loadtxt(loader.sampled_rows(stream,first,stop))
        field = values[:,1]+1j*values[:,2]
        with np.load(OUTPUT/'data_F0.8'/record['cache']) as cache:
            assert np.array_equal(field[::PLOT_STRIDE//AUDIT_STRIDE],cache['field'])
        phase=np.angle(field*np.exp(1j*(time+PHASE_OFFSET)))
        drops=int(np.sum(np.diff(phase)<-np.pi))
        rises=int(np.sum(np.diff(phase)>np.pi))
        turns=float((np.unwrap(phase)[-1]-np.unwrap(phase)[0])/(2*np.pi))
        increment=float(np.max(abs(np.angle(field[1:]*field[:-1].conj()))))
        assert drops==expected and rises==0
        assert abs(turns-expected)<TURN_TOLERANCE
        assert increment<MAX_PHASE_INCREMENT
        results.append({'time':time,'audit_stride':AUDIT_STRIDE,'spacing':AUDIT_STRIDE/loader.RECIPROCAL_SPACING,
                        'drops':drops,'rises':rises,'unwrapped_turns':turns,
                        'maximum_adjacent_phase_increment':increment,
                        'minimum_sampled_density':float(np.min(abs(field)**2))})
        print(results[-1],flush=True)
    (OUTPUT/'phase_checks.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':
    main()
