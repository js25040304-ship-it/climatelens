/* ClimateLens soundscape: optional background music for the Trend Detective page.
 * Muted by default; nothing plays until the student turns sound on. The choice is remembered
 * on this device, and a student who turns it off is never asked again or auto-played.
 * Music never carries data: it only follows the scene and the chosen city.
 */
(function (root) {
  'use strict';
  const TRACKS = {
    home: {file: 'audio/home.mp3', title: 'ClimateLens Theme'},
    'Singapore': {file: 'audio/singapore.mp3', title: 'Singapore · Tropical Future'},
    'Kuala Lumpur': {file: 'audio/kuala-lumpur.mp3', title: 'Kuala Lumpur · Rainforest Rhythm'},
    'Bangkok': {file: 'audio/bangkok.mp3', title: 'Bangkok · Golden River'},
    'Ho Chi Minh City': {file: 'audio/ho-chi-minh-city.mp3', title: 'Ho Chi Minh City · Misty Monsoon'},
    'Jakarta': {file: 'audio/jakarta.mp3', title: 'Jakarta · Island Pulse'},
  };
  const KEY = 'climatelens.soundscape';
  const DEFAULT_VOLUME = 0.25;
  const SWITCH_FADE = 2.5;   // seconds of crossfade when the track changes
  const LOOP_FADE = 3;       // seconds of overlap when a track loops back to its start
  const FOCUS_LEVEL = 0.4;   // predict / observe / verify / case scenes play quieter

  /* Pure rules (unit-tested in tests/test_soundscape.cjs). */
  function plan(scene, city) {
    const key = scene > 1 && city && TRACKS[city] ? city : 'home';
    return {key, track: TRACKS[key], focus: scene >= 3};
  }
  function level(volume, focus) {
    const v = Number.isFinite(volume) ? Math.min(1, Math.max(0, volume)) : DEFAULT_VOLUME;
    return v * (focus ? FOCUS_LEVEL : 1);
  }
  function loadPrefs(storage) {
    try {
      const p = JSON.parse(storage.getItem(KEY) || '{}');
      const volume = typeof p.volume === 'number' && p.volume >= 0 && p.volume <= 1 ? p.volume : DEFAULT_VOLUME;
      return {on: p.on === true, asked: p.asked === true, volume};
    } catch (e) {
      return {on: false, asked: false, volume: DEFAULT_VOLUME};
    }
  }
  function savePrefs(storage, prefs) {
    try { storage.setItem(KEY, JSON.stringify(prefs)); } catch (e) { /* private mode: keep in memory only */ }
  }

  /* Browser player: two decks so tracks and loops crossfade instead of cutting. */
  function createPlayer(doc, storage) {
    const prefs = loadPrefs(storage);
    const decks = [new Audio(), new Audio()];
    decks.forEach(a => { a.preload = 'none'; a.volume = 0; });
    const ramps = new Map();
    let active = 0, currentKey = null, scene = 1, city = null, looping = false, started = false;
    const ui = {};

    function ramp(audio, to, seconds, done) {
      cancelAnimationFrame(ramps.get(audio));
      const from = audio.volume, t0 = performance.now(), ms = Math.max(1, seconds * 1000);
      const step = now => {
        const k = Math.min(1, (now - t0) / ms);
        audio.volume = Math.min(1, Math.max(0, from + (to - from) * k));
        if (k < 1) ramps.set(audio, requestAnimationFrame(step));
        else { ramps.delete(audio); if (done) done(); }
      };
      ramps.set(audio, requestAnimationFrame(step));
    }
    function target() { return level(prefs.volume, plan(scene, city).focus); }
    function start(key, fade) {
      const incoming = decks[1 - active], outgoing = decks[active];
      const file = TRACKS[key].file;
      if (!incoming.src.endsWith(file)) incoming.src = file;
      incoming.currentTime = 0; incoming.volume = 0;
      const playing = incoming.play();
      if (playing && playing.catch) playing.catch(() => { started = false; render('Tap anywhere to start'); });
      ramp(incoming, target(), fade);
      ramp(outgoing, 0, fade, () => { if (decks[active] !== outgoing) outgoing.pause(); });
      active = 1 - active; currentKey = key; looping = false; started = true;
    }
    function sync(fade = SWITCH_FADE) {
      const p = plan(scene, city);
      render();
      if (!prefs.on || doc.hidden) return;
      if (p.key !== currentKey || !started) start(p.key, currentKey ? fade : 1);
      else ramp(decks[active], target(), 0.6);
    }
    function stopAll(fade) {
      decks.forEach(a => ramp(a, 0, fade, () => a.pause()));
      currentKey = null; started = false;
    }
    function onTime(e) {
      const a = e.target;
      if (!prefs.on || a !== decks[active] || looping || !Number.isFinite(a.duration)) return;
      if (a.currentTime > a.duration - LOOP_FADE) { looping = true; start(currentKey, LOOP_FADE); }
    }
    decks.forEach(a => {
      a.addEventListener('timeupdate', onTime);
      a.addEventListener('error', () => { if (a === decks[active] && prefs.on) render('Music file unavailable'); });
    });

    function setOn(on) {
      prefs.on = on; prefs.asked = true; savePrefs(storage, prefs);
      if (ui.offer) ui.offer.hidden = true;
      if (on) sync(1); else { stopAll(0.8); render(); }
    }
    function render(note) {
      if (!ui.toggle) return;
      const p = plan(scene, city);
      ui.toggle.setAttribute('aria-pressed', String(prefs.on));
      ui.state.textContent = prefs.on ? 'Sound on' : 'Sound off';
      ui.title.textContent = note || (p.track.title + (prefs.on && p.focus ? ' · quieter while you work' : ''));
      ui.volume.value = Math.round(prefs.volume * 100);
      ui.pct.textContent = Math.round(prefs.volume * 100) + '%';
      ui.root.classList.toggle('on', prefs.on);
    }

    return {
      mount(els) {
        Object.assign(ui, els);
        ui.toggle.addEventListener('click', () => setOn(!prefs.on));
        ui.volume.addEventListener('input', () => {
          prefs.volume = Number(ui.volume.value) / 100; savePrefs(storage, prefs);
          render(); if (prefs.on && started) ramp(decks[active], target(), 0.2);
        });
        if (ui.offerOn) ui.offerOn.addEventListener('click', () => setOn(true));
        if (ui.offerNo) ui.offerNo.addEventListener('click', () => setOn(false));
        // A remembered "on" still needs one user gesture before the browser allows sound.
        const firstGesture = () => { if (prefs.on && !started) sync(1); };
        doc.addEventListener('pointerdown', firstGesture);
        doc.addEventListener('keydown', firstGesture);
        doc.addEventListener('visibilitychange', () => {
          if (doc.hidden) decks.forEach(a => a.pause());
          else if (prefs.on && started) decks[active].play().catch(() => {});
        });
        render();
      },
      scene(n, cityName) {
        const firstIsland = n === 2 && scene === 1;
        scene = n; city = cityName || null;
        if (ui.offer) ui.offer.hidden = !(firstIsland && !prefs.on && !prefs.asked);  // offered once, never nags
        sync();
      },
      prefs: () => ({...prefs}),
      // read-only snapshot for manual QA in the browser console
      debug: () => ({key: currentKey, started, scene, city, decks: decks.map(a => ({src: a.src.split('/').pop(), volume: +a.volume.toFixed(3), paused: a.paused, time: +a.currentTime.toFixed(1)}))}),
    };
  }

  const api = {TRACKS, KEY, DEFAULT_VOLUME, FOCUS_LEVEL, SWITCH_FADE, LOOP_FADE, plan, level, loadPrefs, savePrefs, createPlayer};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Soundscape = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
