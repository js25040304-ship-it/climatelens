"""Generate downloadable investigation reports."""
import io
import itertools
import math
from pathlib import Path
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from .data import VARIABLES
from .evidence import explanation, trend_unit
from .schemas import Report
from .state import RESULTS, result_for

ROOT = Path(__file__).resolve().parent
router = APIRouter()

def axis_ticks(low,high,target=5):
 """Round-number axis ticks covering [low, high] and plain labels (thousands separators, never scientific notation)."""
 low,high=min(low,high),max(low,high)
 if high-low<1e-12: pad=abs(low)*.05 or 1; low,high=low-pad,high+pad
 raw=(high-low)/(target-1); mag=10**math.floor(math.log10(raw)); step=next(m*mag for m in (1,2,2.5,5,10) if m*mag>=raw*(1-1e-9))
 digits=max(0,-math.floor(math.log10(step)+1e-9)); digits+=abs(round(step*10**digits)-step*10**digits)>1e-6
 ticks=[round(k*step,digits)+0. for k in range(math.floor(low/step+1e-9),math.ceil(high/step-1e-9)+1)]
 return ticks,[f'{t:,.{digits}f}' for t in ticks]
CJK_FONT='NotoSansSC'  # bundled app/fonts/NotoSansSC-Regular.ttf (OFL); embedded as a subset so phone viewers without Chinese fonts still show the text
def register_cjk_font():
 from reportlab.pdfbase import pdfmetrics
 from reportlab.pdfbase.ttfonts import TTFont
 if CJK_FONT not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont(CJK_FONT,str(ROOT/'fonts'/'NotoSansSC-Regular.ttf')))
def font_runs(text):
 """Escape student text for a Paragraph: WinAnsi characters stay in Helvetica, everything else (CJK, full-width forms) uses the embedded CJK font."""
 def latin(ch):
  try: ch.encode('cp1252'); return True
  except UnicodeEncodeError: return False
 return ''.join((lambda t: t if is_latin else '<font name="'+CJK_FONT+'">'+t+'</font>')(escape(''.join(run)).replace('\n','<br/>')) for is_latin,run in itertools.groupby(str(text),key=lambda ch: ch=='\n' or latin(ch)))
def trend_chart(r,s):
 """Annual observations (and the fitted line when inference exists) with labelled, readable axes."""
 from reportlab.lib import colors
 from reportlab.graphics.shapes import Drawing,Line,Circle,Group,String as Text
 def String(x,y,text,**kw): return Text(x,y,text,**{'fontName':'Helvetica',**kw})
 rows=r['annual']; years=[p['year'] for p in rows]; fitted=s['fitted'] if s else []
 ticks,labels=axis_ticks(min([p['value'] for p in rows]+fitted),max([p['value'] for p in rows]+fitted))
 L,B,R,T=70,48,450,196; draw=Drawing(460,236); grey=colors.HexColor('#c8cfcd')
 def X(year): return L+(R-L)*(year-years[0])/max(1,years[-1]-years[0])
 def Y(v): return B+(T-B)*(v-ticks[0])/(ticks[-1]-ticks[0])
 spec=VARIABLES.get(r['settings']['variable'],{}); setting=r['settings']
 draw.add(String(L,224,f"{setting['city']}: {spec.get('label',setting['variable'])}, {setting['start']}–{setting['end']}",fontName='Helvetica-Bold',fontSize=10))
 for t,label in zip(ticks,labels): draw.add(Line(L,Y(t),R,Y(t),strokeColor=grey,strokeWidth=.5)); draw.add(String(L-5,Y(t)-3,label,fontSize=8,textAnchor='end'))
 step=next(k for k in (1,2,5,10,20) if (years[-1]-years[0])/k<=8)
 for year in [y for y in range(years[0],years[-1]+1) if y%step==0 or y in (years[0],years[-1]) and (years[-1]-years[0])<=step]: draw.add(Line(X(year),B,X(year),B-3)); draw.add(String(X(year),B-13,str(year),fontSize=8,textAnchor='middle'))
 draw.add(Line(L,B,R,B)); draw.add(Line(L,B,L,T))
 draw.add(String((L+R)/2,B-30,'Year',fontSize=9,textAnchor='middle'))
 axis=Group(String(0,0,f"{spec.get('label',setting['variable'])} ({r['unit']})",fontSize=9,textAnchor='middle')); axis.transform=(0,1,-1,0,14,(B+T)/2); draw.add(axis)
 for i,p in enumerate(rows):
  if i and p['year']-rows[i-1]['year']==1: draw.add(Line(X(rows[i-1]['year']),Y(rows[i-1]['value']),X(p['year']),Y(p['value']),strokeColor=colors.teal,strokeWidth=.8))
  draw.add(Circle(X(p['year']),Y(p['value']),2,fillColor=colors.teal,strokeColor=colors.teal))
 if fitted: draw.add(Line(X(years[0]),Y(fitted[0]),X(years[-1]),Y(fitted[-1]),strokeColor=colors.darkorange,strokeWidth=1.5))
 draw.add(Circle(R-150,212,2.5,fillColor=colors.teal,strokeColor=colors.teal)); draw.add(String(R-143,209,'Observed annual value',fontSize=8))
 if fitted: draw.add(Line(R-155,200,R-145,200,strokeColor=colors.darkorange,strokeWidth=1.5)); draw.add(String(R-143,197,'Fitted linear trend (OLS)',fontSize=8))
 return draw

def comparison_for(primary, identifier):
 if identifier is None:
  return None
 secondary=RESULTS.get(identifier)
 if secondary is None:
  raise HTTPException(410,'The comparison has expired. Run the comparison again.')
 if not primary or not primary['stats'] or not secondary['stats']:
  raise HTTPException(409,'Both cities need valid trend evidence.')
 a,b=primary['settings'],secondary['settings']
 if a['city']==b['city'] or any(a[key]!=b[key] for key in ('variable','start','end')) or primary['unit']!=secondary['unit']:
  raise HTTPException(409,'Compare two distinct cities with the same indicator, units and requested period.')
 if [row['year'] for row in primary['annual']] != [row['year'] for row in secondary['annual']]:
  raise HTTPException(409,'Both cities must have the same complete years.')
 return secondary

@router.post('/api/report')
def report(w:Report):
 r=result_for(w)
 comparison=comparison_for(r,w.comparison_result_id)
 s=r['stats'] if r else None
 from reportlab.lib import colors
 from reportlab.lib.styles import getSampleStyleSheet
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
 register_cjk_font()
 import reportlab.platypus.paragraph as rlpara  # reportlab's line-start rules are Japanese-centric; add Chinese full-width punctuation (idempotent)
 if isinstance(getattr(rlpara,'ALL_CANNOT_START',None),str): rlpara.ALL_CANNOT_START+=''.join(c for c in '，；：！？、）】」』》〉' if c not in rlpara.ALL_CANNOT_START)
 status='Investigation completed' if s and w.conclusion.strip() and w.reviewed else 'Analysis completed — conclusion or review incomplete' if s else 'Incomplete evidence — analysis unavailable'
 buffer=io.BytesIO(); styles=getSampleStyleSheet(); styles['Heading2'].keepWithNext=1
 blocks=[]
 cjk=styles['BodyText'].clone('CJKBody',wordWrap='CJK')  # CJK line breaking keeps Chinese punctuation off line starts
 def para(text,style='BodyText'): markup=font_runs(text); blocks.extend([Paragraph(markup,cjk if style=='BodyText' and CJK_FONT in markup else styles[style])]+([] if style in ('Title','Heading2') else [Spacer(1,6)]))
 settings=w.settings.model_dump(); spec=VARIABLES.get(settings['variable'],{})
 para('ClimateLens | Investigation report','Title'); para(status,'Heading2')
 para('Research question (student): '+(w.question or 'Not provided')); para(f"City: {settings['city']}  |  Variable: {spec.get('label',settings['variable'])} ({settings['variable']})  |  Period: {settings['start']}–{settings['end']}")
 if w.question.strip():
  from .questions import parse_question
  proposed = parse_question(w.question)['proposed']
  if any(value is not None and value != settings[key] for key,value in proposed.items()):
   para('Scope note: the student question and selected settings differ. The verified analysis applies only to the city, variable and period shown above.')
 para('Initial hypothesis (student): '+(w.hypothesis or 'Skipped'))
 para('Observation notes (student): '+(w.observation or 'Not recorded'))
 if r and r['annual']: blocks.append(trend_chart(r,s))
 para('Verified analysis','Heading2'); para(explanation(r))
 if r and not s and r.get('analysis_error'): para('Why no trend inference: '+r['analysis_error'])
 if s:
  para(s['method'])
  for item in s['limitations']: para(item)
 if comparison:
  from reportlab.platypus import KeepTogether
  years=[row['year'] for row in r['annual']]
  unit=trend_unit(r['unit'])
  rows=[['City','Change per decade','95% confidence interval']]
  for record in (r,comparison):
   stats=record['stats']
   slope=stats['slope_decade']
   low,high=(value*10 for value in stats['ci95_year'])
   largest=max(abs(slope),abs(low),abs(high))
   digits=max(0,2-math.floor(math.log10(largest))) if largest else 0
   rows.append([record['settings']['city'],f'{slope+0.:,.{digits}f} {unit}',
                f'{low+0.:,.{digits}f} to {high+0.:,.{digits}f} {unit}'])
  table=Table(rows,hAlign='LEFT',style=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2efeb')),
                                        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')])
  heading_start=len(blocks)
  para('City trend comparison','Heading2')
  para(f"{spec['label']} | {years[0]}–{years[-1]} | {len(years)} matching complete years")
  blocks.append(table)
  blocks[heading_start:]=[KeepTogether(blocks[heading_start:])]
  para('Each interval describes one city’s trend. To determine whether the trends differ statistically, test the difference between the slopes directly.')
  para('Comparison NASA POWER source: '+comparison['source_url'])
  if comparison.get('source_mode')=='archive': para('Comparison source mode: saved NASA POWER response.')
  para('Comparison data retrieved: '+comparison['retrieved_at'])
 para('Student-authored conclusion (not endorsed or graded)','Heading2'); para(w.conclusion or 'Not yet written')
 if r:
  para('NASA POWER source','Heading2')
  if r.get('source_mode')=='archive': para('Source mode: saved NASA POWER response.')
  para(r['source_url']); para('Retrieved: '+r['retrieved_at']); para('Annual aggregation: '+r['aggregation'])
  para('Excluded years: '+('; '.join(f"{e['year']} (missing or invalid months: {', '.join(map(str,e['missing_or_invalid_months']))})" for e in r['excluded_years']) or 'none'))
  class AnnualTable(Table):  # every piece re-applies the rule (header+3 rows before a break, 3 after); reportlab drops it on split pieces, which let a leftover gap take a lone row
   def split(self,aw,ah): self._rowSplitRange=(4,-3); return Table.split(self,aw,ah)
  table=AnnualTable([['Year','Annual value ('+r['unit']+')']]+[[str(p['year']),f"{p['value']:,.2f}"] for p in r['annual']],repeatRows=1)
  table.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Helvetica'),('ALIGN',(1,1),(1,-1),'RIGHT'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2efeb')),('BOTTOMPADDING',(0,0),(-1,-1),4)])); blocks.append(table)
 else: para('Data source intended: NASA POWER. No verified observations or statistics were available for this report.')
 def footer(canvas,doc): canvas.saveState(); canvas.setFont('Helvetica',8); canvas.drawRightString(doc.pagesize[0]-48,24,f'ClimateLens investigation report  ·  page {doc.page}'); canvas.restoreState()
 SimpleDocTemplate(buffer,title='ClimateLens investigation',leftMargin=48,rightMargin=48).build(blocks,onFirstPage=footer,onLaterPages=footer)
 return Response(buffer.getvalue(),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="ClimateLens-investigation.pdf"'})
