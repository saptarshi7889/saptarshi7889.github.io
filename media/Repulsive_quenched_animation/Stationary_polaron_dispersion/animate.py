"""Stationary dispersion and density from arXiv:2507.10402v2, III B.

Run using an existing NumPy/SciPy/Matplotlib/Pillow installation. No time
evolution is simulated: the animation traverses stationary states in momentum.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

OUTPUT = Path(__file__).resolve().parent
MASS_RATIO = 6.0
COUPLING = 1.0
GAMMA = 0.1
MASS_FACTOR = np.sqrt(1 + 1 / MASS_RATIO)
SCALED_COUPLING = COUPLING / MASS_FACTOR
ROOT_TOLERANCE = 1e-13
PHYSICAL_ROOT_TOLERANCE = 1e-8
CHECK_TOLERANCE = 1e-9
SLOPE_TOLERANCE = 3e-5
DENSE_POINTS_PER_LEG = 6401
ANIMATION_FRAMES = 241
FPS_NUMERATOR = 216
FPS_DENOMINATOR = 5
FPS = FPS_NUMERATOR / FPS_DENOMINATOR
X_LIMIT = 10.0
X_POINTS = 801
FIGURE_SIZE = (10, 7)
DPI = 110
LINE_WIDTH = 2.2
MARKER_SIZE = 8
FONT_SIZE = 12
INSET_FONT_SIZE = 10
INSET_BOUNDS = (0.365, 0.30, 0.34, 0.27)
AXIS_MARGINS = (0.10, 0.97, 0.14, 0.84)
ANNOTATION_POSITION = (0.98, 0.09)
BACKGROUND = '#fafbfe'
BLUE = '#2466b3'
RED = '#cf393f'
COLORS = {'first': BLUE, 'second': RED}
GRID_ALPHA = 0.18
CURSOR_ALPHA = 0.25
DENSITY_PADDING = 0.08
ENERGY_PADDING = 0.15
MP4_QUANTIZER = 18
PNG_COMPRESSION = 3
GIF_TIME_QUANTUM_MS = 10
GIF_COLORS = 128
PREVIEW_MOMENTUM = np.pi
PROFILE_VELOCITY_FRACTION = 0.5
BRANCH_CODE = {'first': 0, 'second': 1}
X = np.linspace(-X_LIMIT, X_LIMIT, X_POINTS)


def critical_velocity():
    """Solve Eq. (10) for v_tilde_c, then convert to V_c/v."""
    def residual(a):
        numerator = 1 - 20*a*a - 8*a**4 + (1 + 8*a*a)**1.5
        return np.sqrt(max(0.0, numerator)) / (2*np.sqrt(2)*a) - SCALED_COUPLING
    a_c = brentq(residual, ROOT_TOLERANCE, 1 - ROOT_TOLERANCE,
                 xtol=ROOT_TOLERANCE)
    return MASS_FACTOR * a_c


UC = critical_velocity()


def shift_root(u, branch):
    """Solve Eq. (9) in t=tanh(x0); reject the negative, peak-producing root."""
    a = u / MASS_FACTOR
    b = np.sqrt(1 - a*a)
    if abs(abs(u) - UC) < ROOT_TOLERANCE:
        # At the double root, generic polynomial root finders lose accuracy.
        return b / (SCALED_COUPLING + np.sqrt(SCALED_COUPLING**2 + 3*b*b))
    roots = np.roots([b**3, SCALED_COUPLING*b*b, -b**3,
                      SCALED_COUPLING*a*a])
    physical = sorted(root.real for root in roots
                      if abs(root.imag) < PHYSICAL_ROOT_TOLERANCE
                      and 0 <= root.real < 1)
    if len(physical) != 2:
        raise ValueError(f'Expected two physical roots at u={u}: {roots}')
    return physical[-1] if branch == 'first' else physical[0]


def state(u, branch, negative_half=False):
    """Return dimensionless P, E, t, a, b, theta, and density."""
    a = u / MASS_FACTOR
    b = np.sqrt(1 - a*a)
    t = shift_root(u, branch)
    # Continuous phase choice at the dark soliton (a=t=0).
    if u == 0:
        theta = np.pi if branch == 'second' else 0.0
        if negative_half:
            theta = -theta
    else:
        theta = np.sign(u)*2*(np.arctan2(b, abs(a)) - np.arctan2(b*t, abs(a)))
    p = MASS_RATIO*u*np.sqrt(GAMMA) - 2*a*b*(1-t) + theta
    if negative_half:
        p += 2*np.pi
    energy = (MASS_FACTOR*b**3/(3*np.sqrt(GAMMA))
              * (-t**3 - 3*t + 4) + 0.5*MASS_RATIO*u*u)
    # Modulus squared of Eq. (8), normalized by n0, with mu=gn0.
    density = a*a + b*b*np.tanh(b*np.abs(X)/MASS_FACTOR + np.arctanh(t))**2
    return p, energy, t, a, b, theta, density


LEGS = [('first', False, 0.0, UC), ('second', False, UC, 0.0),
        ('second', True, 0.0, -UC), ('first', True, -UC, 0.0)]


def build_data():
    legs = []
    for branch, negative, start, end in LEGS:
        velocities = np.linspace(start, end, DENSE_POINTS_PER_LEG)
        rows = np.array([state(u, branch, negative)[:6] for u in velocities])
        legs.append((velocities, rows))
    return legs


def validate(legs):
    """Check equations, branch joins, periodicity and Hellmann–Feynman."""
    max_residual = 0.0
    max_slope_error = 0.0
    for (u, rows), (branch, negative, _, _) in zip(legs, LEGS):
        p, energy, t, a, b, theta = rows.T
        residual = SCALED_COUPLING*(a*a + b*b*t*t) - b**3*t*(1-t*t)
        max_residual = max(max_residual, float(np.max(abs(residual))))
        assert np.all(np.diff(p) > 0), 'Momentum must increase on every leg'
        # d(E/gn0)/d(P/hbar n0) = (Vf/v)/sqrt(gamma).
        slope = np.gradient(energy, p, edge_order=2)
        slope_error = np.max(abs(slope[2:-2] - u[2:-2]/np.sqrt(GAMMA)))
        max_slope_error = max(max_slope_error, float(slope_error))
        for index in (0, len(u)//2, -1):
            density = state(u[index], branch, negative)[-1]
            assert np.all(density >= 0) and np.all(density <= 1 + CHECK_TOLERANCE)
            assert np.max(abs(density-density[::-1])) < CHECK_TOLERANCE
            assert np.all(np.diff(density[X_POINTS//2:]) >= -CHECK_TOLERANCE)
    for previous, following in zip(legs[:-1], legs[1:]):
        assert np.allclose(previous[1][-1, :2], following[1][0, :2],
                           atol=CHECK_TOLERANCE, rtol=0)
        assert abs(previous[1][-1, 2]-following[1][0, 2]) < CHECK_TOLERANCE
    assert abs(legs[0][1][0, 0]) < CHECK_TOLERANCE
    assert abs(legs[-1][1][-1, 0] - 2*np.pi) < CHECK_TOLERANCE
    assert abs(legs[0][1][0, 1] - legs[-1][1][-1, 1]) < CHECK_TOLERANCE
    dark = state(0.0, 'second')
    assert abs(dark[0] - np.pi) < CHECK_TOLERANCE
    assert abs(dark[-1][X_POINTS//2]) < CHECK_TOLERANCE
    assert max_residual < CHECK_TOLERANCE
    assert max_slope_error < SLOPE_TOLERANCE
    return {'max_eq9_residual': max_residual,
            'max_dimensionless_hellmann_feynman_error': max_slope_error,
            'critical_velocity_over_sound': UC,
            'critical_scaled_velocity': UC/MASS_FACTOR,
            'branch_join_momenta': [float(leg[1][-1, 0]) for leg in legs[:-1]]}


def frame_state(p, legs):
    for (velocities, rows), (branch, negative, start, end) in zip(legs, LEGS):
        if p <= rows[-1, 0] + ROOT_TOLERANCE:
            if abs(p-rows[0, 0]) < ROOT_TOLERANCE:
                u = start
            elif abs(p-rows[-1, 0]) < ROOT_TOLERANCE:
                u = end
            else:
                u = brentq(lambda value: state(value, branch, negative)[0]-p,
                           min(start, end), max(start, end), xtol=ROOT_TOLERANCE)
            return u, branch, state(u, branch, negative)
    raise ValueError(f'Momentum outside the period: {p}')


def make_figure(legs):
    plt.rcParams.update({'font.size': FONT_SIZE, 'axes.facecolor': BACKGROUND,
                         'figure.facecolor': BACKGROUND})
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    left, right, bottom, top = AXIS_MARGINS
    fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top)
    for index, ((u, rows), (branch, _, _, _)) in enumerate(zip(legs, LEGS)):
        ax.plot(rows[:, 0], rows[:, 1], color=COLORS[branch], lw=LINE_WIDTH,
                label=f'{branch.capitalize()} solution' if index < 2 else None)
    ax.set(xlim=(0, 2*np.pi), ylim=(0, max(np.max(rows[:, 1]) for _, rows in legs)+ENERGY_PADDING),
           xlabel=r'$P/(\hbar n_0)$', ylabel=r'$E_p/(g n_0)$')
    ax.set_xticks(np.linspace(0, 2*np.pi, 5), ['0', r'$\pi/2$', r'$\pi$', r'$3\pi/2$', r'$2\pi$'])
    ax.grid(alpha=GRID_ALPHA)
    ax.legend(loc='upper right', frameon=False)
    fig.suptitle('Stationary polaron dispersion', fontsize=18, y=0.98)
    fig.text(0.5, 0.90,
             rf'$\widetilde G={COUPLING:g},\quad M/m={MASS_RATIO:g},\quad\gamma={GAMMA:g}$',
             ha='center')
    inset = fig.add_axes(INSET_BOUNDS)
    inset.set(xlim=(-X_LIMIT, X_LIMIT), ylim=(0, 1+DENSITY_PADDING),
              xlabel=r'$x/\xi$', ylabel=r'$|\psi_0|^2/n_0$')
    inset.tick_params(labelsize=INSET_FONT_SIZE)
    inset.xaxis.label.set_size(INSET_FONT_SIZE)
    inset.yaxis.label.set_size(INSET_FONT_SIZE)
    inset.axvline(0, color='gray', lw=1, alpha=CURSOR_ALPHA)
    inset.axhline(1, color='gray', lw=1, alpha=CURSOR_ALPHA)
    inset.grid(alpha=GRID_ALPHA)
    density_line, = inset.plot([], [], lw=LINE_WIDTH)
    point, = ax.plot([], [], 'o', ms=MARKER_SIZE)
    cursor = ax.axvline(0, color=BLUE, alpha=CURSOR_ALPHA)
    text = ax.text(*ANNOTATION_POSITION, '', transform=ax.transAxes, ha='right', va='bottom')
    fig.text(0.5, 0.025, 'Sweep through stationary states; not real-time evolution.', ha='center', fontsize=10)

    def update(p):
        u, branch, values = frame_state(p, legs)
        momentum, energy, _, _, _, _, density = values
        color = COLORS[branch]
        point.set_data([momentum], [energy])
        point.set_color(color)
        cursor.set_xdata([momentum, momentum])
        cursor.set_color(color)
        density_line.set_data(X, density)
        density_line.set_color(color)
        text.set_text(f'{branch.capitalize()} solution\n'
                      + r'$P/(\hbar n_0) = $' + f'{momentum:.3f}\n'
                      + r'$V_f/v = $' + f'{u:.3f}')
        return u, branch, values
    return fig, update


def main():
    legs = build_data()
    checks = validate(legs)
    fig, update = make_figure(legs)
    update(PREVIEW_MOMENTUM)
    fig.savefig(OUTPUT/'dispersion_preview.png', dpi=DPI)
    fig.savefig(OUTPUT/'dispersion.pdf')
    momenta = np.unique(np.concatenate((np.linspace(0, 2*np.pi, ANIMATION_FRAMES),
                                       [leg[1][-1, 0] for leg in legs[:-1]])))
    frame_rows = []
    frame_density = []
    gif_frames = []
    with tempfile.TemporaryDirectory(prefix='stationary-polaron-') as directory:
        frames = Path(directory)
        for index, p in enumerate(momenta):
            u, branch, values = update(p)
            frame_rows.append([values[0], values[1], u, values[2], values[3], values[4],
                               values[5], BRANCH_CODE[branch]])
            frame_density.append(values[-1])
            path = frames/f'frame_{index:03d}.png'
            fig.savefig(path, dpi=DPI, pil_kwargs={'compress_level': PNG_COMPRESSION})
            with Image.open(path) as image:
                gif_frames.append(image.convert('P', palette=Image.Palette.ADAPTIVE,
                                                colors=GIF_COLORS))
        pipeline = ['gst-launch-1.0', '-e', 'multifilesrc', f'location={frames}/frame_%03d.png',
                    'index=0', f'stop-index={len(momenta)-1}',
                    f'caps=image/png,framerate=(fraction){FPS_NUMERATOR}/{FPS_DENOMINATOR}', '!', 'pngdec', '!',
                    'videoconvert', '!', 'video/x-raw,format=I420', '!', 'x264enc',
                    'pass=qual', f'quantizer={MP4_QUANTIZER}', 'speed-preset=medium', '!',
                    'video/x-h264,profile=high', '!', 'mp4mux', 'faststart=true', '!',
                    'filesink', f'location={OUTPUT / "dispersion_density.mp4"}']
        result = subprocess.run(pipeline, capture_output=True, text=True,
                                env=dict(os.environ, GST_DEBUG='1'))
        (OUTPUT/'encoding.log').write_text(result.stdout+result.stderr)
        if result.returncode:
            raise RuntimeError('MP4 encoding failed; see encoding.log')
        boundaries = np.rint(np.arange(len(momenta)+1)*1000/FPS/GIF_TIME_QUANTUM_MS)
        durations = (np.diff(boundaries)*GIF_TIME_QUANTUM_MS).astype(int).tolist()
        gif_frames[0].save(OUTPUT/'dispersion_density.gif', save_all=True,
                           append_images=gif_frames[1:], duration=durations, loop=0,
                           optimize=False)
    plt.close(fig)
    data = np.array(frame_rows)
    np.savetxt(OUTPUT/'stationary_states.csv', data, delimiter=',',
               header='P_over_hbar_n0,E_over_gn0,Vf_over_v,tanh_x0,a,b,theta,branch_0_blue_1_red',
               comments='')
    np.savez_compressed(OUTPUT/'stationary_data.npz', states=data, x_over_xi=X,
                        density_over_n0=np.array(frame_density),
                        dense_states=np.concatenate([np.column_stack((u, rows)) for u, rows in legs]))
    manifest = {'source': 'https://arxiv.org/pdf/2507.10402v2',
                'equations': [8, 9, 10, 11, 12, 13], 'mass_ratio': MASS_RATIO,
                'coupling': COUPLING, 'gamma': GAMMA, 'checks': checks,
                'frames': len(momenta), 'fps': FPS, 'duration_seconds': len(momenta)/FPS,
                'spatial_units': 'x/xi', 'density_units': '|psi0|^2/n0',
                'density_interval': [-X_LIMIT, X_LIMIT],
                'blue': 'first solution, larger tanh(x0), shallower density dip',
                'red': 'second solution, smaller tanh(x0), deeper density dip',
                'interpretation': 'stationary momentum sweep; not a quench or time evolution'}
    (OUTPUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
