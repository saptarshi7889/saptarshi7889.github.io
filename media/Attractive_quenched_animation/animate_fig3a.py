"""Render requested velocity curves and V0=2 density in the existing style."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image
import animate_attractive as style
from prepare_fig3a import INITIAL_VELOCITIES, FINAL_TIME, WINDOW, DENSITY_INITIAL_VELOCITY

OUTPUT = Path(__file__).resolve().parent / 'fig3a'
FRAME_INTERVAL = 0.1
FRAME_COUNT = round(FINAL_TIME / FRAME_INTERVAL) + 1
BASE_FPS = 22.95
PLAYBACK_SPEED = 2.0
FPS = BASE_FPS * PLAYBACK_SPEED
FPS_FRACTION = '459/10'
VELOCITY_BOUNDS = (0.10, 0.12, 0.86, 0.73)
DENSITY_BOUNDS = (0.28, 0.48, 0.68, 0.40)
BEAD_SPACING = 0.5
COLORS = ('#4423bb', '#5752ff', '#16b4cf', '#4bc65b', '#ffb21c')
VELOCITY_LIMITS = (-0.5, 4.8)
DENSITY_LABEL = rf'BOSON DENSITY · $V_0/v={DENSITY_INITIAL_VELOCITY:g}$'
PNG_COMPRESSION = 3
GIF_QUANTUM_MS = 10
SOLITON_START_TIME = 25.0
SOLITON_LABEL_POSITION = (0.84, 0.68)
SOLITON_COLOR = '#333333'


def main():
    data = np.load(OUTPUT/'plot_data.npz')
    metadata = json.loads((OUTPUT/'source_manifest.json').read_text())
    x, saved_times, saved_density = data['positions'], data['times'], data['densities']
    assert saved_times[-1] == FINAL_TIME
    assert all(data[f'velocity_{v:g}'][-1, 0] == FINAL_TIME for v in INITIAL_VELOCITIES)
    times = np.concatenate(([0.0], saved_times))
    densities = np.vstack((np.ones_like(x), saved_density))
    frame_times = np.linspace(0, FINAL_TIME, FRAME_COUNT)
    fig = plt.figure(figsize=style.FIGURE_SIZE, dpi=style.DPI, facecolor=style.BACKGROUND)
    ax = fig.add_axes(VELOCITY_BOUNDS, facecolor=style.BACKGROUND)
    ax.set(xlim=(0, FINAL_TIME), ylim=VELOCITY_LIMITS,
           xlabel=r'$tgn_0/\hbar$', ylabel=r'Impurity velocity $V/v$')
    ax.grid(alpha=style.GRID_ALPHA)
    ax.spines[['top', 'right']].set_visible(False)
    curves = []
    for v, color in zip(INITIAL_VELOCITIES, COLORS):
        values = data[f'velocity_{v:g}']
        line, = ax.plot([], [], color=color, lw=style.LINE_WIDTH, label=rf'$V_0/v={v:g}$')
        dot, = ax.plot([], [], 'D', color=color, ms=style.MARKER_SIZE)
        curves.append((values, line, dot))
    ax.legend(loc='upper right', ncol=len(INITIAL_VELOCITIES), fontsize=style.LEGEND_FONT_SIZE, frameon=False)
    cursor = ax.axvline(0, color=style.CURRENT_COLOR, alpha=style.CURSOR_ALPHA)
    padding = style.DENSITY_PADDING*np.ptp(densities)
    panel = ax.inset_axes(DENSITY_BOUNDS, facecolor='white')
    panel.set(xlim=(-WINDOW, WINDOW), ylim=(densities.min()-padding, densities.max()+padding),
              xlabel=r'Position relative to impurity $x/\xi$', ylabel=r'$n(x,t)/n_0$')
    panel.tick_params(labelsize=style.INSET_FONT_SIZE)
    panel.xaxis.label.set_size(style.INSET_FONT_SIZE)
    panel.yaxis.label.set_size(style.INSET_FONT_SIZE)
    panel.axhline(1, color='0.75', ls=':', lw=style.GUIDE_LINE_WIDTH)
    panel.axvline(0, color='0.75', ls=':', lw=style.GUIDE_LINE_WIDTH)
    indices = np.flatnonzero(abs(x) <= WINDOW)
    beads = indices[::round(BEAD_SPACING/(x[1]-x[0]))]
    density_line, = panel.plot(x[indices], densities[0, indices], color=style.BOSON_COLOR,
                       lw=style.DENSITY_LINE_WIDTH, alpha=style.DENSITY_ALPHA)
    density_dots, = panel.plot(x[beads], densities[0, beads], 'o', color=style.BOSON_COLOR,
                       ms=style.BOSON_DIAMETER, markeredgewidth=0)
    sphere = AnnotationBbox(OffsetImage(style.sphere_image(), zoom=style.IMPURITY_DIAMETER/style.SPHERE_PIXELS),
                            (0, 1), frameon=False, pad=0, zorder=style.IMPURITY_ZORDER)
    panel.add_artist(sphere)
    panel.text(*style.ANNOTATION_POSITION, DENSITY_LABEL, transform=panel.transAxes,
               fontsize=style.INSET_FONT_SIZE, color=style.BOSON_COLOR)
    soliton_indices = indices[x[indices] > 0]
    soliton_label = panel.annotate(
        'soliton', xy=(0, 0), xytext=SOLITON_LABEL_POSITION,
        textcoords='axes fraction', fontsize=style.INSET_FONT_SIZE, color=SOLITON_COLOR,
        ha='center', arrowprops=dict(arrowstyle='->', color=SOLITON_COLOR, shrinkB=0),
        visible=False)
    soliton_targets = []
    fig.suptitle('Impurity velocity and boson density', x=style.TITLE_POSITION[0], y=style.TITLE_POSITION[1],
                 ha='left', fontsize=style.MAIN_TITLE_SIZE)
    clock = fig.text(*style.CLOCK_POSITION, '', ha='right', fontsize=style.CLOCK_SIZE, color=style.VELOCITY_COLOR)
    fig.text(*style.SUBTITLE_POSITION, rf'$M=3m$  |  $\widetilde G=-0.8$  |  Density: $V_0/v={DENSITY_INITIAL_VELOCITY:g}$  |  Impurity frame',
             fontsize=style.SUBTITLE_SIZE, color='0.4')
    note = fig.text(0.10, 0.015, '', fontsize=style.INSET_FONT_SIZE, color='0.4')
    gif_frames = []
    with tempfile.TemporaryDirectory(prefix='fig3a-') as directory:
        frames = Path(directory)
        for index, time in enumerate(frame_times):
            right = min(np.searchsorted(times, time, side='right'), len(times)-1)
            left = max(0, right-1)
            weight = (time-times[left])/(times[right]-times[left])
            density = (1-weight)*densities[left]+weight*densities[right]
            for values, line, dot in curves:
                visible = values[values[:, 0] <= time+style.GRID_TOLERANCE]
                line.set_data(visible[:, 0], visible[:, 1])
                dot.set_data([time], [np.interp(time, values[:, 0], values[:, 1])])
            cursor.set_xdata([time, time])
            density_line.set_ydata(density[indices])
            density_dots.set_ydata(density[beads])
            height = np.interp(0, x, density)
            sphere.xy = sphere.xybox = (0, height)
            soliton_visible = time >= SOLITON_START_TIME
            soliton_label.set_visible(soliton_visible)
            if soliton_visible:
                minimum = soliton_indices[np.argmin(density[soliton_indices])]
                soliton_label.xy = (float(x[minimum]), float(density[minimum]))
                soliton_targets.append(list(soliton_label.xy))
            else:
                soliton_targets.append(None)
            clock.set_text(r'$tgn_0/\hbar = '+f'{time:.1f}'+r'$')
            exact = np.any(np.isclose(saved_times, time, atol=style.GRID_TOLERANCE))
            note.set_text('Density: saved simulation snapshot' if exact else
                          ('Density: uniform initial bath' if time == 0 else
                           f'Density: linear visual interpolation between t={times[left]:g} and {times[right]:g}'))
            path = frames/f'frame_{index:03d}.png'
            fig.savefig(path, dpi=style.DPI, pil_kwargs={'compress_level': PNG_COMPRESSION})
            with Image.open(path) as im:
                gif_frames.append(im.convert('RGB'))
            if index == FRAME_COUNT-1:
                fig.savefig(OUTPUT/'Fig3a_preview.png', dpi=style.DPI)
            if index % 50 == 0:
                print(f'Rendered {index+1}/{FRAME_COUNT}', flush=True)
        pipeline = ['gst-launch-1.0', '-e', 'multifilesrc', f'location={frames}/frame_%03d.png',
                    'index=0', f'stop-index={FRAME_COUNT-1}', f'caps=image/png,framerate=(fraction){FPS_FRACTION}',
                    '!', 'pngdec', '!', 'videoconvert', '!', 'video/x-raw,format=I420', '!', 'x264enc',
                    'pass=qual', f'quantizer={style.MP4_QUANTIZER}', 'speed-preset=medium', '!',
                    'video/x-h264,profile=high', '!', 'mp4mux', 'faststart=true', '!', 'filesink',
                    f'location={OUTPUT}/Fig3a.mp4']
        result = subprocess.run(pipeline, capture_output=True, text=True, env=dict(os.environ, GST_DEBUG='1'))
        (OUTPUT/'encoding.log').write_text(result.stdout+result.stderr)
        result.check_returncode()
        boundaries = np.rint(np.arange(FRAME_COUNT+1)*1000/FPS/GIF_QUANTUM_MS)
        durations = (np.diff(boundaries)*GIF_QUANTUM_MS).astype(int).tolist()
        gif_frames[0].save(OUTPUT/'Fig3a.gif', save_all=True, append_images=gif_frames[1:],
                           duration=durations, loop=0, optimize=False)
    plt.close(fig)
    metadata.update(initial_velocities=list(INITIAL_VELOCITIES), density_initial_velocity=DENSITY_INITIAL_VELOCITY,
                    saved_density_times=saved_times.tolist(), frame_times=frame_times.tolist(), fps=FPS,
                    density_interpolation='Linear interpolation for visualization; identified in each frame. Uniform bath at t=0.',
                    density_display_spacing=float(x[1]-x[0]), duration_seconds=FRAME_COUNT/FPS,
                    density_panel_count=1, density_bounds=list(DENSITY_BOUNDS),
                    density_layout='Inset inside velocity axis; bounds in axes coordinates',
                    playback_speed_relative_to_previous=PLAYBACK_SPEED,
                    soliton_annotation_start_time=SOLITON_START_TIME,
                    soliton_tracking='Minimum of the displayed density for 0 < x <= 40',
                    soliton_arrow_targets=soliton_targets)
    (OUTPUT/'Fig3a_manifest.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print('Created Fig3a.mp4 and Fig3a.gif', flush=True)


if __name__ == '__main__':
    main()
