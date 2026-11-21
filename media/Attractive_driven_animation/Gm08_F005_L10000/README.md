# Attractive driven impurity: third velocity zero crossing

Recorded impurity velocity and boson density for G = −0.8, F = 0.05,
L = 10000, from the supplied `m0.333/F0.05_L10000` run. The layout,
colors, particle markers, and illustrated immersion opening match `Repulsive_driven_animation/G05_F05_L8500`; playback is twice as fast
(20.8 fps).

- Stop at the third velocity zero crossing **after** the initial rest state:
  t ≈ 623.8154752143. Crossings are found by linear interpolation of the
  recorded velocity. Continuations supersede earlier records from their
  respective restart times onward.
- Use every saved configuration through t = 622.5, plus a final density
  interpolated between the saved configurations at t = 622.5 and t = 625.
  The final animation frame labels that interpolation.
- Density is Re(ψ)² + Im(ψ)² in the impurity frame, sampled every 200
  original grid points over −500 ≤ x < 500: dx = 0.00025 gives a displayed
  spacing of 0.05 and 20000 density samples per frame.
- The uniform bath opening and transition to the first configuration at
  t = 2.5 are illustrations, labeled as such. Subsequent frames show saved
  data, except for the interpolated final frame.

Run `prepare.py`, then `animate.py`, using an existing Python installation
with NumPy, Matplotlib and Pillow, plus GStreamer's PNG and x264 plugins.
No packages are installed by these scripts. `prepare.py` requires the
external source directory defined at its top. It reads only the part of
each compressed file needed to reach x = 500, and caches sampled densities
in `density_cache/` for resuming. The compact `plot_data.npz` is sufficient
to regenerate the animation without the external drive.

`source_manifest.json` records source filenames, zero crossings, restart
handling, and endpoint interpolation. `animation_manifest.json` records
rendering and sampling details. Outputs include MP4, GIF, and PNG previews.
