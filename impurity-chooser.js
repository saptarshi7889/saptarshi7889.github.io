(() => {
  'use strict';
  const SETTINGS = {
    width: 320, height: 140, scale: 2, duration: 12, maxFrame: .1,
    tubeY: 75, tubeTop: 52, tubeBottom: 98, left: 12, right: 308,
    spacing: 15, radius: 12, particleRadius: 3, startX: 52,
    steadySpeed: 13, excessSpeed: 44, relaxation: 1.7,
    driftSpeed: 11, oscillationSpeed: 45, period: 3, cameraLimit: 230,
    dropTime: 1.3, responseTime: 2, dropStart: 16, dropEnd: 66,
    center: 160, dipHeight: 23, peakHeight: 23, profileWidth: 25,
    displacement: 24, particleRows: 3, rowSpacing: 11,
    pixelStep: 2, arrowScale: .65, forceLength: 42,
    tubeOpacity: .1, edgeOpacity: .3,
    particleColor: '#df5149', particleShade: '#953631', particleLight: '#ffada0',
    impurityColor: '#365fe9', impurityShade: '#243782', impurityLight: '#9ebaff'
  };
  const root = document.getElementById('impurity-chooser');
  const trigger = document.getElementById('impurity-trigger');
  const protocols = document.getElementById('protocol-options');
  const interactions = document.getElementById('interaction-step');
  const status = document.getElementById('impurity-status');
  const pause = document.getElementById('impurity-pause');
  const replay = document.getElementById('impurity-replay');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const scenes = Array.from(root.querySelectorAll('canvas'), canvas => ({canvas, mode: canvas.dataset.motion}));
  const style = getComputedStyle(root);
  const colors = { tube: style.getPropertyValue('--teal').trim(), ink: style.getPropertyValue('--ink').trim() };
  let time = reduced ? SETTINGS.duration : 0;
  let playing = !reduced;
  let previous = null;

  function motion(mode, t) {
    if (mode === 'quenched') return {
      x: SETTINGS.startX + SETTINGS.steadySpeed*t + SETTINGS.excessSpeed*SETTINGS.relaxation*(1-Math.exp(-t/SETTINGS.relaxation)),
      v: SETTINGS.steadySpeed + SETTINGS.excessSpeed*Math.exp(-t/SETTINGS.relaxation)
    };
    const omega = 2*Math.PI/SETTINGS.period;
    return {x: SETTINGS.startX+SETTINGS.driftSpeed*t+SETTINGS.oscillationSpeed/omega*(1-Math.cos(omega*t)), v: SETTINGS.driftSpeed+SETTINGS.oscillationSpeed*Math.sin(omega*t)};
  }
  function ball(ctx, x, y, radius, impurity = false) {
    x = Math.round(x); y = Math.round(y);
    ctx.fillStyle = impurity ? SETTINGS.impurityColor : SETTINGS.particleColor;
    ctx.fillRect(x-radius+2,y-radius,radius*2-4,radius*2);
    ctx.fillRect(x-radius,y-radius+3,radius*2,radius*2-6 || 2);
    ctx.fillStyle = impurity ? SETTINGS.impurityLight : SETTINGS.particleLight;
    ctx.fillRect(x-radius+2,y-radius+1,Math.max(2,radius-3),Math.max(2,radius-3));
    ctx.fillStyle = impurity ? SETTINGS.impurityShade : SETTINGS.particleShade;
    ctx.fillRect(x+radius-3,y-radius+3,2,radius*2-5);
  }
  function arrow(ctx, x, y, length, label, color) {
    const end = Math.round(x+length), direction = Math.sign(length) || 1;
    ctx.fillStyle = color;
    ctx.fillRect(Math.min(x,end),y,Math.max(2,Math.abs(length)),2);
    for(let i=0;i<4;i++) ctx.fillRect(end-direction*i,y-i,2,i*2+2);
    ctx.font = '10px monospace'; ctx.fillText(label,Math.min(x,end),y-6);
  }
  function tube(ctx) {
    ctx.fillStyle = colors.tube; ctx.globalAlpha = SETTINGS.tubeOpacity;
    ctx.fillRect(SETTINGS.left,SETTINGS.tubeTop,SETTINGS.right-SETTINGS.left,SETTINGS.tubeBottom-SETTINGS.tubeTop);
    ctx.globalAlpha = SETTINGS.edgeOpacity;
    for(const y of [SETTINGS.tubeTop,SETTINGS.tubeBottom]) ctx.fillRect(SETTINGS.left,y,SETTINGS.right-SETTINGS.left,2);
    ctx.globalAlpha = 1;
  }
  function drawMotion(ctx, mode) {
    tube(ctx);
    const m = motion(mode,time), camera = Math.max(0,m.x-SETTINGS.cameraLimit), x = Math.round(m.x-camera);
    for(let bx=SETTINGS.left-camera%SETTINGS.spacing; bx<SETTINGS.right; bx+=SETTINGS.spacing) {
      if(bx>20 && Math.abs(bx-x)>18) ball(ctx,bx,SETTINGS.tubeY,SETTINGS.particleRadius);
    }
    ball(ctx,x,SETTINGS.tubeY,SETTINGS.radius,true);
    arrow(ctx,x,114,Math.sign(m.v)*Math.max(5,Math.abs(m.v)*SETTINGS.arrowScale),'v',colors.ink);
    if(mode==='driven') arrow(ctx,x+7,34,SETTINGS.forceLength,'F',SETTINGS.particleColor);
  }
  function response(t) {
    return 1-Math.exp(-Math.max(0,t-SETTINGS.dropTime)/SETTINGS.responseTime);
  }
  function surface(x, mode, amount) {
    const distance = (x-SETTINGS.center)/SETTINGS.profileWidth;
    const sign = mode==='repulsive' ? 1 : -1;
    return SETTINGS.tubeTop+sign*SETTINGS.dipHeight*amount*Math.exp(-distance*distance);
  }
  function drawInteraction(ctx, mode) {
    const amount = response(time), direction = mode==='repulsive' ? 1 : -1;
    // A surface cross-section illustrates depletion or accumulation, not a GPE solution.
    ctx.fillStyle = colors.tube; ctx.globalAlpha = SETTINGS.tubeOpacity;
    for(let x=SETTINGS.left;x<SETTINGS.right;x+=SETTINGS.pixelStep) {
      const y = Math.round(surface(x,mode,amount));
      ctx.fillRect(x,y,SETTINGS.pixelStep,SETTINGS.tubeBottom-y);
    }
    ctx.globalAlpha = SETTINGS.edgeOpacity;
    for(let x=SETTINGS.left;x<SETTINGS.right;x+=SETTINGS.pixelStep) ctx.fillRect(x,Math.round(surface(x,mode,amount)),SETTINGS.pixelStep,2);
    ctx.globalAlpha = 1;
    for(let row=0;row<SETTINGS.particleRows;row++) {
      for(let initial=23;initial<SETTINGS.right;initial+=SETTINGS.spacing) {
        const distance = initial-SETTINGS.center;
        const displacement = direction*SETTINGS.displacement*amount*Math.tanh(distance/SETTINGS.profileWidth)*Math.exp(-Math.abs(distance)/(SETTINGS.profileWidth*2));
        const x = initial+displacement;
        const y = surface(x,mode,amount)+8+row*SETTINGS.rowSpacing;
        if(Math.hypot(x-SETTINGS.center,y-SETTINGS.dropEnd)>SETTINGS.radius+3) ball(ctx,x,y,SETTINGS.particleRadius);
      }
    }
    const drop = Math.min(1,time/SETTINGS.dropTime);
    const y = SETTINGS.dropStart+(SETTINGS.dropEnd-SETTINGS.dropStart)*drop*drop;
    ball(ctx,SETTINGS.center,y,SETTINGS.radius,true);
  }
  function render() {
    for(const scene of scenes) {
      const isProtocol = scene.mode==='quenched' || scene.mode==='driven';
      if(isProtocol ? protocols.hidden : interactions.hidden) continue;
      const ctx = scene.canvas.getContext('2d');
      ctx.setTransform(SETTINGS.scale,0,0,SETTINGS.scale,0,0);
      ctx.clearRect(0,0,SETTINGS.width,SETTINGS.height);
      if(isProtocol) drawMotion(ctx,scene.mode); else drawInteraction(ctx,scene.mode);
    }
  }
  function controls() { pause.textContent = playing ? 'Pause animations' : 'Play animations'; }
  function restart() {
    time = reduced ? SETTINGS.duration : 0;
    playing = !reduced; previous = null; controls(); render();
  }
  function openProtocols() {
    if(!protocols.hidden) return;
    protocols.hidden = false; trigger.setAttribute('aria-expanded','true'); restart();
  }
  trigger.addEventListener('pointerenter',event=>{if(event.pointerType==='mouse') openProtocols();});
  trigger.addEventListener('click',openProtocols);
  root.addEventListener('keydown',event=>{
    if(event.key==='Escape') {protocols.hidden=true; trigger.setAttribute('aria-expanded','false'); trigger.focus();}
  });
  for(const option of root.querySelectorAll('[data-protocol]')) {
    option.addEventListener('click',()=>{
      const protocol = option.dataset.protocol;
      trigger.classList.add('is-chosen');
      trigger.textContent = `Impurity · ${protocol==='quenched' ? 'Quenched' : 'Driven'}`;
      protocols.hidden=true; trigger.setAttribute('aria-expanded','false');
      interactions.hidden=false;
      for(const link of root.querySelectorAll('[data-interaction]')) link.href=`${protocol}.html#${link.dataset.interaction}`;
      status.textContent = `${protocol==='quenched' ? 'Quenched' : 'Driven'} selected. Choose Repulsive or Attractive.`;
      restart();
      interactions.querySelector('a').focus();
    });
  }
  pause.addEventListener('click',()=>{
    if(time>=SETTINGS.duration) time=0;
    playing=!playing; previous=null; controls(); render();
  });
  replay.addEventListener('click',()=>{time=0; playing=true; previous=null; controls(); render();});
  function frame(now) {
    if(playing && !document.hidden && previous!==null) {
      time=Math.min(SETTINGS.duration,time+Math.min(SETTINGS.maxFrame,(now-previous)/1000));
      if(time>=SETTINGS.duration) {playing=false; controls();}
      render();
    }
    previous=now; requestAnimationFrame(frame);
  }
  root.hidden=false;
  document.getElementById('protocol-fallback').hidden=true;
  controls(); requestAnimationFrame(frame);
})();
