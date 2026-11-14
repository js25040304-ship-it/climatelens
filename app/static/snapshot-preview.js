/* Loaded only in the separately packaged, explicitly labelled archive preview. */
'use strict';
if (document.body.dataset.mode === 'snapshot') {
  const start = 2001, end = 2025;
  const bundle = fetch('/static/recorded-evidence.json').then(r => { if (!r.ok) throw Error('The saved NASA evidence could not be loaded.'); return r.json(); });
  const banner = document.createElement('div'); banner.className = 'preview-banner'; banner.textContent = 'SHARED PREVIEW · Saved NASA records captured 14 Nov 2026 · 2001–2025'; document.body.prepend(banner);
  ['start','end'].forEach(id => { document.getElementById(id).readOnly = true; document.getElementById(id).title = 'Archive: 2001–2025 only. Run the GitHub application for other periods.'; });
  document.querySelector('#export>span').textContent = 'Print / Save PDF';
  document.getElementById('dataLabel').textContent = 'Recorded NASA field record';
  document.querySelectorAll('.scope-card .field-help')[1].textContent = 'Saved records cover 2001–2025. Choose a city and variable; no live NASA request is made.';
  document.getElementById('draftNote').textContent = 'Archive preview: live NASA, external AI and server PDF export run in the GitHub application. Use Print / Save PDF here.';
  const response = value => new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
  window.ClimateSnapshot = {
    async request(path, data) {
      const b = await bundle;
      if (path === 'catalog') return response(b.catalog);
      if (path === 'investigate') {
        if (data.start !== start || data.end !== end) throw Error('The shared archive covers 2001–2025 only. Run the GitHub application for other periods.');
        const record = b.records[`${data.city}|${data.variable}`];
        if (!record) throw Error('No saved NASA record matches this scope.');
        return response(record);
      }
      if (path === 'interpret') {
        const q = data.question.toLowerCase(), cities = Object.keys(b.catalog.cities).filter(c => q.includes(c.toLowerCase()));
        const aliases = {T2M:['temperature','hot','warm','温度','热'],PRECTOTCORR:['rain','precipitation','降雨'],RH2M:['humidity','湿度'],WS10M:['wind','风速'],ALLSKY_SFC_SW_DWN:['solar','radiation','太阳','辐射']};
        const vars = Object.entries(aliases).filter(([,words])=>words.some(w=>q.includes(w))).map(([key])=>key), years = q.match(/\b(?:19|20)\d{2}\b/g)?.map(Number) || [];
        const differentPeriod = years.some(year => year !== start && year !== end);
        const message = differentPeriod
          ? 'Your question mentions a different period. The shared preview uses 2001–2025. Update the question to match, or run the full application to use other years.'
          : 'Review the proposed location and variable. The archive period is fixed at 2001–2025.';
        return response({proposed:{city:cities.length===1?cities[0]:null,variable:vars.length===1?vars[0]:null,start,end},message});
      }
      if (path === 'tutor') {
        const r = b.records[`${data.settings.city}|${data.settings.variable}`], current = r && data.result_id === r.id && data.settings.start === start && data.settings.end === end;
        let answer = 'Load matching observations before interpreting a trend. Your conclusion is your own; this preview does not assess or grade it.';
        if (current) {
          const s = r.stats, u = ClimateUI.unit(r.unit);
          answer = `The saved NASA record has ${s.n} complete years. Its recorded slope is ${ClimateUI.number(s.slope_decade)} ${u} per decade, with a 95% interval from ${ClimateUI.number(s.ci95_year[0]*10)} to ${ClimateUI.number(s.ci95_year[1]*10)} and p ${s.p_value<.001?'':'= '}${ClimateUI.pValue(s.p_value)}.\n\nAn interval describes uncertainty in the estimated slope. Statistical significance does not establish a cause or describe practical importance. Connect your explanation to the evidence and mention the grid-cell limitation. These prepared prompts do not evaluate the correctness of your writing.`;
        }
        return response({mode:'deterministic archive guidance',reason:'snapshot',text:answer});
      }
      throw Error('This action requires the FastAPI application from GitHub.');
    },
    printReport(writing, record) {
      document.getElementById('snapshotReport')?.remove();
      const report = document.createElement('article'); report.id = 'snapshotReport'; report.hidden = true;
      function add(tag,value) { const el=document.createElement(tag);el.textContent=value;report.append(el);return el; }
      add('h1','ClimateLens — saved NASA investigation');
      add('p','Archive preview. Saved real NASA data captured 14 Nov 2026. No live NASA or AI request was made. This is a browser printout, not the server-generated report.');
      add('h2','Scope'); add('p',`${writing.settings.city} · ${writing.settings.variable} · ${writing.settings.start}–${writing.settings.end}`);
      add('p','The evidence applies to the scope above. Review whether the student question matches it.');
      ['question','hypothesis','observation','conclusion'].forEach(key=>{add('h2',key[0].toUpperCase()+key.slice(1));add('p',writing[key]||'(Not written)');});
      add('p',`Status: ${record?.stats&&writing.reviewed&&writing.conclusion.trim()?'Evidence reviewed and conclusion written.':'Incomplete investigation.'}`);
      if(record) {
        add('h2','Recorded evidence'); const s=record.stats,u=ClimateUI.unit(record.unit);
        add('p',`Slope per decade: ${ClimateUI.number(s.slope_decade)} ${u}; 95% interval: ${ClimateUI.number(s.ci95_year[0]*10)} to ${ClimateUI.number(s.ci95_year[1]*10)} ${u}; p ${s.p_value<.001?'':'= '}${ClimateUI.pValue(s.p_value)}.`);
        add('p',s.method); s.limitations.forEach(v=>add('p',v)); ClimateUI.excluded(record.excluded_years).forEach(v=>add('p',v));
        const chart=document.querySelector('#chart svg');if(chart)report.append(chart.cloneNode(true));
        add('h2','Annual observations');const table=document.querySelector('#table table');if(table)report.append(table.cloneNode(true));
        add('p','NASA source: '+record.source_url);add('p','Retrieved: '+record.retrieved_at);add('p','Archive: '+record.archive_provenance.path);add('p','Recorded result SHA-256: '+record.archive_provenance.sha256);
      } else add('p','No observations loaded. No trend can be inferred.');
      document.body.append(report); window.print();
    }
  };
}
