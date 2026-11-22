(() => {
  'use strict';
  const S = {
    width: 480, height: 240, sites: 13, left: 32, spacing: 34,
    chainY: 83, spinLength: 32, boxWidth: 26, boxHeight: 42,
    bathY: 170, coupledY: 127, particles: 6, particleSize: 2,
    particleSpeed: 16, turnRate: 2, transitionRate: 5,
    maxStep: 0.05, milliseconds: 1000, snap: 0.001,
    strengthMin: 0, strengthMax: 100, strengthInitial: 25, strengthCritical: 50,
    resolution: 3, fontSize: 12, spinTurnRate: 0.8, spinSpeed: 1.4,
    depthTilt: 0.35, depthShade: 0.35, pixel: 1, arrowHead: 5, titleY: 21, orderY: 42,
    axisX: 12, axisTop: 51, axisBottom: 107, axisLabelY: 47,
    bathLabelY: 229, waveStep: 4, waveOpacity: 0.4,
    background: '#142c35', line: '#54717a', text: '#e0eee5',
    up: '#ffce64', down: '#69c7e2', bath: '#284852',
    bathEdge: '#69c7a6', particle: '#f18b89', coupling: '#d6a8ee'
  };
  const R = {
    height: 210, top: 51, bottom: 155, spectrumLeft: 34, spectrumRight: 210,
    timeLeft: 275, timeRight: 452, titleY: 19, chartTitleY: 39,
    axisLabelY: 174, footerY: 197, samples: 90, frequencyMax: 3,
    timeWindow: 10, timeScale: 2.5, ballisticSlope: 0.35,
    ohmicDc: 0.4, ohmicRate: 1.2, subohmicExponent: 0.5,
    afmDamping: 0.8, afmFrequency: 2, currentSpeed: 45, ballisticSpeed: 42, ohmicOpacity: 0.9,
    currentHead: 4, currentThreshold: 0.005, markerSize: 4, subohmicArrowDuration: 3,
    currentColor: '#efa3ef', gradientColor: '#c2a5ef'
  };
  const canvas = document.getElementById('spin-canvas');
  canvas.width = S.width * S.resolution;
  canvas.height = S.height * S.resolution;
  const ctx = canvas.getContext('2d');
  ctx.scale(S.resolution, S.resolution);
  const responseCanvas = document.getElementById('spin-response');
  responseCanvas.width = S.width * S.resolution;
  responseCanvas.height = R.height * S.resolution;
  const responseCtx = responseCanvas.getContext('2d');
  responseCtx.scale(S.resolution, S.resolution);
  const probe = document.getElementById('spin-probe');
  const responsePanel = document.getElementById('spin-response-panel');
  const responseStatus = document.getElementById('spin-response-status');
  const currentReadout = document.getElementById('spin-current');
  const panel = document.getElementById('langevin');
  const field = document.getElementById('spin-field');
  const couplingButton = document.getElementById('spin-coupling');
  const bathButton = document.getElementById('spin-bath');
  const strength = document.getElementById('spin-strength');
  strength.min = S.strengthMin;
  strength.max = S.strengthMax;
  strength.value = S.strengthInitial;
  document.getElementById('spin-critical').style.left =
    `${(S.strengthCritical - S.strengthMin) / (S.strengthMax - S.strengthMin) * 100}%`;
  const motion = document.getElementById('spin-motion');
  const status = document.getElementById('spin-status');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const period = Math.PI * 2;
  const parameters = new URLSearchParams(window.location.search);
  const study = parameters.get('study');
  let fieldOn = study === 'ohmic' || study === 'subohmic';
  let subohmic = study === 'subohmic';
  let coupled = false, blend = Number(fieldOn), coupling = 0, ordering = 0;
  let paused = reduced, previous = null, frame = null;
  let probeOn = false, probeTime = 0, currentPhase = 0, previousRegime = null;
  function isOrdered() {
    return coupled && Number(strength.value) > S.strengthCritical;
  }

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

  function responseRegime() {
    if (!isOrdered()) return 'ballistic';
    if (!fieldOn) return 'afm';
    return subohmic ? 'subohmic' : 'ohmic';
  }

  // Illustrative step responses: asymptotic behavior is physical; amplitudes and
  // transient shapes are not fitted to a microscopic calculation.
  function stepCurrent(regime, time) {
    if (regime === 'ballistic') return R.ballisticSlope * time;
    if (regime === 'ohmic') return R.ohmicDc * (1 - Math.exp(-R.ohmicRate * time));
    if (regime === 'subohmic') {
      return (1 - Math.exp(-R.ohmicRate * time)) * Math.pow(1 + time, R.subohmicExponent - 1);
    }
    return Math.exp(-R.afmDamping * time) * Math.sin(R.afmFrequency * time);
  }

  function drawResponse() {
    const regime = responseRegime();
    const c = responseCtx;
    c.fillStyle = S.background;
    c.fillRect(0, 0, S.width, R.height);
    c.font = `${S.fontSize}px monospace`;
    c.textAlign = 'center';
    c.fillStyle = S.text;
    c.fillText('LONGITUDINAL RESPONSE / T = 0', S.width / 2, R.titleY);
    c.fillText('Re σs(ω)', (R.spectrumLeft + R.spectrumRight) / 2, R.chartTitleY);
    c.fillText('Spin current jᶻ(t)', (R.timeLeft + R.timeRight) / 2, R.chartTitleY);
    function segment(x1, y1, x2, y2, color) {
      c.strokeStyle = color;
      c.lineWidth = S.pixel;
      c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke();
    }
    for (const [left, right] of [[R.spectrumLeft, R.spectrumRight], [R.timeLeft, R.timeRight]]) {
      segment(left, R.top, left, R.bottom, S.line);
      segment(left, R.bottom, right, R.bottom, S.line);
    }
    c.fillText('0', R.spectrumLeft, R.axisLabelY);
    c.fillText('ω', R.spectrumRight, R.axisLabelY);
    c.fillText('0', R.timeLeft, R.axisLabelY);
    c.fillText('t', R.timeRight, R.axisLabelY);
    const plotHeight = R.bottom - R.top;
    if (regime === 'ballistic') {
      segment(R.spectrumLeft, R.bottom, R.spectrumLeft, R.top, R.currentColor);
      segment(R.spectrumLeft, R.top, R.spectrumLeft - S.arrowHead, R.top + S.arrowHead, R.currentColor);
      segment(R.spectrumLeft, R.top, R.spectrumLeft + S.arrowHead, R.top + S.arrowHead, R.currentColor);
      c.fillText('δ(ω)', (R.spectrumLeft + R.spectrumRight) / 2, R.top + S.fontSize);
    } else {
      let last = null;
      for (let i = 0; i <= R.samples; i++) {
        const w = R.frequencyMax * i / R.samples;
        const value = regime === 'ohmic' ? R.ohmicDc / (1 + w * w)
          : regime === 'subohmic' ? Math.pow(w, 1 - R.subohmicExponent) / (1 + w * w)
          : w * w / (1 + w * w);
        const point = [R.spectrumLeft + (R.spectrumRight - R.spectrumLeft) * i / R.samples,
          R.bottom - plotHeight * value];
        if (last) segment(...last, ...point, R.currentColor);
        last = point;
      }
    }
    const horizon = Math.max(R.timeWindow, probeTime);
    const currentMax = regime === 'ballistic' ? Math.max(1, R.ballisticSlope * horizon) : 1;
    // Leave space below zero for the AFM's oscillating transient.
    const zeroY = regime === 'afm' ? (R.top + R.bottom) / 2 : R.bottom;
    const currentHeight = zeroY - R.top;
    if (regime === 'afm') segment(R.timeLeft, zeroY, R.timeRight, zeroY, S.line);
    let last = null;
    for (let i = 0; i <= R.samples; i++) {
      const point = [R.timeLeft + (R.timeRight - R.timeLeft) * i / R.samples,
        zeroY - currentHeight * stepCurrent(regime, horizon * i / R.samples) / currentMax];
      if (last) segment(...last, ...point, R.currentColor);
      last = point;
    }
    if (probeOn) {
      const x = R.timeLeft + (R.timeRight - R.timeLeft) * probeTime / horizon;
      const y = zeroY - currentHeight * stepCurrent(regime, probeTime) / currentMax;
      c.fillStyle = R.currentColor;
      c.fillRect(x - R.markerSize / 2, y - R.markerSize / 2, R.markerSize, R.markerSize);
    }
    c.fillStyle = S.text;
    c.fillText(probeOn ? '∂xh_z > 0 / WEAK PROBE ON' : 'WEAK FIELD GRADIENT OFF', S.width / 2, R.footerY);
    currentReadout.textContent = probeOn
      ? `${stepCurrent(regime, probeTime).toFixed(2)} (arbitrary units)` : 'Probe off';
  }

  function subohmicArrowsStopped() {
    return responseRegime() === 'subohmic' && probeTime >= R.subohmicArrowDuration * R.timeScale;
  }

  function drawCurrent() {
    if (!probeOn || subohmicArrowsStopped()) return;
    const current = stepCurrent(responseRegime(), probeTime);
    if (Math.abs(current) < R.currentThreshold) return;
    const direction = Math.sign(current);
    ctx.globalAlpha = responseRegime() === 'ohmic'
      ? R.ohmicOpacity * Math.min(1, Math.abs(current) / R.ohmicDc)
      : Math.min(1, Math.abs(current));
    for (let i = 0; i < S.sites - 1; i++) {
      const fraction = ((currentPhase % 1) + 1) % 1;
      const x = S.left + S.spacing * (i + fraction);
      const head = R.currentHead * direction;
      line(x - head, S.chainY - R.currentHead, x, S.chainY, R.currentColor);
      line(x - head, S.chainY + R.currentHead, x, S.chainY, R.currentColor);
    }
    ctx.globalAlpha = 1;
  }

  function draw() {
    block(0, 0, S.width, S.height, S.background);
    ctx.font = `${S.fontSize}px monospace`;
    ctx.fillStyle = S.text;
    ctx.textAlign = 'center';
    ctx.fillText('1D XXZ SPIN CHAIN', S.width / 2, S.titleY);
    ctx.fillText(!coupled ? 'FREE SPINS / RANDOM 3D ROTATION' : !isOrdered() ? 'LUTTINGER LIQUID / FLUCTUATING SPINS' : fieldOn ? 'SPIN DENSITY WAVE' : 'ANTIFERROMAGNET / ALTERNATING Z', S.width / 2, S.orderY);
    ctx.fillText('+z', S.axisX, S.axisLabelY);
    line(S.axisX, S.axisBottom, S.axisX, S.axisTop, S.line);
    line(S.axisX, S.axisTop, S.axisX - S.pixel, S.axisTop + S.arrowHead, S.line);
    line(S.left, S.chainY, S.left + S.spacing * (S.sites - 1), S.chainY, S.line);
    if (blend * ordering > S.snap) {
      ctx.globalAlpha = blend * ordering * S.waveOpacity;
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
      const freeWeight = 1 - ordering;
      const projectedX = free.x * Math.cos(S.depthTilt) - free.y * Math.sin(S.depthTilt);
      const projectedDepth = free.x * Math.sin(S.depthTilt) + free.y * Math.cos(S.depthTilt);
      const z = free.z * freeWeight + spinZ(index) * ordering;
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
    drawCurrent();
    drawResponse();
    ctx.fillStyle = S.text;
    ctx.fillText(coupled ? 'LOCAL RESERVOIRS / COUPLED' : 'INDEPENDENT LOCAL RESERVOIRS', S.width / 2, S.bathLabelY);
  }

  function tick(now) {
    frame = null;
    const dt = previous === null ? 0 : Math.min((now - previous) / S.milliseconds, S.maxStep);
    previous = now;
    if (probeOn && !paused) {
      probeTime += dt * R.timeScale;
      const current = stepCurrent(responseRegime(), probeTime);
      // Bound only the visual speed; the ballistic current itself keeps growing.
      const speed = responseRegime() === 'ballistic'
        ? R.ballisticSpeed * Math.tanh(current) : R.currentSpeed * current;
      if (!subohmicArrowsStopped()) currentPhase += speed * dt / S.spacing;
    }
    const step = reduced ? 1 : Math.min(1, dt * S.transitionRate);
    blend += (Number(fieldOn) - blend) * step;
    coupling += (Number(coupled) - coupling) * step;
    const orderTarget = Number(isOrdered());
    ordering += (orderTarget - ordering) * step;
    if (Math.abs(orderTarget - ordering) < S.snap) ordering = orderTarget;
    if (Math.abs(Number(fieldOn) - blend) < S.snap) blend = Number(fieldOn);
    if (Math.abs(Number(coupled) - coupling) < S.snap) coupling = Number(coupled);
    if (!paused && ordering < 1) spins.forEach(spin => {
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
    if (!paused || blend !== Number(fieldOn) || coupling !== Number(coupled) || ordering !== orderTarget) wake();
  }

  function wake() {
    if (frame === null && !panel.hidden && !document.hidden) frame = requestAnimationFrame(tick);
  }

  function updateResults() {
    const selected = !fieldOn ? 'antiferromagnet' : subohmic ? 'subohmic' : 'ohmic';
    document.querySelectorAll('[data-spin-result]').forEach(result => {
      result.hidden = result.dataset.spinResult !== selected;
    });
  }

  probe.addEventListener('click', () => {
    probeOn = !probeOn;
    probeTime = 0;
    currentPhase = 0;
    updateResponse();
    draw();
    wake();
  });

  strength.addEventListener('input', () => {
    updateOrder();
    wake();
  });

  field.addEventListener('click', () => {
    fieldOn = !fieldOn;
    updateOrder();
    wake();
  });
  bathButton.addEventListener('click', () => {
    subohmic = !subohmic;
    updateOrder();
    wake();
  });
  couplingButton.addEventListener('click', () => {
    coupled = !coupled;
    updateOrder();
    wake();
  });
  function updateOrder() {
    const relativeStrength = Number(strength.value) > S.strengthCritical ? 'Above critical'
      : Number(strength.value) < S.strengthCritical ? 'Below critical' : 'At critical';
    strength.setAttribute('aria-valuetext', `${relativeStrength}; schematic coupling strength`);
    field.setAttribute('aria-pressed', String(fieldOn));
    couplingButton.setAttribute('aria-pressed', String(coupled));
    bathButton.setAttribute('aria-pressed', String(subohmic));
    document.getElementById('spin-field-state').textContent = fieldOn ? 'ON' : 'OFF';
    document.getElementById('spin-coupling-state').textContent = coupled ? 'ON' : 'OFF';
    document.getElementById('spin-bath-state').textContent = subohmic ? 'Subohmic' : 'Ohmic';
    document.getElementById('spin-order').textContent = !coupled
      ? 'Uncoupled · freely rotating 3D spins'
      : !isOrdered() ? `${relativeStrength} · Luttinger liquid` : fieldOn ? 'Spin density wave · Sᶻ' : 'Antiferromagnet · alternating Sᶻ';
    status.textContent = !coupled
      ? 'Choose the field and bath type to explore the corresponding study below; turn on bath-chain coupling to animate its phases.'
      : isOrdered()
        ? 'Above critical: the connected chain develops magnetic order. The corresponding paper is linked below.'
        : `${relativeStrength}: connected spins fluctuate without long-range order. Increase coupling strength above critical to order the chain.`;
    updateResults();
    updateResponse();
  }
  function updateResponse() {
    const regime = responseRegime();
    if (regime !== previousRegime) {
      probeTime = 0;
      currentPhase = 0;
      previousRegime = regime;
    }
    responsePanel.hidden = !probeOn;
    probe.setAttribute('aria-expanded', String(probeOn));
    probe.setAttribute('aria-pressed', String(probeOn));
    document.getElementById('spin-probe-state').textContent = probeOn ? 'ON' : 'OFF';
    const description = regime === 'ballistic'
      ? 'Luttinger liquid: Drude delta peak; a sustained gradient produces a growing ballistic current.'
      : regime === 'ohmic'
        ? 'Ohmic dissipative phase: finite DC conductivity; the current settles to a nonzero value.'
        : regime === 'subohmic'
          ? 'Subohmic dissipative phase: Re σs ∝ ω^(1−s), illustrated with s = 0.5; the transient current decays toward zero. For clarity, bond arrows stop after 3 seconds; the graph retains the tail.'
          : 'Commensurate AFM: zero DC conductivity; an oscillating transient decays toward zero.';
    document.getElementById('spin-dc').textContent = `DC conductivity - ${
      regime === 'ballistic' ? 'perfect (Luttinger liquid)'
        : regime === 'ohmic' ? 'reduced (Ohmic spin density wave)'
          : regime === 'afm' ? 'zero (antiferromagnet)' : 'zero (subohmic spin density wave)'
    }`;
    responseStatus.textContent = `${description} ${probeOn ? 'Probe on; switch off and on to replay.' : 'Turn on the weak field gradient to animate the response.'}`;
    responseCanvas.setAttribute('aria-label', `Schematic T = 0 response. ${description}`);
    drawResponse();
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
