'use strict';
const $ = id => document.getElementById(id);
const $$ = selector => [...document.querySelectorAll(selector)];
const UI = window.ClimateUI;
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const evidenceGate = UI.gate(), writingGate = UI.gate();
let catalog, result = null, revealed = false, proposal = null, toastTimer, chartGeometry;
const requests = new Map(), buttonJobs = new Map();
const settings = () => ({city: $('city').value, variable: $('variable').value, start: $('start').valueAsNumber, end: $('end').valueAsNumber});
const writing = () => ({settings: settings(), result_id: result?.id || null, question: $('question').value, hypothesis: $('hypothesis').value, observation: $('observation').value, conclusion: $('conclusion').value, reviewed: $('reviewed').checked, message: $('message').value});
const text = (id, value) => { $(id).textContent = value; };
function announce(message, type = '') {
  text('statusText', message); $('status').classList.remove('error', 'loading');
  if (type) $('status').classList.add(type);
}
function toast(message) { text('toast', message); $('toast').classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').classList.remove('show'), 3800); }
function go(id, focus = false) {
  const target = $(id); target.scrollIntoView({behavior: reducedMotion ? 'instant' : 'smooth', block: 'start'});
  if (focus) { target.setAttribute('tabindex', '-1'); target.focus({preventScroll: true}); }
}
function message(id, value, error = false) { text(id, value); $(id).hidden = !value; $(id).classList.toggle('error', error); }
function abortRequests(names) { names.forEach(name => requests.get(name)?.abort()); }
async function api(path, data) {
  // The separately packaged public preview uses recorded NASA results only.
  // Normal FastAPI deployments always use the existing server endpoints.
  if (document.body.dataset.mode === 'snapshot' && window.ClimateSnapshot) return window.ClimateSnapshot.request(path, data);
  requests.get(path)?.abort(); const controller = new AbortController(); requests.set(path, controller);
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 65000);
  try {
    const response = await fetch('/api/' + path, {method: data ? 'POST' : 'GET', headers: {'Content-Type': 'application/json'}, body: data ? JSON.stringify(data) : undefined, signal: controller.signal});
    if (!response.ok) {
      let detail; try { detail = (await response.json()).detail; } catch { /* preserve useful HTTP status */ }
      let msg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(e => `${e.loc?.at(-1) || 'Input'}: ${e.msg || 'invalid value'}`).join('; ') : 'The server could not complete this request.';
      if (response.status === 410) msg = 'This evidence has expired or the server restarted. Run the investigation again; your writing is retained.';
      if (response.status === 409) msg = 'The evidence no longer matches these settings. Run the investigation again; your writing is retained.';
      throw Error(msg);
    }
    return response;
  } catch (error) {
    if (timedOut) throw Error('This request took too long. Try again; your writing is still here.');
    if (error instanceof TypeError) throw Error('Connection unavailable. Check that the application is running and try again. Your writing is retained.');
    throw error;
  } finally { clearTimeout(timer); if (requests.get(path) === controller) requests.delete(path); }
}
async function busy(id, operation, onError) {
  const button = $(id), job = Symbol(id); buttonJobs.set(id, job); button.disabled = true; button.setAttribute('aria-busy', 'true');
  try { await operation(); } catch (error) {
    if (error.name !== 'AbortError') { if (onError) onError(error.message); else { announce(error.message, 'error'); toast(error.message); } }
  } finally {
    if (buttonJobs.get(id) === job) { buttonJobs.delete(id); button.disabled = id === 'run' && !catalog; button.removeAttribute('aria-busy'); }
  }
}
function updateStatus() {
  const complete = !!(result?.stats && revealed && $('reviewed').checked && $('conclusion').value.trim());
  if (complete) { announce('Investigation completed · Your conclusion is ready to export.'); text('completionLabel', 'A question explored. A conclusion in your own words.'); }
  else if (result?.stats) { announce(revealed ? 'Evidence revealed · Review the uncertainty, then write your own conclusion.' : 'Observations loaded · Look for patterns before revealing the statistics.'); text('completionLabel', 'The next step is your own explanation.'); }
  else if (result) announce('Observations loaded. Trend inference unavailable: ' + result.analysis_error, 'error');
  else { announce('Ready when you are. Confirm your question and settings.'); text('completionLabel', 'An investigation starts with curiosity.'); }
  const done = [!!result, revealed, revealed && $('reviewed').checked, complete];
  $$('.chapter-rail a').forEach((a, i) => a.classList.toggle('done', done[i]));
}
function definition() {
  if (!catalog) return;
  const s = settings(), v = catalog.variables[s.variable];
  text('definition', v ? `${v.definition} ${v.aggregation}.` : 'Choose a supported environmental variable.');
  const point = catalog.cities[s.city];
  text('scopeDetail', point ? `${Math.abs(point[0]).toFixed(4)}° ${point[0] < 0 ? 'S' : 'N'} / ${Math.abs(point[1]).toFixed(4)}° ${point[1] < 0 ? 'W' : 'E'} · NASA POWER point` : 'Choose the representative location');
}
function hideFeedback() { $('feedbackPanel').hidden = true; message('feedbackStatus', ''); text('answer', ''); text('tutorReason', ''); proposal = null; $('applyProposal').hidden = true; }
function invalidate() {
  evidenceGate.next(); writingGate.next(); abortRequests(['investigate','interpret','tutor','report']);
  result = null; revealed = false; chartGeometry = null; proposal = null;
  $('reviewed').checked = false; $('evidence').hidden = true; $('evidencePlaceholder').hidden = false; $('verify').disabled = true;
  $('yearExplorer').hidden = true; $('trendLegend').hidden = true; $('chartTooltip').hidden = true;
  $('chart').classList.remove('loading'); $('chart').replaceChildren();
  const empty = document.createElement('div'); empty.className = 'chart-empty'; const p = document.createElement('p'); p.textContent = 'A new lens. A new investigation.'; const hint = document.createElement('span'); hint.textContent = 'Settings changed. Load matching evidence to continue.'; empty.append(p, hint); $('chart').append(empty);
  text('chartTitle', 'Your next question is ready.'); text('source', 'Previous evidence cleared. Your writing is retained; review it against the next result.'); text('dataBadge', 'Awaiting evidence');
  text('table', ''); text('sourceRecord', ''); text('metrics', ''); text('method', ''); text('excludedYears', '');
  text('verificationSeal', 'Evidence stays hidden until you choose to reveal it');
  hideFeedback(); message('parseMessage', ''); message('scopeError', '');
  if ($('conclusion').value.trim() || $('observation').value.trim()) { text('draftNote', 'Your writing was retained. Review it for the changed question and settings before exporting.'); $('draftNote').classList.add('needs-review'); }
  updateStatus(); definition();
}
function validateScope() {
  const error = UI.scopeError(settings(), new Date().getFullYear() - 1);
  message('scopeError', error, true); ['city','variable','start','end'].forEach(id => $(id).setAttribute('aria-invalid', String(!!error)));
  return !error;
}
function showYear(index, showTooltip = false) {
  if (!result?.annual.length) return;
  const i = Math.min(result.annual.length - 1, Math.max(0, Number(index))), row = result.annual[i];
  $('yearCursor').value = i; text('selectedYear', row.year); text('selectedValue', `${UI.number(row.value, 4)} ${UI.unit(result.unit)}`);
  $('yearCursor').setAttribute('aria-valuetext', `${row.year}: ${UI.number(row.value, 4)} ${UI.unit(result.unit)}`);
  $$('.chart-point').forEach((point, j) => point.classList.toggle('selected', i === j));
  if (showTooltip && chartGeometry) {
    text('chartTooltip', `${row.year} · ${UI.number(row.value, 5)} ${UI.unit(result.unit)}`); $('chartTooltip').hidden = false;
    const {w, h, x, y} = chartGeometry, box = $('chart').getBoundingClientRect(), card = $('observationCard').getBoundingClientRect();
    const left = box.left - card.left + x(row.year) / w * box.width;
    $('chartTooltip').style.left = Math.max(8, Math.min(left - 70, card.width - 215)) + 'px';
    $('chartTooltip').style.top = box.top - card.top + y(row.value) / h * box.height - 46 + 'px';
  }
}
function renderChart(animate = true) {
  const rows = result.annual;
  if (!rows.length) { text('chart', 'No complete annual observations. Inspect the source and excluded years.'); return; }
  const compact = innerWidth <= 760;
  const w = compact ? 420 : 900, h = compact ? 300 : 320, left = compact ? 65 : 78, right = 28, top = 32, bottom = 43;
  const values = rows.map(r => r.value), all = revealed && result.stats ? [...values, ...result.stats.fitted] : values;
  let low = Math.min(...all), high = Math.max(...all); const pad = (high - low) * 0.16 || 1; low -= pad; high += pad;
  const x = year => left + (year - rows[0].year) / (rows.at(-1).year - rows[0].year || 1) * (w - left - right);
  const y = value => h - bottom - (value - low) / (high - low) * (h - top - bottom);
  chartGeometry = {w, h, x, y};
  const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`); svg.setAttribute('role','group'); svg.setAttribute('aria-label', `${result.settings.city}: annual ${catalog.variables[result.settings.variable].label}. ${revealed ? 'Trend revealed.' : 'Trend not yet revealed.'}`);
  function el(tag, attrs, value) { const n = document.createElementNS(ns, tag); Object.entries(attrs).forEach(([k,v]) => n.setAttribute(k,v)); if (value !== undefined) n.textContent = value; svg.append(n); return n; }
  for (let i = 0; i < 5; i++) { const v = low + (high - low) * i / 4; el('line', {x1:left,x2:w-right,y1:y(v),y2:y(v),stroke:'#dce5d1','stroke-width':1}); el('text',{x:left-12,y:y(v)+4,'text-anchor':'end','font-size':11,fill:'#7d9269'}, UI.number(v,4)); }
  // Split at missing years rather than drawing an invented bridge over a gap.
  const segments = []; rows.forEach(r => { const last = segments.at(-1); if (!last || r.year !== last.at(-1).year + 1) segments.push([r]); else last.push(r); });
  segments.forEach(part => el('polyline',{points:part.map(r => `${x(r.year)},${y(r.value)}`).join(' '),class:'data-line' + (animate && !reducedMotion ? ' enter' : ''),pathLength:1}));
  if (revealed && result.stats) el('polyline',{points:rows.map((r,i) => `${x(r.year)},${y(result.stats.fitted[i])}`).join(' '),class:'trend-line'});
  rows.forEach((r,i) => {
    const point = el('circle',{cx:x(r.year),cy:y(r.value),r:4,class:'chart-point',tabindex:0,role:'button','aria-label':`${r.year}: ${UI.number(r.value,5)} ${UI.unit(result.unit)}`});
    point.addEventListener('pointerenter',()=>showYear(i,true)); point.addEventListener('focus',()=>showYear(i,true)); point.addEventListener('click',()=>showYear(i,true));
    point.addEventListener('keydown',event => { if (['ArrowRight','ArrowLeft'].includes(event.key)) { event.preventDefault(); const next = Math.max(0,Math.min(rows.length-1,i+(event.key==='ArrowRight'?1:-1))); $$('.chart-point')[next].focus(); } if (event.key === 'Escape') $('chartTooltip').hidden = true; });
  });
  const ticks = [...new Set([rows[0].year, ...rows.filter(r => r.year % (compact ? 10 : 5) === 0).map(r=>r.year), rows.at(-1).year])];
  ticks.forEach(year => el('text',{x:x(year),y:h-17,'text-anchor':'middle','font-size':11,fill:'#7d9269'},year));
  el('text',{x:left,y:17,'font-size':11,fill:'#6e8757'},UI.unit(result.unit));
  $('chart').replaceChildren(svg); $('chart').onpointerleave = () => { $('chartTooltip').hidden = true; };
  $('yearExplorer').hidden = false; $('yearCursor').max = rows.length - 1;
  showYear(Math.min(Number($('yearCursor').value), rows.length - 1));
}
function renderTable() {
  const t = document.createElement('table'), caption = document.createElement('caption'); caption.className = 'sr-only'; caption.textContent = `Annual ${catalog.variables[result.settings.variable].label} observations for ${result.settings.city}`; t.append(caption);
  const thead = document.createElement('thead'), tr = document.createElement('tr');
  ['Year', UI.unit(result.unit)].forEach(value => { const th = document.createElement('th'); th.scope = 'col'; th.textContent = value; tr.append(th); }); thead.append(tr); t.append(thead);
  const tbody = document.createElement('tbody'); result.annual.forEach(row => { const line = document.createElement('tr'); [row.year,UI.number(row.value,6)].forEach(value => { const td = document.createElement('td'); td.textContent = value; line.append(td); }); tbody.append(line); }); t.append(tbody); $('table').replaceChildren(t);
  $('sourceRecord').replaceChildren();
  const add = value => { const p = document.createElement('p'); p.textContent = value; $('sourceRecord').append(p); };
  add(`Source units: ${result.source_unit}. Annual aggregation: ${result.aggregation}.`);
  add(`Retrieved: ${result.retrieved_at}. Retained: ${result.annual.length} complete years. Excluded: ${result.excluded_years.length}.`);
  UI.excluded(result.excluded_years).forEach(add);
  if (result.source_url?.startsWith('https://power.larc.nasa.gov/')) { const a = document.createElement('a'); a.href = result.source_url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = 'Open the original NASA POWER request ↗'; $('sourceRecord').append(a); }
  if (result.archive_provenance?.path?.startsWith('evidence/nasa-data/')) { const p = document.createElement('p'), a = document.createElement('a'); a.href = 'https://github.com/js25040304-ship-it/climatelens/blob/main/' + result.archive_provenance.path; a.target = '_blank'; a.rel = 'noopener'; a.textContent = 'Inspect this saved record in GitHub ↗'; p.append(a); $('sourceRecord').append(p); add('Recorded result SHA-256: ' + result.archive_provenance.sha256); }
}
function renderEvidence() {
  const s = result?.stats; if (!s) return;
  revealed = true; $('evidence').hidden = false; $('evidencePlaceholder').hidden = true; $('trendLegend').hidden = false; text('verificationSeal', 'OLS trend / approximate Newey–West HAC uncertainty');
  $('metrics').replaceChildren();
  const unit = UI.unit(result.unit);
  [['Estimated change / decade',UI.number(s.slope_decade),`${unit} per decade`],['95% confidence interval',`${UI.number(s.ci95_year[0]*10)} to ${UI.number(s.ci95_year[1]*10)}`,`${unit} per decade`],['p-value',UI.pValue(s.p_value),`${s.n} complete annual observations`]].forEach(([label,value,note]) => { const d = document.createElement('div'); d.className = 'metric'; const a = document.createElement('span'), b = document.createElement('strong'), c = document.createElement('small'); a.textContent = label; b.textContent = value; c.textContent = note; d.append(a,b,c); $('metrics').append(d); });
  text('interpretation', `The estimated trend is ${s.direction}. ` + (s.significant ? 'The zero-slope null is rejected at the 0.05 threshold. Statistical significance does not describe the practical size of a change.' : 'The slope is not statistically distinguishable from zero at the 0.05 threshold. This does not prove an absence of change.') + ' A trend alone does not establish a cause.');
  $('method').replaceChildren(); const method = document.createElement('p'); method.textContent = `${s.method} Aggregation: ${result.aggregation}.`; $('method').append(method); const list = document.createElement('ul'); s.limitations.forEach(value => { const li = document.createElement('li'); li.textContent = value; list.append(li); }); $('method').append(list);
  const excluded = document.createElement('ul'); excluded.className = 'excluded-list'; UI.excluded(result.excluded_years).forEach(value => { const li = document.createElement('li'); li.textContent = value; excluded.append(li); }); $('excludedYears').replaceChildren(excluded);
  renderChart(false); updateStatus(); go('verify-section',true);
}
$('run').onclick = () => {
  if (!catalog || !validateScope()) { $('scopeError').focus(); return; }
  invalidate(); const ticket = evidenceGate.current(), requested = settings();
  go('observe'); announce(document.body.dataset.mode === 'snapshot' ? 'Opening the saved NASA observations. This is not a live request…' : 'Contacting NASA POWER and validating monthly observations…', 'loading'); $('chart').classList.add('loading');
  return busy('run', async () => {
    try {
      const loaded = await (await api('investigate', requested)).json(); if (!evidenceGate.isCurrent(ticket)) return;
      result = loaded; text('chartTitle', `${loaded.settings.city} · ${catalog.variables[loaded.settings.variable].label}`);
      text('source', `${loaded.settings.start}–${loaded.settings.end} · ${loaded.annual.length} complete years · retrieved ${new Date(loaded.retrieved_at).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'})} UTC`);
      text('dataBadge', document.body.dataset.mode === 'snapshot' ? 'Saved NASA record' : 'NASA response validated');
      $('verify').disabled = !loaded.stats; $('yearCursor').value = 0; renderChart(); renderTable(); updateStatus(); toast('Your observations are ready. Explore a year or describe the pattern.');
    } finally { if (evidenceGate.isCurrent(ticket)) $('chart').classList.remove('loading'); }
  }, error => { if (evidenceGate.isCurrent(ticket)) { announce(error,'error'); text('dataBadge','No data loaded'); toast(error); } });
};
function applyScope(p) {
  ['city','variable','start','end'].forEach(key => { $(key).value = p[key] ?? ''; }); invalidate();
}
$('interpret').onclick = () => {
  const ticket = evidenceGate.current(), question = $('question').value;
  message('parseMessage', 'Reading your question. No analysis will run automatically.');
  return busy('interpret', async () => { const parsed = await (await api('interpret',{question})).json(); if (!evidenceGate.isCurrent(ticket) || question !== $('question').value) return; applyScope(parsed.proposed); const unset = Object.entries(parsed.proposed).filter(([,v])=>v==null).map(([key])=>({city:'location',variable:'variable',start:'start year',end:'end year'}[key])); message('parseMessage', parsed.message + (unset.length ? ` Please choose: ${unset.join(', ')}.` : ' The proposed scope is ready for your confirmation.')); toast(unset.length ? 'Some fields need your review. Nothing has been analyzed.' : 'Question interpreted. Confirm the settings to investigate.'); }, error => message('parseMessage',error,true));
};
function starter(variable) {
  if (!catalog) return;
  const label = {T2M:'air temperature',PRECTOTCORR:'precipitation',RH2M:'relative humidity',WS10M:'wind speed'}[variable];
  $('question').value = `How has ${label} changed in Singapore between 2001 and 2025?`; $('city').value = 'Singapore'; $('variable').value = variable; $('start').value = 2001; $('end').value = 2025;
  invalidate(); message('parseMessage','Starting question selected. Review the scope, then confirm to load observations.'); go('ask');
}
$$('[data-topic],[data-question]').forEach(button => button.addEventListener('click',()=>starter(button.dataset.topic || button.dataset.question)));
['city','variable','start','end','question'].forEach(id => $(id).addEventListener(id === 'city' || id === 'variable' ? 'change' : 'input',invalidate));
$('yearCursor').addEventListener('input',()=>showYear($('yearCursor').value)); $('verify').onclick = renderEvidence;
$('toggleTable').onclick = () => { $('annualDetails').open = !$('annualDetails').open; $('toggleTable').setAttribute('aria-expanded',String($('annualDetails').open)); };
$('annualDetails').addEventListener('toggle',()=> $('toggleTable').setAttribute('aria-expanded',String($('annualDetails').open)));
$('template').onclick = () => { $('guide').hidden = !$('guide').hidden; $('template').setAttribute('aria-expanded',String(!$('guide').hidden)); };
function writingChanged() { writingGate.next(); abortRequests(['tutor','report']); hideFeedback(); updateStatus(); const value = $('conclusion').value.trim(); const count = value ? (value.match(/[\p{Script=Han}]|[^\s\p{Script=Han}]+/gu) || []).length : 0; text('wordCount',`${count} ${count === 1 ? 'word' : 'words / characters'}`); }
['conclusion','hypothesis','observation','reviewed','message'].forEach(id=>$(id).addEventListener('input',writingChanged));
async function tutor(target) {
  const ticket = evidenceGate.current(), draft = writingGate.current();
  const response = await (await api('tutor',writing())).json();
  if (!evidenceGate.isCurrent(ticket) || !writingGate.isCurrent(draft)) return;
  const answer = response.text + (response.verified_summary ? '\n\nVerified server summary: ' + response.verified_summary : '');
  const mode = response.mode === 'configuration' ? 'Settings suggestion' : response.mode?.startsWith('AI') ? 'AI advisory' : 'Prepared guidance';
  if (target === 'feedback') {
    text('feedbackText',answer); text('feedbackMode',mode); text('feedbackReason',UI.reason(response.reason)); $('feedbackPanel').hidden = false;
    message('feedbackStatus','Feedback is ready below. Your conclusion has not been changed.');
  } else { text('answer',answer); text('tutorMode',mode); text('tutorReason',UI.reason(response.reason)); }
  proposal = response.proposed || null; $('applyProposal').hidden = !proposal;
}
$('feedback').onclick = () => {
  message('feedbackStatus','Preparing feedback on this draft…'); $('feedbackPanel').hidden = true;
  return busy('feedback',()=>tutor('feedback'),error=>message('feedbackStatus',error,true));
};
$('ask').onclick = () => { message('feedbackStatus',''); text('answer','Preparing guidance…'); text('tutorReason',''); return busy('ask',()=>tutor('ask'),error=>text('answer',error)); };
$$('[data-tutor]').forEach(button=>button.addEventListener('click',()=>{ $('message').value = button.dataset.tutor; writingChanged(); $('ask').click(); }));
$('applyProposal').onclick = () => { if (!proposal) return; const p = proposal; applyScope(p); message('parseMessage','Tutor proposal applied for review only. Confirm every field before investigating.'); go('ask'); $('city').focus({preventScroll:true}); };
$('export').onclick = () => busy('export',async()=>{
  if (!validateScope()) { go('ask'); toast('Review the investigation scope before exporting.'); return; }
  if (document.body.dataset.mode === 'snapshot') { window.ClimateSnapshot.printReport(writing(),result); return; }
  const ticket = evidenceGate.current(), draft = writingGate.current();
  const response = await api('report',writing()); if (!evidenceGate.isCurrent(ticket) || !writingGate.isCurrent(draft)) return;
  const blob = await response.blob(); if (!blob.type.includes('pdf')) throw Error('The server did not return a PDF. Try again.');
  const url = URL.createObjectURL(blob), a = document.createElement('a'); a.href = url; a.download = 'ClimateLens-investigation.pdf'; document.body.append(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(url),1000); toast('PDF downloaded. Your original writing is included.');
});
// Reveal each chapter once, with a safe visible default if observers are unavailable.
if (!reducedMotion && 'IntersectionObserver' in window) {
  document.documentElement.classList.add('js-motion');
  const observer = new IntersectionObserver(entries=>entries.forEach(entry=>{ if (entry.isIntersecting) { entry.target.classList.add('in'); observer.unobserve(entry.target); } }),{threshold:0.06,rootMargin:'0px 0px -25px 0px'});
  $$('.reveal').forEach(el=>observer.observe(el));
}
let motionFrame = 0, pointerX = 0, pointerY = 0, smoothX = 0, smoothY = 0, smoothProgress = 0;
const clamp = n => Math.max(0,Math.min(1,n));
function motion() {
  motionFrame = 0; const hero = $('home'), rect = hero.getBoundingClientRect();
  const raw = clamp(-rect.top / Math.max(1,hero.offsetHeight-innerHeight));
  smoothProgress = reducedMotion ? raw : smoothProgress + (raw-smoothProgress)*.13;
  smoothX += (pointerX-smoothX)*.08; smoothY += (pointerY-smoothY)*.08;
  const p = smoothProgress, fade = 1-clamp(p/.5), fly = clamp((p-.2)/.55), mobile = innerWidth <= 760;
  $$('.hero-copy,.hero-note,.island-coordinate').forEach(el=>{el.style.opacity=fade;el.style.visibility=fade>.01?'visible':'hidden';});
  const camera = document.querySelector('.island-camera');
  if (!reducedMotion) { camera.style.transform=`translateX(${-50+p*(mobile?5:14)}%) translate3d(${-smoothX*14}px,${p*30-smoothY*9}px,0) scale(${1+p*.31})`; document.querySelector('.hero-copy').style.transform=`translateY(${-p*42}px)`; }
  const copy = document.querySelector('.fly-copy'), topics = document.querySelector('.island-topics'); copy.style.opacity = fly; copy.style.visibility = fly>.01?'visible':'hidden'; topics.style.opacity=fly; topics.style.visibility=fly>.1?'visible':'hidden';
  const pageProgress=scrollY/Math.max(1,document.documentElement.scrollHeight-innerHeight); document.querySelector('.reading-progress i').style.transform=`scaleX(${clamp(pageProgress)})`;
  document.querySelector('.site-header').classList.toggle('scrolled',scrollY>45); document.querySelector('.chapter-rail').classList.toggle('visible',$('ask').getBoundingClientRect().top<innerHeight*.75);
  let active='ask'; ['ask','observe','verify-section','conclude'].forEach(id=>{if($(id).getBoundingClientRect().top<innerHeight*.5)active=id;}); $$('.chapter-rail a').forEach(a=>{ const on=a.dataset.chapter===active;a.classList.toggle('active',on);if(on)a.setAttribute('aria-current','step');else a.removeAttribute('aria-current'); });
  if (!reducedMotion && (Math.abs(raw-smoothProgress)>.001 || (rect.bottom>0 && (Math.abs(pointerX-smoothX)>.005 || Math.abs(pointerY-smoothY)>.005)))) motionFrame=requestAnimationFrame(motion);
}
function queueMotion(){if(!motionFrame)motionFrame=requestAnimationFrame(motion);}
addEventListener('scroll',queueMotion,{passive:true});addEventListener('resize',queueMotion);addEventListener('pointermove',event=>{if(reducedMotion||$('home').getBoundingClientRect().bottom<0)return;pointerX=event.clientX/innerWidth-.5;pointerY=event.clientY/innerHeight-.5;queueMotion();},{passive:true});
let chartCompact = innerWidth <= 760;
addEventListener('resize',()=>{ const compact=innerWidth<=760;if(compact!==chartCompact){chartCompact=compact;if(result)renderChart(false);} });
queueMotion();
(async()=>{
  try { catalog=await(await api('catalog')).json();
    $('city').replaceChildren(new Option('Choose location','')); Object.keys(catalog.cities).forEach(c=>$('city').add(new Option(c,c)));
    $('variable').replaceChildren(new Option('Choose variable','')); Object.entries(catalog.variables).forEach(([key,v])=>$('variable').add(new Option(v.label,key)));
    $('city').value='Singapore';$('variable').value='T2M';$('city').disabled=false;$('variable').disabled=false;$('run').disabled=false;
    $('start').max=$('end').max=new Date().getFullYear()-1; definition();
  } catch(error) { announce('Could not load the application: '+error.message,'error'); text('definition','The variable catalog is unavailable. Reload when the server is reachable.'); toast('Application unavailable. Check the server connection.'); }
})();
