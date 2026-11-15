/* ClimateLens island ring: the sky scene of the Trend Detective page.
 * Five islands float on one ring that turns slowly by itself. Drag/swipe or the arrows turn it,
 * the mouse wheel moves the camera in and out, and clicking an island flies the camera to it
 * and shows its case file. "Open the case" hands over to the page (pickCity), nothing else.
 * The ring carries no data: the case file only names the city, its coordinates and the variables.
 */
(function (root) {
  'use strict';
  const ZOOM_MIN = 0.65, ZOOM_MAX = 1.6;
  const AUTO_SPEED = 1 / 9;   // islands per second while idle
  const IDLE_MS = 2500;       // pause after any interaction before turning again
  const LABEL_WINDOW = 0.12;  // the big name shows while the nearest island is this close to the front

  /* Pure rules (unit-tested in tests/test_ring.cjs). */
  const mod = (a, n) => ((a % n) + n) % n;
  function frontIndex(pos, n) { return mod(Math.round(pos), n); }
  function offset(i, pos, n) { return mod(i - pos + n / 2, n) - n / 2; }      // -n/2 .. n/2, 0 = front
  function turnTarget(pos, i, n) { let d = mod(i - pos, n); if (d > n / 2) d -= n; return pos + d; }
  function slot(a, g) {
    const t = a * 2 * Math.PI / (g.n || 5), depth = (Math.cos(t) + 1) / 2;   // 1 front .. 0 back
    return {x: g.cx + g.rx * Math.sin(t), y: g.back + (g.front - g.back) * depth * depth, depth,
      s: 0.22 + 0.78 * Math.pow(depth, 2.6)};
  }
  function tagVisible(a, depth, motion, focused) {
    return !focused && Math.sign(a) === motion && Math.abs(a) > 0.5 && depth > 0.4;
  }
  function labelVisible(pos, focused) { return !focused && Math.abs(pos - Math.round(pos)) < LABEL_WINDOW; }
  function settle(start, pos, v) {
    const flick = Math.abs(v) > 0.6 ? -Math.sign(v) * 0.5 : 0;
    return Math.round(Math.max(start - 2, Math.min(start + 2, pos + flick)));
  }
  function clampZoom(z) { return Number.isFinite(z) ? Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, z)) : 1; }

  /* Browser controller. Expects the #ring* elements in index.html.
   * opts: {cities:[{name,country,lat,lon,i}], art(city)->html, vars:[tag], onOpen(i), isDone(name), reduced,
   *        deepLink(city)->{href,label}|null (optional extra link on the case file)} */
  function createRing(doc, win, opts) {
    const $ = id => doc.getElementById(id);
    const el = {stage: $('ringStage'), world: $('ringWorld'), glow: $('ringGlow'), isles: $('ringIsles'),
      label: $('ringLabel'), labelName: $('ringLabelName'), labelCoords: $('ringLabelCoords'),
      panel: $('ringPanel'), pEyebrow: $('ringEyebrow'), pName: $('ringName'), pCoords: $('ringCoords'), pVars: $('ringVars'),
      open: $('ringOpen'), back: $('ringBack'), deep: $('ringDeep'), prev: $('ringPrev'), next: $('ringNext'), play: $('ringPlay'),
      dots: $('ringDots'), map: $('ringMap'), zoom: $('ringZoom'), live: $('ringLive')};
    const C = opts.cities, N = C.length, reduced = !!opts.reduced;
    const fmt = c => `${Math.abs(c.lat).toFixed(2)}°${c.lat < 0 ? 'S' : 'N'} · ${c.lon.toFixed(2)}°E`;
    const short = name => name.replace('Ho Chi Minh City', 'HCMC').replace('Kuala Lumpur', 'KL');
    let pos = 0, prevPos = 0, motion = 1, tween = null, drag = null, hovering = false;
    let auto = !reduced, idleUntil = 0, focused = null, userZoom = 1, active = false, raf = 0, last = 0, shown = -1;
    const cam = {z: 1, x: 0, y: 0}, camT = {z: 1, x: 0, y: 0};
    let geo = {}, isles = [], dots = [], mapDots = [];

    // mini map: lon 96..112, lat -9..17
    const mx = lon => (lon - 96) / 16 * 150 + 10, my = lat => (17 - lat) / 26 * 180 + 10;
    el.map.innerHTML = `<rect width="170" height="200" rx="8" fill="#e3efe9"/>
      <line x1="0" x2="170" y1="${my(0)}" y2="${my(0)}" stroke="#2e7a68" stroke-dasharray="3 3"/>
      <text x="4" y="${my(0) - 3}" font-size="9" fill="#2e7a68">Equator</text>` +
      C.map((c, k) => `<circle data-k="${k}" cx="${mx(c.lon)}" cy="${my(c.lat)}" r="4" fill="#5d7069"/>`).join('') +
      `<text id="ringMapLabel" font-size="10" font-weight="700" fill="#173b37"></text>`;
    mapDots = [...el.map.querySelectorAll('circle')];
    el.dots.innerHTML = C.map((c, k) => `<button type="button" data-k="${k}" aria-label="${c.name}">${short(c.name)}</button>`).join('');
    dots = [...el.dots.querySelectorAll('button')];
    el.pVars.innerHTML = opts.vars.map(v => `<li>${v}</li>`).join('');

    function build() {
      el.isles.innerHTML = C.map((c, k) => `<button type="button" class="isle${opts.isDone(c.name) ? ' done' : ''}" data-k="${k}" aria-label="${c.name}, ${c.country}: show case file"><div class="art">${opts.art(c)}</div><span class="tag">${c.name}</span></button>`).join('');
      isles = [...el.isles.querySelectorAll('.isle')];
      isles.forEach(b => {
        b.addEventListener('pointerenter', () => { hovering = true; });
        b.addEventListener('pointerleave', () => { hovering = false; poke(); });
        b.addEventListener('focus', poke);
        b.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fly(+b.dataset.k); } });
      });
      measure(); shown = -1;
    }
    function measure() {
      const W = win.innerWidth, H = win.innerHeight, narrow = W < 820;
      const size = narrow ? Math.min(W * 0.62, 380) : Math.min(H * 0.46, W * 0.36, 500);
      const rx = narrow ? W * 0.36 : Math.min(W * 0.33, 540);
      const front = narrow ? H * 0.55 : H * 0.62, back = narrow ? H * 0.36 : H * 0.42;
      geo = {W, H, narrow, size, rx, front, back, cx: W / 2, n: N};
      const g = el.glow.style, gw = size * 0.72;
      g.width = gw + 'px'; g.height = gw * 0.28 + 'px'; g.left = W / 2 + 'px'; g.top = front + size * 0.36 + 'px';
      isles.forEach(b => { b.style.width = size + 'px'; b.querySelector('.tag').style.fontSize = (narrow ? 13 : 14) / 0.6 + 'px'; });
      aim();
      if (reduced || !raf) Object.assign(cam, camT);
    }
    function zoomOffset(z) { const C0 = {x: geo.W / 2, y: (geo.front + geo.back) / 2}; return {x: C0.x - z * C0.x, y: C0.y - z * C0.y}; }
    function aim() {
      if (focused === null) { const o = zoomOffset(userZoom); camT.z = userZoom; camT.x = o.x; camT.y = o.y; return; }
      const z = geo.narrow ? 1.25 : 1.5, P = geo.narrow ? {x: geo.W / 2, y: geo.H * 0.30} : {x: geo.W * 0.34, y: geo.H * 0.52};
      camT.z = z; camT.x = P.x - z * geo.cx; camT.y = P.y - z * geo.front;
    }

    function render() {
      if (Math.abs(pos - prevPos) > 1e-4) motion = Math.sign(pos - prevPos); prevPos = pos;
      const k = frontIndex(pos, N);
      isles.forEach((b, i) => {
        const a = offset(i, pos, N), p = slot(a, geo), dim = focused !== null && i !== focused;
        b.style.transform = `translate(${p.x}px,${p.y}px) translate(-50%,-50%) scale(${p.s})`;
        b.style.zIndex = Math.round(p.depth * 100);
        b.style.opacity = dim ? 0.12 : 0.55 + 0.45 * p.depth;
        b.style.filter = p.depth < 0.95 ? `blur(${((1 - p.depth) * 2.2).toFixed(2)}px) saturate(${(0.75 + 0.25 * p.depth).toFixed(2)})` : 'none';
        b.style.pointerEvents = dim ? 'none' : 'auto';
        b.tabIndex = i === k ? 0 : -1;
        b.classList.toggle('cur', Math.abs(a) < 0.5);
        b.querySelector('.tag').style.opacity = tagVisible(a, p.depth, motion, focused !== null) ? 1 : 0;
      });
      const showLabel = labelVisible(pos, focused !== null);
      el.glow.style.opacity = focused !== null ? 1 : Math.max(0, 1 - Math.abs(pos - Math.round(pos)) * 4);
      el.world.style.transform = `translate(${cam.x}px,${cam.y}px) scale(${cam.z})`;
      if (showLabel && !el.label.classList.contains('show')) {   // change text only while hidden
        const c = C[k]; el.labelName.textContent = c.name; el.labelCoords.textContent = fmt(c);
      }
      el.label.classList.toggle('show', showLabel);
      const f = slot(0, geo), sx = cam.x + cam.z * f.x, sy = cam.y + cam.z * f.y, half = geo.size * cam.z / 2, L = el.label.style;
      if (geo.narrow) { L.left = '16px'; L.right = '16px'; L.top = Math.min(geo.H - 190, sy + half * 0.95) + 'px'; }
      else { L.left = Math.min(geo.W - 280, sx + half * 0.82) + 'px'; L.right = 'auto'; L.top = Math.min(geo.H - 190, sy + half * 0.2) + 'px'; }
      ui();
    }
    function ui() {
      const i = focused !== null ? focused : frontIndex(pos, N);
      if (i === shown) return; shown = i;
      const c = C[i];
      dots.forEach((d, k) => d.setAttribute('aria-current', String(k === i)));
      mapDots.forEach((d, k) => { d.setAttribute('r', k === i ? 7 : 4); d.setAttribute('fill', k === i ? '#e0832f' : '#5d7069'); });
      const M = doc.getElementById('ringMapLabel'); M.textContent = short(c.name);
      M.setAttribute('x', Math.min(mx(c.lon) + 9, 125)); M.setAttribute('y', my(c.lat) + 4);
      el.pName.textContent = c.name; el.pCoords.textContent = `${c.country} · ${fmt(c)}`;
      el.pEyebrow.textContent = 'Case file · NASA POWER 2001–2025' + (opts.isDone(c.name) ? ' · ✓ case opened' : '');
      el.open.textContent = `Open the ${c.name} case →`;
      const deep = opts.deepLink ? opts.deepLink(c) : null;   // e.g. Singapore's Island Lab
      if (el.deep) { el.deep.hidden = !deep; if (deep) { el.deep.href = deep.href; el.deep.textContent = deep.label; } }
    }

    function poke() { idleUntil = performance.now() + IDLE_MS; }
    function turn(to, ms) { tween = {from: pos, to, t0: performance.now(), ms: reduced ? 1 : ms}; }
    function step(dir) {
      poke();
      if (focused !== null) { fly(mod(focused + dir, N)); return; }
      turn((tween ? tween.to : Math.round(pos)) + dir, 650);
    }
    function fly(i) {
      focused = i; shown = -1; turn(turnTarget(pos, i, N), 900); aim(); poke();
      doc.body.classList.add('ring-focus');
      el.live.textContent = `${C[i].name}. Case file open.`;
      setTimeout(() => { if (focused === i) el.open.focus({preventScroll: true}); }, reduced ? 0 : 700);
    }
    function land(keepFocus) {
      if (focused === null) return;
      const i = focused; focused = null; shown = -1; aim(); poke();
      doc.body.classList.remove('ring-focus');
      if (keepFocus !== false && active) isles[i].focus({preventScroll: true});
    }
    function setZoom(z) { userZoom = clampZoom(z); poke(); el.zoom.textContent = `Zoom ${Math.round(userZoom * 100)}%`; aim(); }
    function setAuto(on) {
      auto = on; el.play.setAttribute('aria-pressed', String(on)); el.play.textContent = on ? '❚❚' : '▶';
      el.play.setAttribute('aria-label', on ? 'Pause the turning islands' : 'Turn the islands slowly');
    }

    function frame(now) {
      const dt = Math.min(0.05, (now - last) / 1000); last = now;
      if (tween) {
        const k = Math.min(1, (now - tween.t0) / tween.ms), e = 1 - Math.pow(1 - k, 3);
        pos = tween.from + (tween.to - tween.from) * e;
        if (k >= 1) tween = null;
      } else if (!drag && auto && focused === null && !hovering && now > idleUntil) pos += dt * AUTO_SPEED;
      const ease = reduced ? 1 : 1 - Math.exp(-dt * 5);
      cam.z += (camT.z - cam.z) * ease; cam.x += (camT.x - cam.x) * ease; cam.y += (camT.y - cam.y) * ease;
      render();
      raf = win.requestAnimationFrame(frame);
    }

    // controls
    el.prev.addEventListener('click', () => step(-1));
    el.next.addEventListener('click', () => step(1));
    el.play.addEventListener('click', () => { setAuto(!auto); poke(); });
    dots.forEach(d => d.addEventListener('click', () => fly(+d.dataset.k)));
    mapDots.forEach(d => d.addEventListener('click', () => fly(+d.dataset.k)));
    el.open.addEventListener('click', () => { if (focused !== null) opts.onOpen(C[focused].i); });
    el.back.addEventListener('click', () => land());
    doc.addEventListener('keydown', e => {
      if (!active || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
      if (e.key === 'ArrowLeft') { step(-1); e.preventDefault(); }
      else if (e.key === 'ArrowRight') { step(1); e.preventDefault(); }
      else if (e.key === 'Escape') land();
      else if (e.key === '+' || e.key === '=') setZoom(userZoom * 1.15);
      else if (e.key === '-') setZoom(userZoom / 1.15);
    });
    // drag / swipe turns the ring; a tap on an island flies to it; a tap on empty sky lands again
    el.stage.addEventListener('pointerdown', e => {
      if (e.button) return;
      drag = {x: e.clientX, start: pos, moved: false, id: e.pointerId, last: e.clientX, lt: performance.now(), v: 0};
      tween = null; poke();
    });
    el.stage.addEventListener('pointermove', e => {
      if (!drag) return;
      const dx = e.clientX - drag.x;
      if (!drag.moved && Math.abs(dx) > 8 && focused === null) { drag.moved = true; el.stage.setPointerCapture(drag.id); el.stage.classList.add('dragging'); }
      if (drag.moved) {
        const now = performance.now(); drag.v = (e.clientX - drag.last) / Math.max(1, now - drag.lt); drag.last = e.clientX; drag.lt = now;
        pos = drag.start - dx / (geo.rx * 0.9 * cam.z); poke();
      }
    });
    el.stage.addEventListener('pointerup', e => {
      if (!drag) return;
      const d = drag; drag = null; el.stage.classList.remove('dragging'); poke();
      if (d.moved) { turn(settle(d.start, pos, d.v), 500); return; }
      const hit = e.target.closest && e.target.closest('.isle');
      if (hit) fly(+hit.dataset.k); else land(false);
    });
    el.stage.addEventListener('pointercancel', () => { drag = null; el.stage.classList.remove('dragging'); });
    el.stage.addEventListener('wheel', e => {
      e.preventDefault();
      if (focused !== null) { if (e.deltaY > 0) land(false); return; }   // scrolling out leaves the island
      setZoom(userZoom * Math.exp(-e.deltaY * 0.0012));
    }, {passive: false});
    win.addEventListener('resize', () => { if (isles.length) measure(); });

    setAuto(auto); build();
    return {
      rebuild: build,                        // after island images load or a case is closed
      setActive(on) {                        // only animate while the sky scene is showing
        active = on;
        if (on && !raf) { last = performance.now(); poke(); raf = win.requestAnimationFrame(frame); }
        if (!on && raf) { win.cancelAnimationFrame(raf); raf = 0; land(false); }
      },
      show(cityName) {                       // bring a city to the front without animation (back from a case)
        const k = C.findIndex(c => c.name === cityName);
        if (k >= 0) { tween = null; pos = turnTarget(pos, k, N); prevPos = pos; render(); }
      },
      debug: () => ({pos: +pos.toFixed(3), front: C[frontIndex(pos, N)].name, focused: focused === null ? null : C[focused].name, auto, zoom: userZoom, running: !!raf}),
    };
  }

  const api = {ZOOM_MIN, ZOOM_MAX, AUTO_SPEED, LABEL_WINDOW, frontIndex, offset, turnTarget, slot, tagVisible, labelVisible, settle, clampZoom, createRing};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Ring = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
