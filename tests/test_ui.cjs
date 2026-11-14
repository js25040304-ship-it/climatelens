const {test} = require('node:test');
const assert = require('node:assert/strict');
const UI = require('../app/static/ui-utils.js');
test('ordinary numbers use readable digits rather than scientific notation',()=>{
  assert.equal(UI.number(2350),'2,350');
  assert.equal(UI.number(-2350),'-2,350');
  assert.equal(UI.number(0.000000123),'0.000000123');
  assert.equal(UI.number(NaN),'—'); assert.equal(UI.number(-0),'0');
});
test('p-value display preserves the 0.05 decision boundary',()=>{
  for (const p of [0.049999,0.0499999999999,0.04999999999999999,0.05000000001,0.05,0.051]) {
    const display = UI.pValue(p); assert.equal(Number(display)<.05,p<.05);
    assert.ok(!/[eE]/.test(display));
  }
  assert.equal(UI.pValue(1.2e-10),'< 0.001');
  assert.equal(UI.pValue(0),'< 0.001'); assert.equal(UI.pValue(null),'—');
});
test('excluded years name months and explicitly avoid interpolation',()=>{
  assert.match(UI.excluded([{year:2012,missing_or_invalid_months:[2,7]}])[0],/2012.*Feb, Jul.*not interpolated/);
  assert.match(UI.excluded([])[0],/No years excluded/);
});
test('provider fallback reasons are user-facing and keep authentication details private',()=>{
  for(const code of ['no_key','timeout','auth','http_error','bad_response']) assert.ok(UI.reason(code).length>20);
  assert.match(UI.reason('timeout'),/timed out/); assert.equal(UI.reason(undefined),'');
});
test('invalid and ambiguous scopes cannot run',()=>{
  assert.notEqual(UI.scopeError({city:'',variable:'',start:NaN,end:NaN},2025),'');
  assert.notEqual(UI.scopeError({city:'Singapore',variable:'T2M',start:2020,end:2025},2025),'');
  assert.notEqual(UI.scopeError({city:'Singapore',variable:'T2M',start:2001,end:2026},2025),'');
  assert.equal(UI.scopeError({city:'Singapore',variable:'T2M',start:2001,end:2025},2025),'');
});
test('settings and writing revisions reject stale async results',async()=>{
  const evidence=UI.gate(),writing=UI.gate(); const old=evidence.current(),draft=writing.current();
  const pending=Promise.resolve().then(()=>evidence.isCurrent(old)); evidence.next();
  assert.equal(await pending,false); assert.equal(writing.isCurrent(draft),true);
  writing.next();assert.equal(writing.isCurrent(draft),false);
});

test('shared preview keeps archive years when a question requests 2001–2024', async () => {
  const {readFileSync} = require('node:fs');
  const {join} = require('node:path');
  const {runInNewContext} = require('node:vm');
  const record = {id: 'snapshot:singapore-T2M'};
  const snapshot = {
    catalog: {cities: {Singapore: {}}, variables: {T2M: {}}},
    records: {'Singapore|T2M': record},
  };
  const window = {};
  runInNewContext(
    readFileSync(join(__dirname, '../app/static/snapshot-preview.js'), 'utf8'),
    {
      window,
      Response,
      fetch: async () => ({ok: true, json: async () => snapshot}),
      document: {
        body: {dataset: {mode: 'snapshot'}, prepend() {}},
        createElement: () => ({}),
        getElementById: () => ({}),
        querySelector: () => ({}),
        querySelectorAll: () => [{}, {}],
      },
    },
  );
  const {proposed, message} = await (await window.ClimateSnapshot.request('interpret', {
    question: 'How has the temperature in Singapore changed between 2001 and 2024?',
  })).json();
  assert.match(message, /different period.*2001–2025/);
  assert.deepEqual(proposed, {city: 'Singapore', variable: 'T2M', start: 2001, end: 2025});
  assert.deepEqual(await (await window.ClimateSnapshot.request('investigate', proposed)).json(), record);
});
