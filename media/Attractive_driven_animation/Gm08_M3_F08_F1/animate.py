"""Render attractive driven velocities, density and three fixed phase snapshots."""
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
FORCES = ('0.8', '1')
# Stroke colors from Fig. 2(a) of arXiv:2606.13645.
COLORS = {'0.8': (0.2421875, 0.15039062, 0.66029358),
          '1': (0.92718506, 0.72979736, 0.19729614)}
DATA_DIRECTORIES = {'0.8':'data_F0.8', '1':'data_F1_fallback'}
GRIDS = {'0.8': {'dt': 0.0025, 'length': 3600.0, 'dx': 1/6000},
         '1': {'dt': 0.01, 'length': 2400.0, 'dx': 1/8000}}
PHASE_TIMES = (15.0, 39.0, 63.0)
CYLINDER_WINDOWS = {15.0: 50.0, 39.0: 100.0, 63.0: 150.0}
CYLINDER_VIEW_ROTATION = np.pi/2
PHASE_OFFSET = -np.pi/2
PHASE_TURN_TOLERANCE = 0.01
PHASE_BOUNDS = ((0.71, 0.66, 0.27, 0.20), (0.71, 0.40, 0.27, 0.20), (0.71, 0.14, 0.27, 0.20))
PHASE_COLOR = '#3e26a8'
PHASE_TITLE_SIZE = 10
PHASE_HEADING_POSITION = (0.71, 0.91)
PHASE_FIGURE_SIZE = (14, 9)
PHASE_HEIGHT_RATIOS = (3, 1)
CYLINDER_RADIUS = 0.75
CYLINDER_HEIGHT = 2.0
CYLINDER_ELLIPSE_DEPTH = 0.14
CYLINDER_ANGLE_STEP = np.pi/32
CYLINDER_RING_COUNT = 13
CYLINDER_MERIDIAN_COUNT = 12
CYLINDER_RING_SAMPLES = 129
CYLINDER_GRID_COLOR = '#a5a9b2'
CYLINDER_GRID_ALPHA = 0.18
CYLINDER_GRID_WIDTH = 0.45
CYLINDER_CAP_WIDTH = 0.7
CYLINDER_AXIS_MARGIN = 0.30
CYLINDER_TOP_MARGIN = 0.55
CYLINDER_BOTTOM_MARGIN = 0.25
CYLINDER_LABEL_SIZE = 8
CYLINDER_LABEL_OFFSET = 0.09
CYLINDER_FRONT_LABEL_LIFT = 0.18
CYLINDER_LEFT_LABEL_LIFT = 0.18
CYLINDER_POSITION_LABEL_OFFSET = 3 * CYLINDER_LABEL_OFFSET
CYLINDER_AXIS_OFFSET = 0.40
CYLINDER_REAR_DASH = (0, (2, 2))
CYLINDER_FRONT_WIDTH = 1.0
CYLINDER_REFERENCE = 'https://arxiv.org/pdf/2412.04355v1, Fig. 2(a)'
PHASE_FIGURE_MARGINS = {'left': 0.06, 'right': 0.98, 'bottom': 0.11, 'top': 0.89, 'hspace': 0.16, 'wspace': 0.22}
FINAL_TIME = 65.0
WINDOW = 200.0
STRIDE = 300
# 8 fps multiplied by the requested playback factor of 1.9.
FPS_NUMERATOR = 76
FPS_DENOMINATOR = 5
FPS = FPS_NUMERATOR / FPS_DENOMINATOR
FIGURE_SIZE = (14, 9)
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
VELOCITY_BOUNDS = (0.08, 0.58, 0.55, 0.27)
DENSITY_BOUNDS = (0.08, 0.15, 0.55, 0.28)
TITLE_POSITION = (0.08, 0.97)
SUBTITLE_POSITION = (0.08, 0.92)
CLOCK_POSITION = (0.63, 0.88)
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


def phase_snapshots(times, positions, fields):
    phases, records = [], []
    for count, time in enumerate(PHASE_TIMES, start=1):
        index, = np.flatnonzero(np.isclose(times,time))
        field = fields[index]
        phase = np.angle(field*np.exp(1j*(time+PHASE_OFFSET)))
        drops = np.flatnonzero(np.diff(phase) < -np.pi)
        rises = np.flatnonzero(np.diff(phase) > np.pi)
        unwrapped = np.unwrap(phase)
        turns = float((unwrapped[-1]-unwrapped[0])/(2*np.pi))
        assert len(drops)==count and len(rises)==0
        assert abs(turns-count) < PHASE_TURN_TOLERANCE
        phases.append(phase)
        records.append({'time':time,'wrapped_drops':len(drops),'wrapped_rises':len(rises),
                        'unwrapped_turns':turns,
                        'drop_positions':((positions[drops]+positions[drops+1])/2).tolist()})
    return phases, records


def cylinder_curve(positions, phase, window=WINDOW):
    """Interpolate the display angle so short segments follow the cylinder surface."""
    unwrapped = np.unwrap(phase)
    counts = np.maximum(1, np.ceil(abs(np.diff(unwrapped))/CYLINDER_ANGLE_STEP).astype(int))
    segments = np.repeat(np.arange(len(counts)), counts)
    fractions = np.concatenate([np.arange(count)/count for count in counts])
    x = positions[segments] + fractions*np.diff(positions)[segments]
    theta = unwrapped[segments] + fractions*np.diff(unwrapped)[segments]
    x = np.append(x, positions[-1])
    theta = np.append(theta, unwrapped[-1])
    viewing_angle = theta + CYLINDER_VIEW_ROTATION
    horizontal = CYLINDER_RADIUS*np.sin(viewing_angle)
    axial = x/window*CYLINDER_HEIGHT/2
    vertical = axial - CYLINDER_ELLIPSE_DEPTH*np.cos(viewing_angle)
    front = np.cos(viewing_angle) >= 0
    return horizontal, vertical, axial, theta, front


def draw_phase_cylinder(ax, positions, phase, record, show_position_labels=False):
    """Orthographic cylinder: vertical position, polar phase, dashed rear curve."""
    window = CYLINDER_WINDOWS[record['time']]
    selected = abs(positions) < window
    positions, phase = positions[selected], phase[selected]
    assert np.sum(np.diff(phase)<-np.pi)==record['wrapped_drops']
    angles = np.linspace(0, 2*np.pi, CYLINDER_RING_SAMPLES)
    horizontal = CYLINDER_RADIUS*np.sin(angles)
    depth = -CYLINDER_ELLIPSE_DEPTH*np.cos(angles)
    for height in np.linspace(-CYLINDER_HEIGHT/2, CYLINDER_HEIGHT/2, CYLINDER_RING_COUNT):
        ax.plot(horizontal, height+depth, color=CYLINDER_GRID_COLOR,
                lw=CYLINDER_GRID_WIDTH, alpha=CYLINDER_GRID_ALPHA)
    for angle in np.linspace(0, 2*np.pi, CYLINDER_MERIDIAN_COUNT, endpoint=False):
        u = CYLINDER_RADIUS*np.sin(angle)
        v = -CYLINDER_ELLIPSE_DEPTH*np.cos(angle)
        ax.plot([u,u], [-CYLINDER_HEIGHT/2+v,CYLINDER_HEIGHT/2+v],
                color=CYLINDER_GRID_COLOR, lw=CYLINDER_GRID_WIDTH, alpha=CYLINDER_GRID_ALPHA)
    for height in (-CYLINDER_HEIGHT/2,CYLINDER_HEIGHT/2):
        ax.plot(horizontal,height+depth,color=CYLINDER_GRID_COLOR,lw=CYLINDER_CAP_WIDTH)
    u,v,_,_,front = cylinder_curve(positions,phase,window)
    ax.plot(u,np.where(front,np.nan,v),color=PHASE_COLOR,lw=CYLINDER_FRONT_WIDTH,
            linestyle=CYLINDER_REAR_DASH)
    ax.plot(u,np.where(front,v,np.nan),color=PHASE_COLOR,lw=CYLINDER_FRONT_WIDTH)
    top=CYLINDER_HEIGHT/2
    for angle,label in ((0,'0'),(np.pi,r'$\pi\equiv-\pi$'),
                        (np.pi/2,r'$\pi/2$'),(-np.pi/2,r'$-\pi/2$')):
        view=angle+CYLINDER_VIEW_ROTATION
        horizontal=(CYLINDER_RADIUS+CYLINDER_LABEL_OFFSET)*np.sin(view)
        vertical=top-(CYLINDER_ELLIPSE_DEPTH+CYLINDER_LABEL_OFFSET)*np.cos(view)
        if np.cos(view)>0:
            vertical += CYLINDER_FRONT_LABEL_LIFT
        if horizontal < -CYLINDER_RADIUS/2:
            vertical += CYLINDER_LEFT_LABEL_LIFT
        alignment='left' if horizontal>CYLINDER_RADIUS/2 else 'right' if horizontal<-CYLINDER_RADIUS/2 else 'center'
        ax.text(horizontal,vertical,label,ha=alignment,va='center',
                fontsize=CYLINDER_LABEL_SIZE,color=PHASE_COLOR)
    if show_position_labels:
        axis_x=-CYLINDER_RADIUS-CYLINDER_AXIS_OFFSET
        ax.annotate('',xy=(axis_x,top),xytext=(axis_x,-top),
                    arrowprops={'arrowstyle':'->','color':'0.35','lw':CYLINDER_CAP_WIDTH})
        for position in (-window,0,window):
            ax.text(axis_x-CYLINDER_POSITION_LABEL_OFFSET,position/window*top,f'{position:g}',
                    ha='right',va='center',fontsize=CYLINDER_LABEL_SIZE,color='0.35')
        ax.text(axis_x,top+CYLINDER_TOP_MARGIN/2,r'$x/\xi$',ha='center',
                fontsize=CYLINDER_LABEL_SIZE,color='0.35')
    ax.set(xlim=(-CYLINDER_RADIUS-CYLINDER_AXIS_MARGIN-CYLINDER_AXIS_OFFSET,CYLINDER_RADIUS+CYLINDER_AXIS_MARGIN),
           ylim=(-top-CYLINDER_BOTTOM_MARGIN,top+CYLINDER_TOP_MARGIN))
    ax.set_aspect('equal')
    ax.set_axis_off()
    ax.set_title(f"t = {record['time']:g}\n≈ {record['wrapped_drops']} phase turn"+
                 ('' if record['wrapped_drops']==1 else 's'),fontsize=PHASE_TITLE_SIZE)


def draw_phase_panels(fig, positions, phases, records):
    fig.text(*PHASE_HEADING_POSITION, r'PHASE ON CYLINDERS  |  $\widetilde F=0.8$',
             fontsize=LABEL_SIZE,color=COLORS['0.8'])
    for index,(bounds,phase,record) in enumerate(zip(PHASE_BOUNDS,phases,records)):
        ax=fig.add_axes(bounds)
        draw_phase_cylinder(ax,positions,phase,record,show_position_labels=True)


def save_phase_figure(positions, phases, phase_records, times, densities):
    fig, axes = plt.subplots(2,len(PHASE_TIMES),figsize=PHASE_FIGURE_SIZE,dpi=DPI,
                             gridspec_kw={'height_ratios':PHASE_HEIGHT_RATIOS})
    fig.subplots_adjust(**PHASE_FIGURE_MARGINS)
    for index,(phase,record) in enumerate(zip(phases,phase_records)):
        draw_phase_cylinder(axes[0,index],positions,phase,record,show_position_labels=True)
        row,=np.flatnonzero(np.isclose(times,record['time']))
        axes[1,index].plot(positions,densities[row],color=DENSITY_COLOR,lw=DENSITY_LINE_WIDTH)
        window=CYLINDER_WINDOWS[record['time']]
        axes[1,index].set(xlim=(-window,window),xlabel=r'$x/\xi$',
                          ylim=(0,densities.max()+DENSITY_PADDING))
        axes[1,index].grid(alpha=GRID_ALPHA)
    axes[1,0].set_ylabel(r'$n(x)/n_0$')
    fig.suptitle(r'$\widetilde G=-0.8$, $M=3m$, $\widetilde F=0.8$: cylindrical phase and density',fontsize=CLOCK_SIZE)
    for suffix in ('png','pdf'):
        fig.savefig(OUTPUT/('phase_snapshots.'+suffix),dpi=DPI)
    plt.close(fig)


def main():
    velocities, sources, grids = {}, {}, {}
    for force in FORCES:
        directory = OUTPUT / DATA_DIRECTORIES[force]
        records = json.loads((directory/'manifest.json').read_text())
        selected = [r for r in records if r['kind'] == 'velocity']
        assert selected, f'Load the selected velocity run for F={force}'
        if force=='1':
            selected=[r for r in selected if r['dt']==GRIDS[force]['dt'] and
                      r['length']==GRIDS[force]['length'] and r['dx']==GRIDS[force]['dx']]
        velocities[force] = stitch(selected, directory)
        sources[force] = selected
        grids[force] = GRIDS[force]
    directory = OUTPUT/'data_F0.8'
    records = json.loads((directory/'manifest.json').read_text())
    grid = grids['0.8']
    snapshots = sorted([r for r in records if r['kind']=='field' and r['time'] <= FINAL_TIME],
                       key=lambda r:r['time'])
    times = np.array([r['time'] for r in snapshots])
    assert len(times) and np.all(np.diff(times)>0) and np.isclose(times[-1], FINAL_TIME)
    arrays = [np.load(directory/r['cache']) for r in snapshots]
    positions = arrays[0]['positions']
    assert all(np.array_equal(a['positions'], positions) for a in arrays)
    fields = np.array([a['field'] for a in arrays])
    densities = abs(fields)**2
    assert np.isfinite(densities).all() and (densities >= 0).all()
    assert (abs(positions) < WINDOW).all()
    assert np.allclose(np.diff(positions), STRIDE*grid['dx'])
    phases, phase_records = phase_snapshots(times, positions, fields)
    save_phase_figure(positions, phases, phase_records, times, densities)
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
    density_ax.text(0.02,0.91,r'BOSON DENSITY  |  $\widetilde F=0.8$', transform=density_ax.transAxes,
                    color=DENSITY_COLOR, fontsize=LABEL_SIZE)
    fig.text(*TITLE_POSITION, 'Attractive driven impurity: velocity, density and phase', fontsize=TITLE_SIZE)
    fig.text(*SUBTITLE_POSITION, r'$\widetilde G=-0.8$    |    $M=3m$    |    $\gamma=0.1$    |    Impurity frame',
             fontsize=LABEL_SIZE, color='0.4')
    clock = fig.text(*CLOCK_POSITION, '', ha='right', fontsize=CLOCK_SIZE)
    draw_phase_panels(fig, positions, phases, phase_records)
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
                'color_reference':'https://arxiv.org/pdf/2606.13645, Fig. 2(a)',
                'fps':FPS,'duration_seconds':len(times)/FPS,
                'velocity_rows':{f:len(v) for f,v in velocities.items()},
                'velocity_restart_rule':'Continuation supersedes earlier records from its restart time',
                'interpolation':'No density interpolation; each frame is a saved configuration',
                'endpoint_time':FINAL_TIME, 'phase_snapshots':phase_records,
                'phase_convention':'Arg[phi(x,t) exp(i t - i pi/2)] in [-pi,pi)',
                'phase_reference':'https://arxiv.org/pdf/2606.13645, Fig. 3',
                'phase_display':'Three fixed F=0.8 cylinders: position along the axis, polar angle is phase; rear curve dashed',
                'cylinder_reference':CYLINDER_REFERENCE,
                'cylinder_geometry':'Viewing angle a=theta+pi/2; (R sin(a), x H/(2 window)-ellipse_depth cos(a)); cos(a)>=0 is front',
                'cylinder_spatial_windows':CYLINDER_WINDOWS,
                'cylinder_view_rotation':CYLINDER_VIEW_ROTATION,
                'cylinder_interpolation':'Linear unwrapped-angle interpolation for display geometry only'}
    (OUTPUT/'animation_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Rendered {len(times)} saved configurations through t={times[-1]:g}',flush=True)


if __name__ == '__main__':
    main()
