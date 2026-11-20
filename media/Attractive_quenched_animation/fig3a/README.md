# Fig. 3(a) style animation

Requested initial velocities: V0/v = 0.5, 1.5, 2.5, 3.5, 4.5.
The density inset inside the velocity plot shows V0/v = 2 in the impurity
frame, spanning x/xi = [-40, 40]. There is no additional zoom panel.
Both plots evolve from t = 0 to 40. Parameters: G = -0.8 and M = 3m
(the stored inverse mass is 0.333333).

The largest physical dx available for each velocity is used:

| V0/v | source directory | physical dx |
| --- | --- | --- |
| 0.5 | dx1000 | 0.001 |
| 1.5 | dx1000 | 0.001 |
| 2.5 | dx1000 | 0.001 |
| 3.5 | dx2000 | 0.0005 |
| 4.5 | dx5000 | 0.0002 |

The requested density snapshots are in V2/dx12500.tar.gz,
at t = 2.5, 5, 7.5, ..., 40 (dx = 0.00008, dt = 0.01, L = 1200).
Density is Re(psi)^2 + Im(psi)^2. Every 625th source point is used,
giving spacing 0.05, equivalent to every 500th point for dx10000.
Particle beads use spacing 0.5,
matching the earlier animation's display style; the connecting density
curve uses all sampled points.

Frames between saved densities use linear visual interpolation, explicitly
labelled in the animation. The t=0 density is the known uniform initial bath,
not a saved snapshot. Interpolated frames do not resolve the physical dynamics
between the 2.5-unit snapshot intervals. Velocity histories use the original
0.1-spaced data and have no missing intervals through t=40.

The animation has 401 frames at 45.9 fps (about 8.74 seconds).
Playback is twice the previous 22.95 fps, with the same 0.1 time step
between frames. The inset occupies the upper right of the velocity axes.
From simulation time t=25 onward, a “soliton” arrow tracks the minimum
of the displayed density at x>0, following both its position and depth.
The arrow targets are recorded in Fig3a_manifest.json.
Source provenance is in source_manifest.json and Fig3a_manifest.json.
The existing Attractive_quench outputs are preserved.

Reproduce using the existing Python scientific packages and GStreamer:

```bash
MPLCONFIGDIR=/tmp/gpe-animation-mpl python prepare_fig3a.py
MPLCONFIGDIR=/tmp/gpe-animation-mpl python animate_fig3a.py
```

Run from the parent directory. Preparation reuses the local density cache
when present. No dependencies were installed and no raw data were modified.
