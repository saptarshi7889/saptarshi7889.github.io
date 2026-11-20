(() => {
  'use strict';
  const C = {
    width: 480, height: 210, scale: 2, center: 210,
    left: 12, right: 468, surfaceY: 90, bottom: 157,
    spacing: 15, rows: 4, rowSpacing: 13, particleRadius: 3,
    radius: 13, impurityY: 108, profileWidth: 29, profileHeight: 27,
    displacement: 27, steadySpeed: 13, excessSpeed: 44, relaxation: 1.7,
    driftSpeed: 11, oscillationSpeed: 45, period: 3, maxFrame: .1, duration: 7,
    pixel: 2, velocityY: 185, forceY: 40, forceLength: 50, arrowScale: .7,
    tubeOpacity: .1, edgeOpacity: .4, labelSize: 12,
    red: '#df5149', redLight: '#ffada0', redShade: '#953631',
    blue: '#365fe9', blueLight: '#9ebaff', blueShade: '#243782'
  };
  const canvas = document.getElementById('case-canvas');
  const button = document.getElementById('case-pause');
  const ctx = canvas.getContext('2d');
  const protocol = canvas.dataset.protocol;
  const sign = canvas.dataset.interaction==='repulsive' ? 1 : -1;
  const style = getComputedStyle(canvas);
  const tube = style.getPropertyValue('--teal').trim();
  const ink = style.getPropertyValue('--ink').trim();
  let playing = !matchMedia('(prefers-reduced-motion: reduce)').matches;
  let time = 0, playback = 0, previous = null;
  function motion(t) {
    if(protocol==='quenched') return {
      x: C.steadySpeed*t+C.excessSpeed*C.relaxation*(1-Math.exp(-t/C.relaxation)),
      v: C.steadySpeed+C.excessSpeed*Math.exp(-t/C.relaxation)
    };
    const omega = 2*Math.PI/C.period;
    return {x:C.driftSpeed*t+C.oscillationSpeed/omega*(1-Math.cos(omega*t)),v:C.driftSpeed+C.oscillationSpeed*Math.sin(omega*t)};
  }
  function surface(x, center) {
    const distance = (x-center)/C.profileWidth;
    return C.surfaceY+sign*C.profileHeight*Math.exp(-distance*distance);
  }
  function displacement(distance) {
    return sign*C.displacement*Math.tanh(distance/C.profileWidth)*Math.exp(-Math.abs(distance)/(C.profileWidth*2));
  }
  function ball(x,y,r,impurity=false) {
    x=Math.round(x); y=Math.round(y);
    ctx.fillStyle=impurity?C.blue:C.red;
    ctx.fillRect(x-r+2,y-r,r*2-4,r*2);
    ctx.fillRect(x-r,y-r+3,r*2,r*2-6 || C.pixel);
    ctx.fillStyle=impurity?C.blueLight:C.redLight;
    ctx.fillRect(x-r+2,y-r+1,Math.max(2,r-3),Math.max(2,r-3));
    ctx.fillStyle=impurity?C.blueShade:C.redShade;
    ctx.fillRect(x+r-3,y-r+3,C.pixel,r*2-5);
  }
  function arrow(x,y,length,label,color) {
    const end=Math.round(x+length), direction=Math.sign(length)||1;
    ctx.fillStyle=color;
    ctx.fillRect(Math.min(x,end),y,Math.max(C.pixel,Math.abs(length)),C.pixel);
    for(let i=0;i<4;i++) ctx.fillRect(end-direction*i,y-i,C.pixel,i*2+C.pixel);
    ctx.font=`${C.labelSize}px monospace`;
    ctx.fillText(label,Math.min(x,end),y-8);
  }
  function render() {
    ctx.setTransform(C.scale,0,0,C.scale,0,0);
    ctx.clearRect(0,0,C.width,C.height);
    const m=motion(time);
    // Track the mean drift, keeping oscillations visible while the bath scrolls.
    const camera=protocol==='quenched'?m.x:C.driftSpeed*time;
    const center=C.center+m.x-camera;
    ctx.fillStyle=tube; ctx.globalAlpha=C.tubeOpacity;
    for(let x=C.left;x<C.right;x+=C.pixel) {
      const y=Math.round(surface(x,center));
      ctx.fillRect(x,y,C.pixel,C.bottom-y);
    }
    ctx.globalAlpha=C.edgeOpacity;
    for(let x=C.left;x<C.right;x+=C.pixel) ctx.fillRect(x,Math.round(surface(x,center)),C.pixel,C.pixel);
    ctx.globalAlpha=1;
    for(let row=0;row<C.rows;row++) {
      for(let base=C.left-camera%C.spacing;base<C.right;base+=C.spacing) {
        const x=base+displacement(base-center);
        const y=surface(x,center)+8+row*C.rowSpacing;
        if(x>C.left && x<C.right && Math.hypot(x-center,y-C.impurityY)>C.radius+C.particleRadius) ball(x,y,C.particleRadius);
      }
    }
    ball(center,C.impurityY,C.radius,true);
    arrow(center,C.velocityY,Math.sign(m.v)*Math.max(5,Math.abs(m.v)*C.arrowScale),'v',ink);
    if(protocol==='driven') arrow(center+8,C.forceY,C.forceLength,'F',C.red);
  }
  function controls() {button.textContent=playing?'Pause animation':'Play animation';}
  button.addEventListener('click',()=>{
    if(playback>=C.duration) playback=0;
    playing=!playing;previous=null;controls();
  });
  function frame(now) {
    if(playing && !document.hidden && previous!==null) {
      const elapsed=Math.min(C.maxFrame,(now-previous)/1000,C.duration-playback);
      time+=elapsed; playback+=elapsed;
      if(playback>=C.duration) {playing=false;controls();}
      render();
    }
    previous=now;requestAnimationFrame(frame);
  }
  controls();render();requestAnimationFrame(frame);
})();
