# Attractive driven impurity: G=-0.8, M=3m, F=0.8 and 1

Source root:
`/run/media/sap/Seagate/Attractive_impurity_raw_data/Codes/Impurity_Thomas_Data/Delta_Impurity_optimum/Attractive_impurity/Attractive_driven/G-0.8/m0.333`.
F=0.8 uses dt=0.0025, dx=1/6000, L=3600. The requested F=1 dt=0.0025
archive has velocity records for 0..34 and 64..115, with its first continuation
missing. The user authorized another dx or dt when that data was unavailable.
The F=1 fallback uses dt=0.01, dx=1/8000, L=2400 from F1.tar.gz, keeping
the entire F=1 curve on one grid and time step. The finer dx=1/12000, dt=0.01
run in that archive ends at t=47.9, so it does not cover the requested interval. The dimensionless boson coupling is gamma=0.1.

Run the scripts in this directory using the existing NumPy, Matplotlib and
Pillow installation, plus system gzip and GStreamer. No packages are installed.
`load_data.py` reads complex fields for F=0.8 from individual compressed files
and F=1 velocities from the authorized fallback archive F1.tar.gz. Original files are not changed.
`check_phase.py` checks the selected phase snapshots with denser samples.
`animate.py` renders the sampled fields, velocities and three fixed phase panels.

The requested interval is t<=65. Density is Re(phi)^2+Im(phi)^2 in the impurity
frame, using every 300th point strictly within (-200,200). The plotted spacing
is 0.05, with 7999 points per frame. There are saved fields at every integer
time from 1 through 65. No density interpolation is used. Cached complex fields
allow both density and phase plots to be reproduced without rereading the drive.
Velocity continuations supersede earlier records from their restart time onward;
the renderer checks for gaps rather than joining missing intervals.

The phase convention is Theta(x,t)=Arg[phi(x,t) exp(i t-i pi/2)] in [-pi,pi).
The factor exp(i t) removes the uniform bath rotation, and the constant -pi/2
sets the same background phase as Fig. 3 of the paper. Three fixed snapshots
at t=15,39,63 show one, two and three downward wrapped 2pi discontinuities.
These are branch jumps in a wrapped plot, not evidence of a new zero of the
complex field at every displayed vertical line. The unwrapped phase change
across this finite window is approximately 2pi,4pi,6pi at those times.

The denser checks use every 30th point (spacing 0.005); all three counts agree.
Their unwrapped phase turns are 1.000266, 2.000406 and 2.999556. The maximum
adjacent phase increments are 0.6481, 0.3890 and 0.2381 rad, respectively.
`phase_checks.json` records these checks. Over the full sequence, the rounded
unwrapped turn count increases in t intervals (14,15), (38,39) and (62,63).
Positive-to-negative impurity velocity crossings occur at t approximately
16.2935, 40.2005 and 64.0705, consistent with one added turn per oscillation
slightly before that velocity crossing. See `cycle_phase_checks.json`.

The times, phase convention and velocity colors follow Figs. 2 and 3 of
Majumdar and Petkovic, *Driven dynamics of an attractive Bose polaron*,
https://arxiv.org/abs/2606.13645. The violet curve is F=0.8; the amber curve is F=1.
The fixed phase panels are reference snapshots and do not follow the movie clock.
`phase_snapshots.png` and `phase_snapshots.pdf` provide a larger static view.

Verified exports: 65 saved density frames, 651 velocity records per force,
1680 by 1080 H.264 MP4 at 15.2 fps (65/15.2 = 4.276316 s). The GIF has
65 frames and 4.28 s total duration, using 60/70 ms delays. Both exports were
fully decoded. Playback matches the preceding repulsive force-comparison
animation. The website includes this recording as its second attractive-driven
regime tab, labelled Strong force. Publication requires the user’s commit
and push through the existing GitHub Pages workflow.

## Cylindrical phase display

The animation stacks the same three phase snapshots vertically as cylinders,
following Fig. 2(a) of https://arxiv.org/pdf/2412.04355v1. Position x/xi is the
vertical cylinder axis, and phase Theta is its polar angle. Front-facing curve
segments are solid; rear-facing segments are dashed. The phase data and gauge
are unchanged. A 2pi branch jump joins continuously on the cylinder; the three
profiles therefore show approximately one, two and three phase turns across
the displayed spatial interval. These are not winding numbers of a closed
spatial ring: the shown interval is only a window within the full simulation.

For drawing, the unwrapped angle is linearly interpolated between retained
samples so successive angular steps are at most pi/32. This keeps the curve
on the cylinder surface rather than drawing chords across its interior; it
does not add simulation data. The static PNG/PDF use the same cylindrical
profiles in three columns, with their density profiles underneath.

The cylinder camera is rotated by pi/2 to place the background phase near
-pi/2 on the front surface, where small phase variations have maximal lateral
visibility. This is a viewing rotation, not a change in the phase gauge or
amplitude. Phase windows are (-50,50), (-100,100) and (-150,150) at t=15,39,63.
They retain one, two and three wrapped drops, with approximately 0.99826,
1.99867 and 3.00359 unwrapped turns across the cropped intervals. The animation
density panel still covers (-200,200); only the three phase cylinders are
zoomed. The static figure density panels use the corresponding phase windows.
Thinner curves, wider cylinders and a lighter mesh expose the small ripples.
