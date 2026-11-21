# Stationary polaron dispersion

Source: [arXiv:2507.10402v2](https://arxiv.org/pdf/2507.10402v2),
Section III B, Eqs. (8)–(13). Parameters: G/(hbar v) = 1,
M/m = 6, gamma = 0.1. This is a sweep through stationary states,
not a simulation of time evolution after a quench.

## Dimensionless equations

Let r = M/m, u = Vf/v, s = sqrt(1 + 1/r), a = u/s,
b = sqrt(1 − a²), k = Gtilde/s, and t = tanh(x0).
Eq. (10) is solved for a_c = u_c/s, with left-hand side k.
Eq. (9) becomes the cubic

    b³ t³ + k b² t² − b³ t + k a² = 0.

The negative root gives an origin-centered density peak and is discarded.
The larger nonnegative root is the first (blue) solution; the smaller is
the second (red) solution. Their double root at |u| = u_c is evaluated
analytically to avoid numerical splitting. At u = 0, the second root is
t = 0, the dark soliton.

The plotted momentum and energy are

    q = P/(hbar n0) = r u sqrt(gamma) − 2ab(1 − t) + theta,
    epsilon = Ep/(g n0) = s b³ (4 − 3t − t³)/(3 sqrt(gamma)) + r u²/2.

The energy expression is Eq. (13) with its first two terms combined.
For z = x/xi and xi = hbar/sqrt(m g n0), Eq. (8) gives

    rho(z) = |psi0|²/n0 = a² + b² tanh²(b |z|/s + atanh(t)).

We use mu = g n0 (thermodynamic limit), as specified in the paper.
The phase factor in Eq. (8) has unit modulus. The periodic boundary
phase theta x/L affects momentum through Eq. (12), and does not alter
the density. Finite-size corrections are not included.

The sweep follows first solution u: 0 → uc, second solution uc → 0,
second solution 0 → −uc, then first solution −uc → 0. Negative momenta
are shifted by +2pi without changing energy or density, giving [pi, 2pi].
Eq. (11) is evaluated with a continuous phase convention: theta = pi
at the positive-half dark soliton and −pi at its negative-half copy.
The two copies give the same plotted momentum pi after the shift.

## Outputs and checks

- `dispersion_density.mp4` and `.gif`: momentum sweep with matching density inset.
  Playback is 43.2 fps (twice the previous 21.6 fps), lasting 5.625 seconds.
  GIF frame durations alternate between 20 and 30 ms to approximate this rate.
- `dispersion_preview.png` and `dispersion.pdf`: static view at momentum pi.
- `stationary_states.csv`: one row per animation frame; branch 0 is blue, 1 red.
- `stationary_data.npz`: frame states, normalized density profiles, spatial
  grid and dense dispersion samples. `dense_states` columns are u, q,
  epsilon, t, a, b, theta, in traversal order, including repeated joins.
- `manifest.json`: parameters, critical velocity, joins and validation errors.

Before rendering, the script verifies the cubic residual, increasing
momentum, continuity at all joins, energy periodicity, the dark-soliton
limit, symmetric density dips, and the dimensionless Hellmann–Feynman
relation d epsilon/dq = u/sqrt(gamma). The numerical derivative check
omits two samples at each branch endpoint, where the cubic roots coalesce.
Animation samples include the branch joins and the dark soliton exactly.

Run with an existing environment containing NumPy, SciPy, Matplotlib and
Pillow, plus the existing GStreamer pngdec/x264enc/mp4mux plugins:

```sh
MPLCONFIGDIR=/tmp/stationary-polaron-mpl python media/Stationary_polaron_dispersion/animate.py
```

No dependencies were installed for this work. Rendering reuses the available
scientific Python installation and GStreamer, as in the existing animations.
Rerunning replaces only the generated files in this directory. Temporary
PNG frames are created in the system temporary directory and removed afterward.
