"""Render synchronized force comparison and sampled F=3.5 density."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

OUTPUT = Path(__file__).resolve().parent
FORCES = ('3.5', '4', '4.1')
SELECTED_RUNS = {'3.5': (0.0025, 4800.0), '4': (0.01, 1600.0), '4.1': (0.01, 1600.0)}
# Stroke colors extracted from the vector PDF, Fig. 3(b).
COLORS = {'3.5': (0.24220276, 0.15039062, 0.66029358),
          '4': (0.14079285, 0.62258911, 0.89978027),
          '4.1': (0.58859253, 0.79129028, 0.28329468)}
FINAL_TIME = 80.0
WINDOW = 200.0
STRIDE = 300
# 8 fps multiplied by the requested playback factor of 1.9.
FPS_NUMERATOR = 76
FPS_DENOMINATOR = 5
FPS = FPS_NUMERATOR / FPS_DENOMINATOR
FIGURE_SIZE = (12, 8)
DPI = 120
LINE_WIDTH = 2.0
DENSITY_LINE_WIDTH = 1.3
MARKER_SIZE = 5
BOSON_STRIDE = 40
BOSON_SIZE = 2.5
IMPURITY_SIZE = 10
BACKGROUND = '#fafbfe'
DENSITY_COLOR = '#279aab'
IMPURITY_COLOR = '#e15b64'
VELOCITY_PADDING = 0.10
DENSITY_PADDING = 0.08
GRID_ALPHA = 0.18
ENCODING_QUANTIZER = 18
TIME_TOLERANCE = 1e-8
VELOCITY_BOUNDS = (0.10, 0.53, 0.86, 0.34)
DENSITY_BOUNDS = (0.10, 0.12, 0.86, 0.28)
TITLE_POSITION = (0.10, 0.96)
SUBTITLE_POSITION = (0.10, 0.915)
CLOCK_POSITION = (0.96, 0.915)
TITLE_SIZE = 19
LABEL_SIZE = 10
CLOCK_SIZE = 14
GIF_QUANTUM_MS = 10


def stitch(records, directory):
    parts = sorted([(record, np.load(directory/record['cache'])) for record in records],
                   key=lambda item: item[1][0, 0])
    kept = []
    for index, (_, values) in enumerate(parts):
        assert np.all(np.diff(values[:, 0]) > 0)
        if index + 1 < len(parts):
            values = values[values[:, 0] < parts[index+1][1][0, 0]]
        kept.append(values)
    velocity = np.concatenate(kept)
    velocity = velocity[(velocity[:,0] >= 0) & (velocity[:,0] <= FINAL_TIME+TIME_TOLERANCE)]
    assert np.all(np.diff(velocity[:,0]) > 0) and np.isfinite(velocity).all()
    assert np.isclose(velocity[0,0], 0) and np.isclose(velocity[-1,0], FINAL_TIME)
    cadence = np.median(np.diff(velocity[:,0]))
    assert np.max(np.diff(velocity[:,0])) <= cadence * 1.5 + TIME_TOLERANCE, 'Gap in velocity records'
    return velocity


def main():
    velocities, sources, grids = {}, {}, {}
    for force in FORCES:
        directory = OUTPUT / ('data_F'+force)
        records = json.loads((directory/'manifest.json').read_text())
        candidates = [r for r in records if r['kind'] == 'velocity']
        dt, length = SELECTED_RUNS[force]
        selected = [r for r in candidates if (r['dt'], r['length']) == (dt, length)]
        assert selected, f'Load the selected velocity run for F={force}'
        velocities[force] = stitch(selected, directory)
        sources[force] = selected
        grids[force] = {'dt': dt, 'length': length, 'dx': selected[0]['dx']}
    directory = OUTPUT/'data_F3.5'
    records = json.loads((directory/'manifest.json').read_text())
    grid = grids['3.5']
    snapshots = sorted([r for r in records if r['kind']=='density' and
                        r['dt']==grid['dt'] and r['length']==grid['length'] and r['time'] <= FINAL_TIME], key=lambda r:r['time'])
    times = np.array([r['time'] for r in snapshots])
    assert len(times) and np.all(np.diff(times)>0) and np.isclose(times[-1], FINAL_TIME)
    arrays = [np.load(directory/r['cache']) for r in snapshots]
    positions = arrays[0]['positions']
    assert all(np.array_equal(a['positions'], positions) for a in arrays)
    densities = np.array([a['density'] for a in arrays])
    assert np.isfinite(densities).all() and (densities >= 0).all()
    assert (abs(positions) < WINDOW).all()
    assert np.allclose(np.diff(positions), STRIDE*grid['dx'])
    fig = plt.figure(figsize=FIGURE_SIZE, dpi=DPI, facecolor=BACKGROUND)
    ax = fig.add_axes(VELOCITY_BOUNDS, facecolor=BACKGROUND)
    low = min(v[:,1].min() for v in velocities.values())-VELOCITY_PADDING
    high = max(v[:,1].max() for v in velocities.values())+VELOCITY_PADDING
    ax.set(xlim=(0,FINAL_TIME), ylim=(low,high), xlabel=r'$tgn_0/\hbar$', ylabel=r'$V/v$')
    ax.spines[['top','right']].set_visible(False)
    ax.grid(alpha=GRID_ALPHA)
    lines, markers = {}, {}
    for force in FORCES:
        lines[force], = ax.plot([], [], color=COLORS[force], lw=LINE_WIDTH, label=rf'$\widetilde F={force}$')
        markers[force], = ax.plot([], [], 'o', color=COLORS[force], ms=MARKER_SIZE)
    ax.legend(loc='lower left', ncol=len(FORCES), frameon=False)
    cursor = ax.axvline(times[0], color='0.5', alpha=GRID_ALPHA)
    density_ax = fig.add_axes(DENSITY_BOUNDS, facecolor='white')
    density_ax.set(xlim=(-WINDOW,WINDOW), ylim=(0,densities.max()+DENSITY_PADDING),
                   xlabel=r'Position relative to impurity, $x/\xi$', ylabel=r'$n(x)/n_0$')
    density_ax.axhline(1, color='0.7', ls=':', lw=1)
    density_ax.axvline(0, color='0.7', ls=':', lw=1)
    density_line, = density_ax.plot(positions, densities[0], color=DENSITY_COLOR, lw=DENSITY_LINE_WIDTH)
    beads, = density_ax.plot(positions[::BOSON_STRIDE], densities[0,::BOSON_STRIDE], 'o',
                             color=DENSITY_COLOR, ms=BOSON_SIZE, markeredgewidth=0)
    impurity, = density_ax.plot([0], [np.interp(0,positions,densities[0])], 'o',
                                color=IMPURITY_COLOR, ms=IMPURITY_SIZE, markeredgecolor='#873044')
    density_ax.text(0.02,0.91,r'BOSON DENSITY  |  $\widetilde F=3.5$', transform=density_ax.transAxes,
                    color=DENSITY_COLOR, fontsize=LABEL_SIZE)
    fig.text(*TITLE_POSITION, 'Driven impurity: velocity and boson density', fontsize=TITLE_SIZE)
    fig.text(*SUBTITLE_POSITION, r'$\widetilde G=0.5$    |    $M=3m$    |    $\gamma=1/400$    |    Impurity frame',
             fontsize=LABEL_SIZE, color='0.4')
    clock = fig.text(*CLOCK_POSITION, '', ha='right', fontsize=CLOCK_SIZE)
    gif_frames = []
    with tempfile.TemporaryDirectory(prefix='driven-animation-') as temp:
        frames = Path(temp)
        for index, (time,density) in enumerate(zip(times,densities)):
            for force, velocity in velocities.items():
                mask = velocity[:,0] <= time+TIME_TOLERANCE
                lines[force].set_data(velocity[mask,0], velocity[mask,1])
                markers[force].set_data([time],[np.interp(time,velocity[:,0],velocity[:,1])])
            cursor.set_xdata([time,time])
            density_line.set_ydata(density)
            beads.set_ydata(density[::BOSON_STRIDE])
            impurity.set_ydata([np.interp(0,positions,density)])
            clock.set_text(rf'$tgn_0/\hbar={time:g}$')
            path = frames/f'frame_{index:03d}.png'
            fig.savefig(path,dpi=DPI)
            with Image.open(path) as frame:
                gif_frames.append(frame.convert('P',palette=Image.Palette.ADAPTIVE))
            if index == 0:
                fig.savefig(OUTPUT/'velocity_density_animation_intro.png',dpi=DPI)
            if index == len(times)-1:
                fig.savefig(OUTPUT/'velocity_density_animation_preview.png',dpi=DPI)
        plt.close(fig)
        pipeline = ['gst-launch-1.0','-e','multifilesrc',f'location={frames}/frame_%03d.png',
                    'index=0',f'stop-index={len(times)-1}',f'caps=image/png,framerate=(fraction){FPS_NUMERATOR}/{FPS_DENOMINATOR}',
                    '!','pngdec','!','videoconvert','!','video/x-raw,format=I420','!','x264enc',
                    'pass=qual',f'quantizer={ENCODING_QUANTIZER}','speed-preset=medium',
                    '!','video/x-h264,profile=high','!','mp4mux','faststart=true',
                    '!','filesink',f'location={OUTPUT}/velocity_density_animation.mp4']
        result = subprocess.run(pipeline,capture_output=True,text=True,env=dict(os.environ,GST_DEBUG='1'))
        (OUTPUT/'animation_encoding.log').write_text(result.stdout+result.stderr)
        assert result.returncode == 0, 'See animation_encoding.log'
        boundaries = np.rint(np.arange(len(times)+1)*1000/FPS/GIF_QUANTUM_MS)*GIF_QUANTUM_MS
        gif_frames[0].save(OUTPUT/'velocity_density_animation.gif',save_all=True,
                           append_images=gif_frames[1:],duration=np.diff(boundaries).astype(int).tolist(),loop=0)
    manifest = {'forces':FORCES,'grids':grids,'velocity_sources':sources,'density_sources':snapshots,
                'density_times':times.tolist(),'density_window':[-WINDOW,WINDOW], 'stride':STRIDE,
                'density_points':len(positions),'density_spacing':STRIDE*grid['dx'],
                'density_definition':'Re(phi)^2 + Im(phi)^2', 'colors':COLORS,
                'color_reference':'https://arxiv.org/pdf/2511.20326, Fig. 3(b)',
                'fps':FPS,'duration_seconds':len(times)/FPS,
                'velocity_rows':{f:len(v) for f,v in velocities.items()},
                'velocity_restart_rule':'Continuation supersedes earlier records from its restart time',
                'interpolation':'No density interpolation; each frame is a saved configuration',
                'endpoint_time':FINAL_TIME}
    (OUTPUT/'animation_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Rendered {len(times)} saved configurations through t={times[-1]:g}',flush=True)


if __name__ == '__main__':
    main()
