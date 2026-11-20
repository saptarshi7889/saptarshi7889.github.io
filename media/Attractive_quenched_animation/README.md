# Attractive quench animation

Single velocity history for G=-0.8, mass parameter 0.125 (M=8m), V0/v=2,
through t=75. Rendering follows the neighboring quantum-flutter animation.
Two density panels sit above a separate, unobstructed velocity axis.
The wide density view spans [-50,50] and uses every 5000th source grid point;
the close-up spans [-15,15] and uses every 2500th point. At dx=0.0001,
these spacings are 0.5 and 0.25. Density is Re(psi)^2+Im(psi)^2.
Coordinates are reconstructed from grid indices and checked against source
coordinates. The shaded impurity stays at x=0 in the impurity frame.

All 124 available configurations are used: integer times 1–26, then half-unit
times through 75. Playback uses 12.75 frames per second (1.7 times the previous 7.5 fps speed);
thus physical time advances more slowly after t=26. The opening uniform bath
and smooth transition to the first saved configuration are labelled illustrative.
Velocity restart files supersede earlier files from their start time onward.
There is no velocity segment between t=65.7 and 73.5 in the supplied folder:
this interval is filled using the brown vector curve in Fig. 2.1, printed page
135 (PDF page 136) of Impurity_corrected-1.pdf. Only the 77 missing interior
samples are inserted; original raw samples and endpoints are preserved.
The recovered coordinates have plotting precision, not simulation precision.
Overlap RMS error is 0.00054; maximum error is 0.00216 in velocity units.
See velocity_bridge_validation.png and velocity_bridge.csv.
Source paths and that gap are recorded in source_manifest.json.

Using the existing NumPy, Matplotlib, Pillow and GStreamer installation:

```bash
python prepare_attractive.py
MPLCONFIGDIR=/tmp/gpe-animation-mpl python extract_velocity_bridge.py
MPLCONFIGDIR=/tmp/gpe-animation-mpl python animate_attractive.py
```

Preparation reads the external drive and caches small sampled arrays in
`density_cache/` and `plot_data.npz`. Rerunning the renderer needs only these
local caches and source_manifest.json. Raw files are never modified.
Outputs: Attractive_quench.mp4, .gif, intro/final PNGs, manifest and encoding log.
