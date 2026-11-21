# Attractive driven impurity: G = −0.8, M = 8m, F = 0.03

Velocity history and boson density in the impurity frame, using the same
visual style and 20.8 fps playback as the shortened M = 3m, F = 0.05
animation in `../Gm08_F005_L10000`.

- Source: the supplied `G-0.8/m0.125/F0.03.tar.gz` archive.
- Grid: dx = 0.00025, dt = 0.01, L = 4200. Every configuration is checked
  against this grid before combining it with the others.
- Density: Re(ψ)² + Im(ψ)², every 200 original grid points over
  −500 ≤ x < 500, giving 20000 samples at spacing 0.05.
- Endpoint: third velocity zero crossing after t = 0, matching the endpoint
  convention of the latest animation (return to zero during the second
  oscillation). Logged velocity is linearly interpolated at the crossing;
  final density is interpolated between the two bracketing configurations
  and explicitly labeled.
- Continuations supersede earlier velocity records from their respective
  restart times onward.
- The uniform bath immersion opening and transition to the first saved
  configuration are illustrative and labeled as such.

Run `prepare.py`, then `animate.py`, using an existing Python installation
with NumPy, Matplotlib and Pillow, plus GStreamer's PNG and x264 plugins.
No dependencies are installed by these scripts.

The source archive is streamed without extracting full configurations.
Ignored `density_cache/` and `velocity_cache/` folders retain compact sampled
data. `archive_manifest.json` marks a completed archive scan; subsequent
preparation uses these caches without rereading the archive. The final
`plot_data.npz` is sufficient to rerender without the external drive.
`source_manifest.json` records filenames, zero crossings, the precise
endpoint, restart handling, and interpolation. `animation_manifest.json`
records frame times, playback speed, and rendering details.

Verified endpoint: t = 1064.522797194, interpolated between saved densities
at t = 1062.5 and 1065. The animation uses 426 density frames plus 15
illustrative opening frames (441 total), lasting 21.2019 seconds at 20.8 fps.
