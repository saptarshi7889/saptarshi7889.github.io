"""Extract the brown vector curve from Fig. 2.1; fill only the raw-data gap."""
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUTPUT = Path(__file__).resolve().parent
PDF = Path('/home/sap/Downloads/Impurity_corrected-1.pdf')
PDF_PAGE = 136
TRANSFORM = 'matrix(0.262425, 0, 0, 0.272985, 250.480068, 456.810445)'
BROWN = 'rgb(50.196838%, 7.843018%, 7.843018%)'
X_ZERO = 65.496429
X_50 = 118.830117
Y_MINUS_ONE = 243.209744
Y_TWO = 22.644967
GAP = (65.7, 73.5)
SAMPLE_STEP = 0.1
OVERLAP_WINDOW = (55, 80)
FIGSIZE = (9, 5)
DPI = 160

def main():
    svg = OUTPUT/'figure_2_1_page135.svg'
    subprocess.run(['pdftocairo', '-f', str(PDF_PAGE), '-l', str(PDF_PAGE), '-svg', str(PDF), str(svg)], check=True)
    chunks = []
    for element in ET.parse(svg).iter():
        if element.get('transform') != TRANSFORM or element.get('stroke') != BROWN:
            continue
        path = element.get('d', '')
        if len(path) < 100:
            continue  # Legend swatch.
        assert set(re.findall('[A-Za-z]', path)) <= {'M', 'L'}
        xy = np.array(re.findall(r'[-+]?\d*\.?\d+', path), dtype=float).reshape(-1, 2)
        chunks.append(xy)
    xy = np.concatenate(chunks)
    xy = xy[np.argsort(xy[:, 0])]
    _, unique = np.unique(xy[:, 0], return_index=True)
    xy = xy[unique]
    curve = np.column_stack(((xy[:, 0]-X_ZERO)*50/(X_50-X_ZERO),
                             -1+(Y_MINUS_ONE-xy[:, 1])*3/(Y_MINUS_ONE-Y_TWO)))
    np.savetxt(OUTPUT/'brown_curve_extracted.csv', curve, delimiter=',', header='time,velocity', comments='')
    data = dict(np.load(OUTPUT/'plot_data.npz'))
    raw = data['velocity']
    raw = raw[(raw[:, 0] <= GAP[0]) | (raw[:, 0] >= GAP[1])]
    overlap = (raw[:, 0]>=OVERLAP_WINDOW[0]) & (raw[:, 0]<=OVERLAP_WINDOW[1])
    errors = np.interp(raw[overlap, 0], curve[:, 0], curve[:, 1])-raw[overlap, 1]
    print('Overlap RMS error:',np.sqrt(np.mean(errors**2)), 'max:',abs(errors).max())
    print('Endpoints [raw, PDF]:',[(t, float(np.interp(t,raw[:,0],raw[:,1])),float(np.interp(t,curve[:,0],curve[:,1]))) for t in GAP])
    assert abs(errors).max() < 0.003, 'Extracted curve does not match raw data'
    times = np.arange(round(GAP[0]/SAMPLE_STEP)+1, round(GAP[1]/SAMPLE_STEP))*SAMPLE_STEP
    bridge = np.column_stack((times, np.interp(times,curve[:,0],curve[:,1])))
    np.savetxt(OUTPUT/'velocity_bridge.csv',bridge,delimiter=',',header='time,velocity',comments='')
    # Keep the measured endpoints and every other original sample unchanged.
    merged = np.concatenate((raw, bridge))
    merged = merged[np.argsort(merged[:,0])]
    assert np.allclose(np.diff(merged[:,0]), SAMPLE_STEP)
    data['velocity'] = merged
    np.savez_compressed(OUTPUT/'plot_data.npz', **data)
    metadata_path = OUTPUT/'source_manifest.json'
    metadata = json.loads(metadata_path.read_text())
    metadata['velocity_gaps'] = []
    metadata['velocity_bridge'] = dict(pdf=str(PDF), pdf_page=PDF_PAGE, printed_page=135,
        figure='2.1, velocity top row third panel, brown curve', interval=list(GAP),
        method='Extract vector M/L vertices; linear interpolation to 0.1 time grid; preserve raw endpoints',
        sample_count=len(bridge), overlap_rms_error=float(np.sqrt(np.mean(errors**2))),
        overlap_max_error=float(abs(errors).max()), status='Recovered plotted coordinates, not original simulation precision')
    metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(curve[:,0],curve[:,1],color='brown',label='PDF vector curve',linewidth=1)
    ax.plot(raw[:,0],raw[:,1],'.',label='Original velocity files',markersize=3)
    ax.plot(bridge[:,0],bridge[:,1],color='orange',label='Recovered bridge',linewidth=2)
    ax.set(xlim=OVERLAP_WINDOW,xlabel='Time',ylabel='Impurity velocity V/v',title='Fig. 2.1 brown curve: bridge validation')
    ax.legend(); ax.grid(alpha=0.2); fig.tight_layout()
    fig.savefig(OUTPUT/'velocity_bridge_validation.png',dpi=DPI)

if __name__ == '__main__':
    main()
