(() => {
  'use strict';
  const S = {
    width: 480, height: 240, sites: 13, left: 32, spacing: 34,
    chainY: 83, spinLength: 32, boxWidth: 26, boxHeight: 42,
    bathY: 170, coupledY: 127, particles: 6, particleSize: 2,
    particleSpeed: 16, turnRate: 2, transitionRate: 5,
    maxStep: 0.05, milliseconds: 1000, snap: 0.001,
    resolution: 3, fontSize: 12, spinTurnRate: 0.8, spinSpeed: 1.4,
    depthTilt: 0.35, depthShade: 0.35, pixel: 1, arrowHead: 5, titleY: 21, orderY: 42,
    axisX: 12, axisTop: 51, axisBottom: 107, axisLabelY: 47,
    bathLabelY: 229, waveStep: 4, waveOpacity: 0.4,
    background: '#142c35', line: '#54717a', text: '#e0eee5',
    up: '#ffce64', down: '#69c7e2', bath: '#284852',
    bathEdge: '#69c7a6', particle: '#f18b89', coupling: '#d6a8ee'
  };
  const canvas = document.getElementById('spin-canvas');
  canvas.width = S.width * S.resolution;
  canvas.height = S.height * S.resolution;
  const ctx = canvas.getContext('2d');
  ctx.scale(S.resolution, S.resolution);
  const panel = document.getElementById('langevin');
  const field = document.getElementById('spin-field');
  const couplingButton = document.getElementById('spin-coupling');
  const bathButton = document.getElementById('spin-bath');
  const motion = document.getElementById('spin-motion');
  const status = document.getElementById('spin-status');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const period = Math.PI * 2;
  const parameters = new URLSearchParams(window.location.search);
  const study = parameters.get('study');
  let fieldOn = study === 'ohmic' || study === 'subohmic';
  let subohmic = study === 'subohmic';
  let coupled = false, blend = Number(fieldOn), coupling = 0;
  let paused = reduced, previous = null, frame = null;
  function randomDirection() {
    const z = Math.random() * 2 - 1;
    const angle = Math.random() * period;
    const radius = Math.sqrt(1 - z * z);
    return { x: radius * Math.cos(angle), y: radius * Math.sin(angle), z };
  }
  const spins = Array.from({ length: S.sites }, () => ({
    direction: randomDirection(), axis: randomDirection()
  }));
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
    ctx.font = `${S.fontSize}px monospace`;
    ctx.fillStyle = S.text;
    ctx.textAlign = 'center';
    ctx.fillText('1D XXZ SPIN CHAIN', S.width / 2, S.titleY);
    ctx.fillText(!coupled ? 'FREE SPINS / RANDOM 3D ROTATION' : fieldOn ? 'SPIN DENSITY WAVE' : 'ANTIFERROMAGNET / ALTERNATING Z', S.width / 2, S.orderY);
    ctx.fillText('+z', S.axisX, S.axisLabelY);
    line(S.axisX, S.axisBottom, S.axisX, S.axisTop, S.line);
    line(S.axisX, S.axisTop, S.axisX - S.pixel, S.axisTop + S.arrowHead, S.line);
    line(S.left, S.chainY, S.left + S.spacing * (S.sites - 1), S.chainY, S.line);
    if (blend * coupling > S.snap) {
      ctx.globalAlpha = blend * coupling * S.waveOpacity;
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
      const free = spins[index].direction;
      const freeWeight = 1 - coupling;
      const projectedX = free.x * Math.cos(S.depthTilt) - free.y * Math.sin(S.depthTilt);
      const projectedDepth = free.x * Math.sin(S.depthTilt) + free.y * Math.cos(S.depthTilt);
      const z = free.z * freeWeight + spinZ(index) * coupling;
      const dx = S.spinLength * projectedX * freeWeight;
      const dy = -S.spinLength * z;
      const length = Math.hypot(dx, dy);
      const tipX = x + dx;
      const tipY = S.chainY + dy;
      const color = z >= 0 ? S.up : S.down;
      ctx.globalAlpha = 1 - S.depthShade * freeWeight * (1 - projectedDepth) / 2;
      line(x, S.chainY, tipX, tipY, color);
      if (length > S.snap) {
        const head = Math.min(S.arrowHead, length);
        const ux = dx / length, uy = dy / length;
        line(tipX, tipY, tipX - head * (ux + uy), tipY - head * (uy - ux), color);
        line(tipX, tipY, tipX - head * (ux - uy), tipY - head * (uy + ux), color);
      }
      ctx.globalAlpha = 1;
      block(x - S.pixel, S.chainY - S.pixel, S.pixel * 2, S.pixel * 2, S.text);
    });
    ctx.fillStyle = S.text;
    ctx.fillText(coupled ? 'LOCAL RESERVOIRS / COUPLED' : 'INDEPENDENT LOCAL RESERVOIRS', S.width / 2, S.bathLabelY);
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
    if (!paused && coupling < 1) spins.forEach(spin => {
      if (Math.random() < dt * S.spinTurnRate) spin.axis = randomDirection();
      const a = spin.axis, v = spin.direction;
      const angle = dt * S.spinSpeed;
      const c = Math.cos(angle), t = Math.sin(angle), dot = a.x * v.x + a.y * v.y + a.z * v.z;
      // Rodrigues rotation preserves unit length on the three-dimensional sphere.
      spin.direction = {
        x: v.x * c + (a.y * v.z - a.z * v.y) * t + a.x * dot * (1 - c),
        y: v.y * c + (a.z * v.x - a.x * v.z) * t + a.y * dot * (1 - c),
        z: v.z * c + (a.x * v.y - a.y * v.x) * t + a.z * dot * (1 - c)
      };
    });
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

  function navigateToResults() {
    if (!coupled) return;
    const destination = !fieldOn ? 'langevin-antiferromagnet.html'
      : subohmic ? 'langevin-subohmic.html' : 'langevin-ohmic.html';
    window.location.assign(destination);
  }

  field.addEventListener('click', () => {
    fieldOn = !fieldOn;
    updateOrder();
    wake();
    navigateToResults();
  });
  bathButton.addEventListener('click', () => {
    subohmic = !subohmic;
    updateOrder();
    navigateToResults();
  });
  couplingButton.addEventListener('click', () => {
    coupled = !coupled;
    updateOrder();
    wake();
    navigateToResults();
  });
  function updateOrder() {
    field.setAttribute('aria-pressed', String(fieldOn));
    couplingButton.setAttribute('aria-pressed', String(coupled));
    bathButton.setAttribute('aria-pressed', String(subohmic));
    document.getElementById('spin-field-state').textContent = fieldOn ? 'ON' : 'OFF';
    document.getElementById('spin-coupling-state').textContent = coupled ? 'ON' : 'OFF';
    document.getElementById('spin-bath-state').textContent = subohmic ? 'Subohmic' : 'Ohmic';
    document.getElementById('spin-order').textContent = !coupled
      ? 'Uncoupled · freely rotating 3D spins'
      : fieldOn ? 'Spin density wave · Sᶻ' : 'Antiferromagnet · alternating Sᶻ';
    status.textContent = !coupled
      ? 'Choose the field and bath type, then turn on bath-chain coupling to explore the results.'
      : 'Opening the results for the selected configuration.';
  }
  function updateMotion() {
    motion.setAttribute('aria-pressed', String(paused));
    motion.textContent = paused ? 'Resume motion' : 'Pause motion';
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
  updateOrder();
  updateMotion();
  draw();
  wake();
})();
