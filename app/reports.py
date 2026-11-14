"""Generate downloadable investigation reports."""
import io
import itertools
import math
from pathlib import Path
from xml.sax.saxutils import escape

from fastapi import APIRouter
from fastapi.responses import Response

from .data import VARIABLES
from .evidence import explanation
from .schemas import Writing
from .state import result_for

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

@router.post('/api/report')
def report(w:Writing):
 from reportlab.lib import colors
 from reportlab.lib.styles import getSampleStyleSheet
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
 register_cjk_font()
 import reportlab.platypus.paragraph as rlpara  # reportlab's line-start rules are Japanese-centric; add Chinese full-width punctuation (idempotent)
 if isinstance(getattr(rlpara,'ALL_CANNOT_START',None),str): rlpara.ALL_CANNOT_START+=''.join(c for c in '，；：！？、）】」』》〉' if c not in rlpara.ALL_CANNOT_START)
 r=result_for(w); s=r['stats'] if r else None
 status='Investigation completed' if s and w.conclusion.strip() and w.reviewed else 'Analysis completed — conclusion or review incomplete' if s else 'Incomplete evidence — analysis unavailable'
 buffer=io.BytesIO(); styles=getSampleStyleSheet(); styles['Heading2'].keepWithNext=1
 blocks=[]
 cjk=styles['BodyText'].clone('CJKBody',wordWrap='CJK')  # CJK line breaking keeps Chinese punctuation off line starts
 def para(text,style='BodyText'): markup=font_runs(text); blocks.extend([Paragraph(markup,cjk if style=='BodyText' and CJK_FONT in markup else styles[style])]+([] if style in ('Title','Heading2') else [Spacer(1,6)]))
 settings=w.settings.model_dump(); spec=VARIABLES.get(settings['variable'],{})
 para('ClimateLens | Investigation report','Title'); para(status,'Heading2')
 para('Research question: '+(w.question or 'Not provided')); para(f"City: {settings['city']}  |  Variable: {spec.get('label',settings['variable'])} ({settings['variable']})  |  Period: {settings['start']}–{settings['end']}")
 para('Initial hypothesis (student): '+(w.hypothesis or 'Skipped'))
 para('Observation notes (student): '+(w.observation or 'Not recorded'))
 if r and r['annual']: blocks.append(trend_chart(r,s))
 para('Verified analysis','Heading2'); para(explanation(r))
 if r and not s and r.get('analysis_error'): para('Why no trend inference: '+r['analysis_error'])
 if s:
  para(s['method'])
  for item in s['limitations']: para(item)
 para('Student-authored conclusion (not endorsed or graded)','Heading2'); para(w.conclusion or 'Not yet written')
 if r:
  para('NASA POWER source','Heading2'); para(r['source_url']); para('Retrieved: '+r['retrieved_at']); para('Annual aggregation: '+r['aggregation'])
  para('Excluded years: '+('; '.join(f"{e['year']} (missing or invalid months: {', '.join(map(str,e['missing_or_invalid_months']))})" for e in r['excluded_years']) or 'none'))
  class AnnualTable(Table):  # every piece re-applies the rule (header+3 rows before a break, 3 after); reportlab drops it on split pieces, which let a leftover gap take a lone row
   def split(self,aw,ah): self._rowSplitRange=(4,-3); return Table.split(self,aw,ah)
  table=AnnualTable([['Year','Annual value ('+r['unit']+')']]+[[str(p['year']),f"{p['value']:,.2f}"] for p in r['annual']],repeatRows=1)
  table.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Helvetica'),('ALIGN',(1,1),(1,-1),'RIGHT'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2efeb')),('BOTTOMPADDING',(0,0),(-1,-1),4)])); blocks.append(table)
 else: para('Data source intended: NASA POWER. No verified observations or statistics were available for this report.')
 def footer(canvas,doc): canvas.saveState(); canvas.setFont('Helvetica',8); canvas.drawRightString(doc.pagesize[0]-48,24,f'ClimateLens investigation report  ·  page {doc.page}'); canvas.restoreState()
 SimpleDocTemplate(buffer,title='ClimateLens investigation',leftMargin=48,rightMargin=48).build(blocks,onFirstPage=footer,onLaterPages=footer)
 return Response(buffer.getvalue(),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="ClimateLens-investigation.pdf"'})
