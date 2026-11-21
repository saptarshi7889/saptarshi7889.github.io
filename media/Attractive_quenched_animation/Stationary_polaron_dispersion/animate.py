"""Attractive coth continuation of the stationary mean-field dispersion.

Sources: arXiv:2507.10402v2 III B and PhysRevResearch.2.033142.
The unique nonsingular peak root is retained; dip roots are excluded.

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
from scipy.integrate import quad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

OUTPUT = Path(__file__).resolve().parent
MASS_RATIO = 5.0
COUPLING = -0.8
GAMMA = 0.1
MASS_FACTOR = np.sqrt(1 + 1 / MASS_RATIO)
SCALED_COUPLING = COUPLING / MASS_FACTOR
ROOT_TOLERANCE = 1e-13
CHECK_TOLERANCE = 1e-9
SLOPE_TOLERANCE = 3e-5
DENSE_POINTS_PER_LEG = 6401
QUADRATURE_TOLERANCE = 1e-8
HALF_PERIOD = np.pi
PERIOD = 2*np.pi
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
TITLE_FONT_SIZE = 18
TITLE_Y = 0.98
PARAMETERS_Y = 0.90
CAPTION_Y = 0.025
GAP_LABEL_POSITION = (0.5, 0.88)
TEXT_CENTER_X = 0.5
INSET_BOUNDS = (0.365, 0.30, 0.34, 0.27)
AXIS_MARGINS = (0.10, 0.97, 0.14, 0.84)
ANNOTATION_POSITION = (0.02, 0.95)
BACKGROUND = '#fafbfe'
BLUE = '#2466b3'
COLORS = {'peak': BLUE}
GRID_ALPHA = 0.18
CURSOR_ALPHA = 0.25
DENSITY_PADDING = 0.08
ENERGY_PADDING = 0.15
MP4_QUANTIZER = 18
PNG_COMPRESSION = 3
GIF_TIME_QUANTUM_MS = 10
GIF_COLORS = 128
PREVIEW_MOMENTUM_FRACTION = 0.65
BRANCH_CODE = {'peak': 0}
X = np.linspace(-X_LIMIT, X_LIMIT, X_POINTS)


def peak_root(u):
    """Use c=b*coth(x0)>b, the unique nonsingular density-peak root.

    Solving for c instead of coth(x0) also covers the sonic limit b=0.
    The other real cubic roots, when present, belong to density-dip profiles.
    """
    a = u / MASS_FACTOR
    b = np.sqrt(max(0.0, 1-a*a))
    def residual(c):
        return c**3 + SCALED_COUPLING*c*c - b*b*c + SCALED_COUPLING*a*a
    upper = b + abs(SCALED_COUPLING) + 1
    return brentq(residual, b, upper, xtol=ROOT_TOLERANCE)


def density_profile(z, a, b, c):
    """Stable coth profile, including its algebraically decaying sonic limit."""
    distance = np.abs(z) / MASS_FACTOR
    if b == 0:
        amplitude = c / (1+c*distance)
    else:
        tangent = np.tanh(b*distance)
        amplitude = (c+b*tangent) / (1+(c/b)*tangent)
    return a*a + amplitude*amplitude


def state(u, branch='peak', negative_half=False):
    """Return P, E, c=b*coth(x0), a, b, phase and density in existing units."""
    a = u / MASS_FACTOR
    b = np.sqrt(max(0.0, 1-a*a))
    c = peak_root(u)
    theta = 0.0 if u == 0 else np.sign(u)*2*(
        np.arctan2(b, abs(a))-np.arctan2(c, abs(a)))
    p = MASS_RATIO*u*np.sqrt(GAMMA) + 2*a*(c-b) + theta
    if negative_half:
        p += PERIOD
    energy = (MASS_FACTOR*(4*b**3-3*b*b*c-c**3)/(3*np.sqrt(GAMMA))
              + 0.5*MASS_RATIO*u*u)
    return p, energy, c, a, b, theta, density_profile(X, a, b, c)


UC = MASS_FACTOR
LEGS = [('peak', False, 0.0, UC), ('peak', True, -UC, 0.0)]


def build_data():
    legs = []
    for branch, negative, start, end in LEGS:
        velocities = np.linspace(start, end, DENSE_POINTS_PER_LEG)
        rows = np.array([state(u, branch, negative)[:6] for u in velocities])
        legs.append((velocities, rows))
    return legs


def validate(legs):
    """Check root selection, peak shape, energy functional, symmetry and slope."""
    max_residual = 0.0
    max_slope_error = 0.0
    max_functional_error = 0.0
    for (u, rows), (branch, negative, _, _) in zip(legs, LEGS):
        p, energy, c, a, b, theta = rows.T
        residual = c**3 + SCALED_COUPLING*c*c - b*b*c + SCALED_COUPLING*a*a
        max_residual = max(max_residual, float(np.max(abs(residual))))
        assert np.all(c > b), 'Only the peak-producing root is admissible'
        assert np.all(np.diff(p) > 0), 'Momentum must increase on each branch'
        slope = np.gradient(energy, p, edge_order=2)
        max_slope_error = max(max_slope_error, float(np.max(
            abs(slope[2:-2]-u[2:-2]/np.sqrt(GAMMA)))))
        for index in (0, len(u)//2, -1):
            density = state(u[index], branch, negative)[-1]
            assert np.all(density >= 1-CHECK_TOLERANCE)
            assert density[X_POINTS//2] > 1
            assert np.max(abs(density-density[::-1])) < CHECK_TOLERANCE
            assert np.all(np.diff(density[X_POINTS//2:]) <= CHECK_TOLERANCE)
            # rho'(0+)/rho(0) = 2*Gtilde/s^2, including the sonic limit.
            origin_density = a[index]**2+c[index]**2
            derivative = 2*c[index]*(b[index]**2-c[index]**2)/MASS_FACTOR
            assert abs(derivative/origin_density-2*COUPLING/MASS_FACTOR**2) < CHECK_TOLERANCE
            integral = 2*quad(lambda z: (density_profile(z, a[index], b[index], c[index])-1)**2,
                              0, np.inf, epsabs=QUADRATURE_TOLERANCE)[0]
            functional_energy = ((integral+COUPLING*origin_density)/np.sqrt(GAMMA)
                                 + 0.5*MASS_RATIO*u[index]**2)
            max_functional_error = max(max_functional_error, abs(functional_energy-energy[index]))
    assert np.allclose(legs[0][1][:, 1], legs[1][1][::-1, 1], atol=CHECK_TOLERANCE, rtol=0)
    assert np.allclose(legs[0][1][:, 0]+legs[1][1][::-1, 0], PERIOD, atol=CHECK_TOLERANCE, rtol=0)
    gap_left, gap_right = legs[0][1][-1, 0], legs[1][1][0, 0]
    assert gap_left < HALF_PERIOD < gap_right
    assert max_residual < CHECK_TOLERANCE
    assert max_slope_error < SLOPE_TOLERANCE
    assert max_functional_error < QUADRATURE_TOLERANCE
    return {'max_cubic_residual': max_residual,
            'max_dimensionless_hellmann_feynman_error': max_slope_error,
            'max_energy_functional_error': max_functional_error,
            'limiting_velocity_over_sound': UC,
            'momentum_gap': [float(gap_left), float(gap_right)],
            'momentum_gap_width': float(gap_right-gap_left),
            'endpoint_energy': float(legs[0][1][-1, 1]),
            'zero_momentum_energy': float(legs[0][1][0, 1])}


def frame_state(p, legs):
    for (velocities, rows), (branch, negative, start, end) in zip(legs, LEGS):
        if rows[0, 0]-ROOT_TOLERANCE <= p <= rows[-1, 0]+ROOT_TOLERANCE:
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
                label='Peak solution' if index == 0 else None)
    ax.set(xlim=(0, 2*np.pi), ylim=(min(np.min(rows[:, 1]) for _, rows in legs)-ENERGY_PADDING, max(np.max(rows[:, 1]) for _, rows in legs)+ENERGY_PADDING),
           xlabel=r'$P/(\hbar n_0)$', ylabel=r'$E_p/(g n_0)$')
    ax.set_xticks(np.linspace(0, 2*np.pi, 5), ['0', r'$\pi/2$', r'$\pi$', r'$3\pi/2$', r'$2\pi$'])
    ax.grid(alpha=GRID_ALPHA)
    ax.legend(loc='upper right', frameon=False)
    gap_left, gap_right = legs[0][1][-1, 0], legs[1][1][0, 0]
    ax.axvspan(gap_left, gap_right, color='gray', alpha=GRID_ALPHA)
    ax.text(*GAP_LABEL_POSITION, 'No peak solution', transform=ax.transAxes, ha='center', fontsize=INSET_FONT_SIZE)
    fig.suptitle('Attractive stationary polaron dispersion', fontsize=TITLE_FONT_SIZE, y=TITLE_Y)
    fig.text(TEXT_CENTER_X, PARAMETERS_Y,
             rf'$\widetilde G={COUPLING:g},\quad M/m={MASS_RATIO:g},\quad\gamma={GAMMA:g}$',
             ha='center')
    inset = fig.add_axes(INSET_BOUNDS)
    inset.set(xlim=(-X_LIMIT, X_LIMIT), ylim=(0, max(state(u)[-1].max() for u in (0, UC))+DENSITY_PADDING),
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
    text = ax.text(*ANNOTATION_POSITION, '', transform=ax.transAxes, ha='left', va='top')
    fig.text(TEXT_CENTER_X, CAPTION_Y, 'Sweep through stationary states; not real-time evolution.', ha='center', fontsize=INSET_FONT_SIZE)

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
    update(PREVIEW_MOMENTUM_FRACTION*legs[0][1][-1, 0])
    fig.savefig(OUTPUT/'dispersion_preview.png', dpi=DPI)
    fig.savefig(OUTPUT/'dispersion.pdf')
    # Traverse each existing branch separately: never interpolate across the gap.
    momenta = np.concatenate([np.linspace(rows[0, 0], rows[-1, 0],
                                         (ANIMATION_FRAMES+1)//2) for _, rows in legs])
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
               header='P_over_hbar_n0,E_over_gn0,Vf_over_v,c_b_coth_x0,a,b,theta,peak_solution_0',
               comments='')
    np.savez_compressed(OUTPUT/'stationary_data.npz', states=data, x_over_xi=X,
                        density_over_n0=np.array(frame_density),
                        dense_states=np.concatenate([np.column_stack((u, rows)) for u, rows in legs]))
    manifest = {'source': 'https://arxiv.org/pdf/2507.10402v2',
                'equations': [8, 9, 11, 12, 13], 'mass_ratio': MASS_RATIO,
                'coupling': COUPLING, 'gamma': GAMMA, 'checks': checks,
                'frames': len(momenta), 'fps': FPS, 'duration_seconds': len(momenta)/FPS,
                'spatial_units': 'x/xi', 'density_units': '|psi0|^2/n0',
                'density_interval': [-X_LIMIT, X_LIMIT],
                'blue': 'unique nonsingular peak solution, c=b*coth(x0)>b',
                'gap_interpretation': 'missing momentum interval within the localized peak family; not an excitation energy gap',
                'additional_source': 'https://doi.org/10.1103/PhysRevResearch.2.033142',
                'interpretation': 'stationary momentum sweep; not a quench or time evolution'}
    (OUTPUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
