# Attractive stationary polaron dispersion

Parameters: Gtilde = G/(hbar v) = -0.8, M/m = 5, gamma = 0.1.
This is a stationary-state momentum sweep, not time evolution after a quench.
The repulsive animation and its data are preserved separately.

## Sources and scope

- [Majumdar and Petković, arXiv:2507.10402v2](https://arxiv.org/html/2507.10402v2),
  III B, Eqs. (8), (9), (11)–(13): conventions, momentum and energy functional.
  That paper treats repulsive coupling; the attractive continuation below is
  evaluated here, rather than attributed to its repulsive critical-velocity formula.
- [Jager et al., Physical Review Research 2, 033142 (2020)](https://doi.org/10.1103/PhysRevResearch.2.033142):
  attractive mean-field condensate deformation and coth solution.

The calculation retains the same reduced-mass mean-field equation as the
existing repulsive plot, uses mu = g n0 in the thermodynamic limit, and omits
quantum fluctuations and finite-size corrections. No novelty claim is made.
No local Zotero library was accessible during the source check.

## Attractive continuation and root selection

Write r = M/m, s = sqrt(1+1/r), u = Vf/v, a = u/s,
b = sqrt(1-a^2), k = Gtilde/s, and c = b coth(x0).
The density-peak solution has real x0 > 0 and c > b. Its boundary condition is

    c^3 + k c^2 - b^2 c + k a^2 = 0.

For negative k there is exactly one root c > b. A bracketed solver selects
this root directly. Other roots, including dip solutions when real, are not
used to connect the branches. The negative tanh root of the repulsive
ansatz is not a substitute for the nonsingular attractive coth profile.

For z = x/xi, xi = hbar/sqrt(m g n0), the density is

    rho(z) = a^2 + b^2 coth^2(b |z|/s + x0).

The implementation evaluates this without overflowing coth or dividing by
b at the sonic endpoint. With T = tanh(b |z|/s), the amplitude is
(c+b T)/(1+c T/b). At b=0 its exact limit is c/(1+c |z|/s),
giving rho(z) = 1 + [c/(1+c |z|/s)]^2.
The endpoint therefore remains a peak and has an algebraic tail.

Choose the continuous phase theta = 0 at u=0, and otherwise

    theta = sign(u) 2 [atan2(b, |a|) - atan2(c, |a|)].
    q = P/(hbar n0) = r u sqrt(gamma) + 2a(c-b) + theta.
    epsilon = Ep/(g n0)
            = s [4b^3 - 3b^2 c - c^3]/[3 sqrt(gamma)] + r u^2/2.

The positive-velocity branch runs u: 0 -> s. The negative-velocity branch
runs u: -s -> 0, with q shifted by 2pi. They are copies of the same
physical peak solution, and are both blue. They are drawn separately.

## Gap and checks

For these parameters the branches terminate at

    q_left  = 2.4043351887853044
    q_right = 3.878850118394282
    width   = 1.4745149296089775.

The endpoint velocity is |Vf|/v = sqrt(1+1/5) = 1.0954451150,
the sound threshold of this reduced-mass mean-field equation. Both endpoint
energies are epsilon = 0.9005065295; epsilon(q=0) = -3.7085954802.
The gap is a missing momentum interval in this localized stationary family,
not a vertical excitation-energy gap or proof of a gap in the full many-body
spectrum. No curve or animation frames interpolate through it.

Checks cover the cubic residual, increasing momentum on each branch,
reflection/periodicity, density symmetry, rho >= 1, a central peak,
monotonic decay away from the impurity, the derivative jump, and

    d epsilon/dq = u/sqrt(gamma).

As an independent energy check, numerical quadrature evaluates

    epsilon = [integral (rho-1)^2 dz + Gtilde rho(0)]/sqrt(gamma)
              + r u^2/2.

Here the gradient and bath-interaction energies each contribute half the
integral, as follows by differentiating the coth wavefunction. The check
includes zero velocity, an intermediate velocity, and the exact sonic limit
on both branches. Errors are recorded in manifest.json.

## Files and regeneration

- `dispersion.pdf`, `dispersion_preview.png`: plot with matching density inset.
- `dispersion_density.mp4`, `.gif`: 242 frames at 43.2 fps, with a jump between
  the two branches instead of fictitious states in the gap.
- `stationary_states.csv`: q, epsilon, u, c, a, b, theta, peak-solution code 0.
- `stationary_data.npz`: frame states, density profiles, x/xi, and dense samples.
  Dense columns are u, q, epsilon, c, a, b, theta.
- `animate.py`, `manifest.json`, `encoding.log`: generator, checks, encoding log.

Using an existing scientific Python installation with NumPy, SciPy,
Matplotlib and Pillow, and GStreamer pngdec/x264enc/mp4mux plugins:

```sh
MPLCONFIGDIR=/tmp/stationary-polaron-mpl python media/Attractive_quenched_animation/Stationary_polaron_dispersion/animate.py
```

No dependencies were installed. Regeneration replaces only this directory's
outputs. Temporary PNG frames are removed automatically.
