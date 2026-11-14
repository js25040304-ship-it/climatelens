"""Owner 5: PDF export based on server-held evidence and student text."""
import io
import json
from xml.sax.saxutils import escape
from fastapi import APIRouter
from fastapi.responses import Response
from .schemas import Writing
from .state import result_for
from .evidence import explanation

router = APIRouter()

@router.post('/api/report')
def report(w:Writing):
 from reportlab.lib import colors
 from reportlab.lib.styles import getSampleStyleSheet
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
 from reportlab.graphics.shapes import Drawing,Line,String,Circle
 from reportlab.pdfbase import pdfmetrics
 from reportlab.pdfbase.cidfonts import UnicodeCIDFont
 pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
 r=result_for(w); s=r['stats'] if r else None
 status='Investigation completed' if s and w.conclusion.strip() and w.reviewed else 'Analysis completed — conclusion or review incomplete' if s else 'Incomplete evidence — analysis unavailable'
 buffer=io.BytesIO(); styles=getSampleStyleSheet()
 for style in styles.byName.values(): style.fontName='STSong-Light'
 blocks=[]
 def para(text,style='BodyText'): blocks.extend([Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style]),Spacer(1,9)])
 para('ClimateLens | Investigation report','Title'); para(status,'Heading2')
 para(w.question or 'Research question not provided'); para(json.dumps(w.settings.model_dump(),ensure_ascii=False))
 para('Initial hypothesis (student): '+(w.hypothesis or 'Skipped'))
 para('Observation notes (student): '+(w.observation or 'Not recorded'))
 if r and r['annual']:
  rows=r['annual']; vals=[p['value'] for p in rows]; low=min(vals); high=max(vals); span=high-low or 1
  draw=Drawing(450,190)
  def xy(i,v): return (40+390*i/max(1,len(rows)-1),35+125*(v-low)/span)
  draw.add(Line(40,35,430,35)); draw.add(Line(40,35,40,160))
  for i,p in enumerate(rows):
   x,y=xy(i,p['value']); draw.add(Circle(x,y,2,fillColor=colors.teal))
   if i: draw.add(Line(*xy(i-1,rows[i-1]['value']),x,y,strokeColor=colors.teal))
   if s and i: draw.add(Line(*xy(i-1,s['fitted'][i-1]),*xy(i,s['fitted'][i]),strokeColor=colors.darkorange))
  draw.add(String(40,15,str(rows[0]['year']))); draw.add(String(405,15,str(rows[-1]['year'])))
  draw.add(String(42,175,r['unit']+' | teal: observed; orange: fitted',fontSize=9)); draw.add(String(0,35,f'{low:.2g}',fontSize=8)); draw.add(String(0,155,f'{high:.2g}',fontSize=8)); blocks.append(draw)
 para('Verified analysis','Heading2'); para(explanation(r))
 if s:
  para(s['method'])
  for item in s['limitations']: para(item)
 para('Student-authored conclusion (not endorsed or graded)','Heading2'); para(w.conclusion or 'Not yet written')
 if r:
  para('NASA POWER source','Heading2'); para(r['source_url']); para('Retrieved: '+r['retrieved_at']); para(r['aggregation']); para('Excluded years: '+json.dumps(r['excluded_years']))
  table=Table([['Year','Annual value ('+r['unit']+')']]+[[str(p['year']),f"{p['value']:.4f}"] for p in r['annual']],repeatRows=1)
  table.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'STSong-Light'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2efeb')),('BOTTOMPADDING',(0,0),(-1,-1),6)])); blocks.append(table)
 else: para('Data source intended: NASA POWER. No verified observations or statistics were available for this report.')
 SimpleDocTemplate(buffer,title='ClimateLens investigation',leftMargin=48,rightMargin=48).build(blocks)
 return Response(buffer.getvalue(),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="ClimateLens-investigation.pdf"'})

