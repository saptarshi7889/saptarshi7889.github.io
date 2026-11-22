(() => {
  'use strict';
  const S = {
    width: 480, height: 240, sites: 13, left: 32, spacing: 34,
    chainY: 83, spinLength: 32, boxWidth: 26, boxHeight: 42,
    bathY: 170, coupledY: 127, particles: 6, particleSize: 2,
    particleSpeed: 16, turnRate: 2, transitionRate: 5,
    maxStep: 0.05, milliseconds: 1000, snap: 0.001,
    pixel: 2, arrowHead: 6, labelX: 14, titleY: 21, orderY: 42,
    axisX: 12, axisTop: 51, axisBottom: 107, axisLabelY: 47,
    bathLabelY: 229, waveStep: 4, waveOpacity: 0.4,
    background: '#142c35', line: '#54717a', text: '#e0eee5',
    up: '#ffce64', down: '#69c7e2', bath: '#284852',
    bathEdge: '#69c7a6', particle: '#f18b89', coupling: '#d6a8ee'
  };
  const canvas = document.getElementById('spin-canvas');
  const ctx = canvas.getContext('2d');
  const panel = document.getElementById('langevin');
  const field = document.getElementById('spin-field');
  const scene = document.getElementById('spin-scene');
  const motion = document.getElementById('spin-motion');
  const status = document.getElementById('spin-status');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const period = Math.PI * 2;
  let fieldOn = false, coupled = false, blend = 0, coupling = 0;
  let paused = reduced, previous = null, frame = null;
  const particles = Array.from({ length: S.sites }, () =>
    Array.from({ length: S.particles }, () => ({
      x: Math.random() * (S.boxWidth - S.pixel * 2 - S.particleSize),
      y: Math.random() * (S.boxHeight - S.pixel * 2 - S.particleSize),
      angle: Math.random() * period
    })));

  function block(x, y, width, height, color) {
    ctx.fillStyle = color;
    ctx.fillRect(Math.round(x), Math.round(y), Math.round(width), Math.round(height));
  }

  function line(x1, y1, x2, y2, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = S.pixel;
    ctx.beginPath();
    ctx.moveTo(Math.round(x1), Math.round(y1));
    ctx.lineTo(Math.round(x2), Math.round(y2));
    ctx.stroke();
  }

  function spinZ(index) {
    const afm = index % 2 === 0 ? 1 : -1;
    const wave = Math.cos(period * index / (S.sites - 1));
    return afm * (1 - blend) + wave * blend;
  }

  function draw() {
    block(0, 0, S.width, S.height, S.background);
    ctx.font = '10px monospace';
    ctx.fillStyle = S.text;
    ctx.fillText('1D XXZ SPIN CHAIN', S.labelX, S.titleY);
    ctx.fillText(fieldOn ? 'SPIN DENSITY WAVE / ONE PERIOD' : 'ANTIFERROMAGNET / ALTERNATING Z', S.labelX, S.orderY);
    ctx.fillText('+z', S.axisX, S.axisLabelY);
    line(S.axisX, S.axisBottom, S.axisX, S.axisTop, S.line);
    line(S.axisX, S.axisTop, S.axisX - S.pixel, S.axisTop + S.arrowHead, S.line);
    line(S.left, S.chainY, S.left + S.spacing * (S.sites - 1), S.chainY, S.line);
    if (blend > S.snap) {
      ctx.globalAlpha = blend * S.waveOpacity;
      for (let x = 0; x <= S.spacing * (S.sites - 1); x += S.waveStep) {
        const y = S.chainY - S.spinLength * Math.cos(period * x / (S.spacing * (S.sites - 1)));
        block(S.left + x, y, S.pixel, S.pixel, S.up);
      }
      ctx.globalAlpha = 1;
    }
    particles.forEach((bath, index) => {
      const x = S.left + S.spacing * index;
      const y = S.bathY + (S.coupledY - S.bathY) * coupling;
      if (coupling > S.snap) {
        ctx.globalAlpha = coupling;
        line(x, S.chainY + S.spinLength + S.pixel, x, y, S.coupling);
        ctx.globalAlpha = 1;
      }
      block(x - S.boxWidth / 2, y, S.boxWidth, S.boxHeight, S.bathEdge);
      block(x - S.boxWidth / 2 + S.pixel, y + S.pixel,
        S.boxWidth - S.pixel * 2, S.boxHeight - S.pixel * 2, S.bath);
      bath.forEach(p => block(x - S.boxWidth / 2 + S.pixel + p.x,
        y + S.pixel + p.y, S.particleSize, S.particleSize, S.particle));
      const z = spinZ(index);
      const tip = S.chainY - S.spinLength * z;
      const color = z >= 0 ? S.up : S.down;
      line(x, S.chainY, x, tip, color);
      if (Math.abs(z) > S.snap) {
        const head = Math.min(S.arrowHead, Math.abs(S.spinLength * z));
        const direction = z >= 0 ? 1 : -1;
        line(x, tip, x - head, tip + direction * head, color);
        line(x, tip, x + head, tip + direction * head, color);
      }
      block(x - S.pixel, S.chainY - S.pixel, S.pixel * 2, S.pixel * 2, S.text);
    });
    ctx.fillStyle = S.text;
    ctx.fillText(coupled ? 'LOCAL RESERVOIRS / COUPLED' : 'INDEPENDENT LOCAL RESERVOIRS', S.labelX, S.bathLabelY);
  }

  function tick(now) {
    frame = null;
    const dt = previous === null ? 0 : Math.min((now - previous) / S.milliseconds, S.maxStep);
    previous = now;
    const step = reduced ? 1 : Math.min(1, dt * S.transitionRate);
    blend += (Number(fieldOn) - blend) * step;
    coupling += (Number(coupled) - coupling) * step;
    if (Math.abs(Number(fieldOn) - blend) < S.snap) blend = Number(fieldOn);
    if (Math.abs(Number(coupled) - coupling) < S.snap) coupling = Number(coupled);
    if (!paused) particles.forEach(bath => bath.forEach(p => {
      if (Math.random() < dt * S.turnRate) p.angle = Math.random() * period;
      p.x += Math.cos(p.angle) * S.particleSpeed * dt;
      p.y += Math.sin(p.angle) * S.particleSpeed * dt;
      const maxX = S.boxWidth - S.pixel * 2 - S.particleSize;
      const maxY = S.boxHeight - S.pixel * 2 - S.particleSize;
      if (p.x < 0 || p.x > maxX) p.angle = Math.PI - p.angle;
      if (p.y < 0 || p.y > maxY) p.angle = -p.angle;
      p.x = Math.max(0, Math.min(maxX, p.x));
      p.y = Math.max(0, Math.min(maxY, p.y));
    }));
    draw();
    if (!paused || blend !== Number(fieldOn) || coupling !== Number(coupled)) wake();
  }

  function wake() {
    if (frame === null && !panel.hidden && !document.hidden) frame = requestAnimationFrame(tick);
  }

  field.addEventListener('click', () => {
    fieldOn = !fieldOn;
    field.setAttribute('aria-pressed', String(fieldOn));
    document.getElementById('spin-field-state').textContent = fieldOn ? 'ON' : 'OFF';
    document.getElementById('spin-order').textContent = fieldOn
      ? 'Spin density wave · one period of Sᶻ' : 'Antiferromagnet · alternating Sᶻ';
    status.textContent = `${fieldOn ? 'Field on: one period of a spin density wave.' : 'Field off: antiferromagnetic order.'} Reservoirs ${coupled ? 'coupled.' : 'uncoupled; click the animation to couple them.'}`;
    wake();
  });
  scene.addEventListener('click', () => {
    coupled = !coupled;
    scene.setAttribute('aria-pressed', String(coupled));
    scene.setAttribute('aria-label', coupled ? 'Decouple the reservoirs from the spin chain' : 'Couple the independent reservoirs to the spin chain');
    status.textContent = coupled ? 'Each reservoir is coupled to its own spin. Click again to decouple.' : 'Reservoirs uncoupled. Click the animation to couple them.';
    wake();
  });
  function updateMotion() {
    motion.setAttribute('aria-pressed', String(paused));
    motion.textContent = paused ? 'Resume particle motion' : 'Pause particle motion';
  }
  motion.addEventListener('click', () => { paused = !paused; updateMotion(); wake(); });
  function visibilityChanged() {
    if (panel.hidden || document.hidden) {
      if (frame !== null) cancelAnimationFrame(frame);
      frame = null;
    }
    previous = null;
    wake();
  }
  new MutationObserver(visibilityChanged).observe(panel, { attributes: true, attributeFilter: ['hidden'] });
  document.addEventListener('visibilitychange', visibilityChanged);
  updateMotion();
  draw();
  wake();
})();
