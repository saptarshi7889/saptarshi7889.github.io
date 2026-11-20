# Repulsive quenched animation

Fig. 8 (left) velocity animation for V0/v=0.5, 1, 1.5, 2.5, 3.5 and 4,
with G tilde=1, M=3m and gamma=0.1, through t=40. The density inset is
explicitly labelled as corresponding only to V0/v=1.5.
Paper: https://arxiv.org/abs/2507.10402.

Source: `Velocity_initial_vel_final.tar.gz`, `Actual/V1.5/dx3000`.
The grid spacing is 1/3000, dt=0.01, L=1000. All 16 saved density snapshots
at t=2.5, 5, ..., 40 are retained. Density is Re(psi)^2+Im(psi)^2.
Only -40<x<40 is used, sampled every 150th grid point (spacing 0.05).
Coordinates are reconstructed from grid indices and checked against the
rounded coordinates in the source files. Source data are never changed.

The layout and rendering are adapted from the existing driven F4 animation:
colored velocity histories with a legend, amber tracers, teal density curve and boson beads,
and a shaded coral impurity at x=0. The illustrated uniform-bath opening
and transition to the first snapshot are labelled illustrative.

With the existing NumPy, Matplotlib, Pillow and GStreamer installation:

```bash
python3 load_archive.py
python3 load_velocities.py
MPLCONFIGDIR=/tmp/gpe-animation-mpl python3 animate.py
```

Archive loading is needed only once. It caches the small sampled arrays in
`plot_data.npz`; later appearance changes require only `animate.py`.
Outputs are `velocity_density_animation.mp4`, `.gif`, intro/final PNGs,
`animation_manifest.json`, and the encoding log. Rerunning the renderer
replaces these generated outputs.

Playback is 1.5 times faster than the first version: 31 frames at 7.5 fps
(about 4.13 seconds). GIF durations alternate to approximate that rate within
the format's 10 ms timing precision. Velocity histories are cached separately
in `all_velocities.npz`, with source archive members recorded in
`velocity_sources.json`. The V0/v=6 and 6.5 curves are omitted;
the velocity y-axis extends to 4.5.

`Quantum_flutter.mp4` animates Fig. 13(a) with the Fig. 14 density inset:
M=8m, V0/v=3.5, gamma=0.1, and couplings 3, 1, 0.85, 0.75, 0.65, 0.5.
The density inset uses only G tilde=0.65. Both histories and density snapshots
extend through t=50, at 6 fps (20% slower than the earlier animation), with
the same illustrated opening. The impurity sphere is 20% smaller, with an
moving arrows tracking the blue bosonic density rather than the impurity.
A second inset below the wide density view zooms to -5<x<5 to highlight the
cloud oscillation around the fixed impurity. Both insets use the same G=0.65
snapshots. The wide-view arrow tracks the depletion's right half-depth
shoulder; the zoom arrow tracks a point 0.15 to the right of its minimum.
The existing velocity-density animation is retained.

To reproduce it with the existing dependencies:

```bash
python3 load_quantum_flutter.py Different_coupling.tar.gz Different_masses.tar.gz
python3 prepare_quantum_flutter.py
MPLCONFIGDIR=/tmp/gpe-animation-mpl python3 animate_quantum_flutter.py
```

The first command streams the archives without extracting the large fields;
it caches sampled arrays and source catalogs in `quantum_flutter_data/`.
The preparation step selects the smallest grid spacing (largest dx-folder
number) with continuous velocity data from t=0 to 50 for each coupling,
merging restart files within the same folder. It requires all twenty density
snapshots at t=2.5, 5, ..., 50 in a single G=0.65 folder. Source choices and
grid parameters are recorded in `quantum_flutter_data/source_manifest.json`.
Preparation can also use a fully read nested target-mass archive while the
outer scan continues through unrelated masses; the completed source scopes
are recorded in the manifest.
After caching, rerun only the renderer to adjust the appearance. Additional
outputs are `Quantum_flutter.gif`, intro/final PNGs, an encoding log, and
`Quantum_flutter_manifest.json`.
