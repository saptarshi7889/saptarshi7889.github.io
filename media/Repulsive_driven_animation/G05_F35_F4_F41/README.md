# Driven repulsive impurity: F=3.5, 4, 4.1

Run `python media/Repulsive_driven_animation/G05_F35_F4_F41/load_archive.py`
from the repository root, then run `animate.py` at the same path.
Existing NumPy, Matplotlib, Pillow, gzip and GStreamer installations are used.
No dependencies are installed. Original archives are read without modification.

The source directory is
`/run/media/sap/RIdata/Data/Repulsive_impurity_simulation_data/Repulsive_Driven/Diff_G/G0.5`.
Velocity data use dx=1/6000 for F=3.5 and 4, and dx=1/20000 for F=4.1.
The selected runs cover velocity from 0 through 80: dt=0.0025, L=4800 for
F=3.5; dt=0.01, L=1600 for F=4 and F=4.1. Different time steps
and lengths are never combined. Continuations supersede earlier velocity records
from their restart times. Source members and selected grids are recorded in the
animation manifest.

Only F=3.5 density is shown. Every 300th grid point is retained strictly within
(-200,200), giving spacing 0.05. Density is Re(phi)^2 + Im(phi)^2; coordinates
are reconstructed from integer grid indices and checked against saved coordinates.
The density uses the same time step and system length as the F=3.5 velocity.
Every frame uses a saved density configuration, with no interpolation between
configurations. Decorative beads use a further display stride along the density
curve. The coral marker denotes the impurity at x=0.

Violet F=3.5, cyan F=4, and green F=4.1 colors are extracted from the vector
strokes in Fig. 3(b) of https://arxiv.org/pdf/2511.20326.
Outputs: MP4, GIF, initial/final PNG previews, encoding log and source manifest.
Rerunning the renderer replaces generated outputs. Data caches permit rendering
without reading the external drive again. Loading interrupted archives reuses
already saved samples, while scanning the compressed archive from its beginning.

Verified render: 80 saved density frames (t=1,...,80), 7999 points per frame,
801 velocity records per force (t=0,...,80). MP4: 1440 by 960, 15.2 fps, approximately 5.263 s.
GIF: 80 frames, total duration 5.26 s. Playback is 1.9 times the original 8 fps.
GIF delays alternate between 60 and 70 ms to approximate the requested rate. Both exports decoded successfully.
The F=3.5 and F=4 archives were scanned completely. The F=4.1 scan was stopped
after the complete selected velocity run was cached; its other time steps were
not fully inventoried. This does not limit the selected animation data.
