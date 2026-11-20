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
    stageHeight: 190, stageOffset: 60, stageStartY: 42, stageCenter: 160,
    stageTravel: 60, stageArrowY: 180, stageForceY: 82,
    particleColor: '#df5149', particleShade: '#953631', particleLight: '#ffada0',
    impurityColor: '#365fe9', impurityShade: '#243782', impurityLight: '#9ebaff'
  };
  const root = document.getElementById('impurity-chooser');
  const trigger = document.getElementById('impurity-trigger');
  const pipe = document.getElementById('impurity-pipe');
  const protocols = document.getElementById('protocol-options');
  const interactions = document.getElementById('interaction-step');
  const status = document.getElementById('impurity-status');
  const pause = document.getElementById('impurity-pause');
  const replay = document.getElementById('impurity-replay');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const style = getComputedStyle(root);
  const colors = { tube: style.getPropertyValue('--teal').trim(), ink: style.getPropertyValue('--ink').trim() };
  let time = reduced ? SETTINGS.duration : 0;
  let playing = !reduced;
  let previous = null;
  let dropped = false, stageTime = 0, selectedProtocol = 'quenched';
  let awaitingDrop = false, previewProtocol = null, previewInteraction = null;

  function drawStage() {
    const ctx = pipe.getContext('2d');
    const fall = reduced ? 1 : Math.min(1,stageTime/SETTINGS.dropTime);
    const movingTime = Math.max(0,stageTime-SETTINGS.dropTime);
    const protocol = previewProtocol || selectedProtocol;
    const m = motion(protocol,movingTime);
    const travel = dropped ? m.x-SETTINGS.startX : 0;
    const camera = protocol==='driven' ? SETTINGS.driftSpeed*movingTime : Math.max(0,travel-SETTINGS.stageTravel);
    const x = SETTINGS.stageCenter+travel-camera;
    const y = dropped ? SETTINGS.stageStartY+(SETTINGS.tubeY+SETTINGS.stageOffset-SETTINGS.stageStartY)*fall*fall : SETTINGS.stageStartY;
    ctx.setTransform(SETTINGS.scale,0,0,SETTINGS.scale,0,0);
    ctx.clearRect(0,0,SETTINGS.width,SETTINGS.stageHeight);
    const interaction = previewInteraction;
    const direction = interaction==='repulsive' ? 1 : interaction==='attractive' ? -1 : 0;
    const surfaceY = bx => SETTINGS.tubeTop+SETTINGS.stageOffset+direction*SETTINGS.dipHeight*Math.exp(-(((bx-x)/SETTINGS.profileWidth)**2));
    ctx.fillStyle=colors.tube; ctx.globalAlpha=SETTINGS.tubeOpacity;
    for(let bx=SETTINGS.left;bx<SETTINGS.right;bx+=SETTINGS.pixelStep) {
      const top=surfaceY(bx);
      ctx.fillRect(bx,top,SETTINGS.pixelStep,SETTINGS.tubeBottom+SETTINGS.stageOffset-top);
    }
    ctx.globalAlpha=SETTINGS.edgeOpacity;
    for(let bx=SETTINGS.left;bx<SETTINGS.right;bx+=SETTINGS.pixelStep) ctx.fillRect(bx,surfaceY(bx),SETTINGS.pixelStep,SETTINGS.pixelStep);
    ctx.globalAlpha=1;
    for(let row=0;row<SETTINGS.particleRows;row++) {
      for(let bx=SETTINGS.left-camera%SETTINGS.spacing;bx<SETTINGS.right;bx+=SETTINGS.spacing) {
        const distance=bx-x;
        const shifted=bx+direction*SETTINGS.displacement*Math.tanh(distance/SETTINGS.profileWidth)*Math.exp(-Math.abs(distance)/(SETTINGS.profileWidth*2));
        const py=surfaceY(shifted)+8+row*SETTINGS.rowSpacing;
        if(shifted>20 && shifted<SETTINGS.right && (!dropped || fall<1 || Math.hypot(shifted-x,py-y)>25)) ball(ctx,shifted,py,SETTINGS.particleRadius);
      }
    }
    trigger.style.left=`${x/SETTINGS.width*100}%`;
    trigger.style.top=`${y/SETTINGS.stageHeight*100}%`;
    if(dropped && fall>=1) {
      arrow(ctx,x,SETTINGS.stageArrowY,Math.sign(m.v)*Math.max(5,Math.abs(m.v)*SETTINGS.arrowScale),'v',colors.ink);
      if(protocol==='driven') arrow(ctx,x+7,SETTINGS.stageForceY,SETTINGS.forceLength,'F',SETTINGS.particleColor);
    }
  }

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
  function render() { drawStage(); }
  function controls() { pause.textContent = playing ? 'Pause animations' : 'Play animations'; }
  function restart() {
    time = reduced ? SETTINGS.duration : 0;
    playing = !reduced; previous = null; controls(); render();
  }
  function openProtocols() {
    if(!protocols.hidden) return;
    protocols.hidden = false; trigger.setAttribute('aria-expanded','true'); restart();
  }
  trigger.addEventListener('click',()=>{
    if(!dropped) {
      dropped=true; stageTime=reduced?SETTINGS.dropTime:0; awaitingDrop=true;
      status.textContent='Dropping into the Bose gas…';
      restart();
    } else if(!awaitingDrop) openProtocols();
    if(awaitingDrop && reduced) {awaitingDrop=false;openProtocols();}
  });
  root.addEventListener('keydown',event=>{
    if(event.key==='Escape') {protocols.hidden=true; trigger.setAttribute('aria-expanded','false'); trigger.focus();}
  });
  for(const option of root.querySelectorAll('[data-protocol]')) {
    function preview() {previewProtocol=option.dataset.protocol;stageTime=SETTINGS.dropTime;render();}
    function clearPreview() {previewProtocol=null;render();}
    option.addEventListener('pointerenter',preview);
    option.addEventListener('focus',preview);
    option.addEventListener('pointerleave',clearPreview);
    option.addEventListener('blur',clearPreview);
    option.addEventListener('click',()=>{
      const protocol = option.dataset.protocol;
      selectedProtocol=protocol;
      previewProtocol=null; previewInteraction=null;
      stageTime=SETTINGS.dropTime;
      protocols.hidden=true; trigger.setAttribute('aria-expanded','false');
      interactions.hidden=false;
      status.textContent = `${protocol==='quenched' ? 'Quenched' : 'Driven'} selected. Choose Repulsive or Attractive.`;
      restart();
      interactions.querySelector('button').focus();
    });
  }
  for(const option of root.querySelectorAll('[data-interaction]')) {
    const preview=()=>{previewInteraction=option.dataset.interaction;render();};
    const clear=()=>{previewInteraction=null;render();};
    option.addEventListener('pointerenter',preview);
    option.addEventListener('focus',preview);
    option.addEventListener('pointerleave',clear);
    option.addEventListener('blur',clear);
    option.addEventListener('click',()=>{
      const interaction=option.dataset.interaction;
      window.location.assign(`${selectedProtocol}${interaction==='attractive' ? '-attractive' : ''}.html#${interaction}`);
    });
  }
  pause.addEventListener('click',()=>{
    if(time>=SETTINGS.duration) time=0;
    playing=!playing; previous=null; controls(); render();
  });
  replay.addEventListener('click',()=>{time=0; stageTime=0; playing=true; previous=null; controls(); render();});
  function frame(now) {
    if(playing && !document.hidden && previous!==null) {
      const elapsed=Math.min(SETTINGS.maxFrame,(now-previous)/1000);
      time=Math.min(SETTINGS.duration,time+elapsed);
      if(dropped) stageTime+=elapsed;
      if(awaitingDrop && stageTime>=SETTINGS.dropTime) {
        awaitingDrop=false; openProtocols();
        status.textContent='Quenched or Driven? Hover to preview, click to choose.';
      }
      render();
    }
    previous=now; requestAnimationFrame(frame);
  }
  root.hidden=false;
  document.getElementById('protocol-fallback').hidden=true;
  controls(); render(); requestAnimationFrame(frame);
})();
