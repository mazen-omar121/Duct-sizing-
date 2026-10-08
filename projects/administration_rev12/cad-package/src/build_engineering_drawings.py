"""Administration HVAC Rev11: revised routing, formed connections and I&C.
Run: python cad-package/src/build_engineering_drawings.py
Input airflows and selected duct sizes are retained from the Rev05 coordination basis.
"""
from pathlib import Path
from math import hypot,atan2,cos,sin,pi,ceil
import argparse,csv,json,copy
import fitz,ezdxf
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from ezdxf.enums import TextEntityAlignment
from duct_geometry import Network, pieces

BASE=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--output-dir',default=str(BASE.parent));args=ap.parse_args()
OUT=Path(args.output_dir);OUT.mkdir(parents=True,exist_ok=True)
MM=72/25.4;PW,PH=841,594;MH=19500
COL={'SA':'#239321','RA':'#1567BD','EA':'#B95A18','OA':'#408A95','FLOW':'#D33823','SYM':'#15251C','INST':'#703779','ARCH':'#B7B7B7','INK':'#171C20','DIM':'#74787B','NOTE':'#6C6C6C'}
LAYER={'SA':'M-SA-DUCT','RA':'M-RA-DUCT','EA':'M-EA-DUCT','OA':'M-OA-DUCT','FLOW':'M-AIR-FLOW','SYM':'M-DEVICE','INST':'M-INSTRUMENT','ARCH':'A-ARCHITECTURE','INK':'M-ANNOTATION','DIM':'M-DIMENSION','NOTE':'M-NOTES'}
FONT='Helvetica';BOLD='Helvetica-Bold'
MONOCHROME=False
DATA=json.loads((BASE/'inputs/Administration_design_basis.json').read_text())
ROOMS={r['id']:r for r in DATA['rooms']};ORDER=['02','05','04','08','06','07','09','03','01']
SHORT={'02':'ELECTRICAL PANEL','05':'OPERATOR CONSOLE','04':'MEETING','08':'TELECOM PANEL','06':'CORRIDOR','07':'BED / REST','09':'TOILETS','03':'KITCHEN','01':'CLEAN AGENT'}
def read_csv(n):return list(csv.DictReader((BASE/'schedules'/n).open()))
ROOF_MAIN=read_csv('Roof_main_basis.csv');RISERS=read_csv('Roof_risers.csv')
SECTIONS=read_csv('Duct_sections.csv');TERMINALS=read_csv('Terminals.csv');INSTRUMENTS=read_csv('Instruments.csv');COMPONENTS=read_csv('Components.csv');IO=read_csv('IO_points.csv')
BYSEC={r['tag']:r for r in SECTIONS}
def num(v):return float(v) if v not in ('','TBC',None) else None
def P(x,y):return x,MH-y
def size(r):return ('D'+r['diameter_mm']) if r.get('diameter_mm') else r['width_mm']+'x'+r['height_mm']
def pts(r):
 p=json.loads(r['points_mm']);out=[p[0]]
 for q in p[1:]:
  if hypot(q[0]-out[-1][0],q[1]-out[-1][1])>=10:out.append(q)
 return [P(*q) for q in out]

class Scene:
 def __init__(self,w=PW,h=PH,fontscale=1):self.w=w;self.h=h;self.ops=[];self.fontscale=fontscale
 def line(self,p,k='INK',lw=.25,dash=False):self.ops.append(('line',p,k,lw,dash))
 def poly(self,p,k='INK',lw=.25,fill=None,dash=False):self.ops.append(('poly',p,k,lw,fill,dash))
 def rect(self,x,y,w,h,k='INK',lw=.25,fill=None,dash=False):self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],k,lw,fill,dash)
 def circle(self,x,y,r,k='INK',lw=.25,fill=None):self.ops.append(('circle',x,y,r,k,lw,fill))
 def text(self,x,y,t,z=2.8,k='INK',bold=False,align='left',angle=0,mask=False):
  z*=self.fontscale
  if mask:
   lines=t.split('\n');ww=max(pdfmetrics.stringWidth(a,BOLD if bold else FONT,z) for a in lines)
   xx=x-ww/2 if align=='center' else x-ww if align=='right' else x
   self.rect(xx-z*.18,y-z*.94,ww+z*.36,z*(.98+1.3*(len(lines)-1)),'INK',0,'#FFFFFF')
   # Label masks must be distinguishable from un-stroked duct fills.
   self.ops[-1]=self.ops[-1][:-1]+('LABEL_MASK',)
  self.ops.append(('text',x,y,str(t),z,k,bold,align,angle))
 def para(self,x,y,t,w,z=2.7,k='INK',bold=False,lead=1.3):
  lines=[];a=''
  for word in t.split():
   b=(a+' '+word).strip()
   if a and pdfmetrics.stringWidth(b,BOLD if bold else FONT,z)>w:lines.append(a);a=word
   else:a=b
  if a:lines.append(a)
  for i,l in enumerate(lines):self.text(x,y+i*z*lead,l,z,k,bold)
  return len(lines)*z*lead
 def arrow(self,a,b,k='FLOW',lw=.22,z=2):
  self.line([a,b],k,lw);ang=atan2(b[1]-a[1],b[0]-a[0]);x,y=b
  self.poly([(x,y),(x-z*cos(ang)+.38*z*sin(ang),y-z*sin(ang)-.38*z*cos(ang)),(x-z*cos(ang)-.38*z*sin(ang),y-z*sin(ang)+.38*z*cos(ang))],k,lw,COL[k])
 def block(self,name,x,y,a=0,sx=1,sy=None,tag=''):
  self.ops.append(('block',name,x,y,a,sx,sy if sy is not None else sx,tag))
 def place(self,sub,x,y,den,b):self.ops.append(('place',sub,x,y,den,b))

BLOCKS={}
def blockdef(name):
 s=Scene(0,0);BLOCKS[name]=s;return s
# Device blocks use millimetre model dimensions. Plan terminal faces retain their input sizes.
s=blockdef('HVAC_SD_4WAY');s.rect(-300,-300,600,600,'SA',10,'#FFFFFF');s.rect(-110,-110,220,220,'FLOW',9)
for x,y in [(-300,-300),(300,-300),(300,300),(-300,300)]:s.line([(x,y),(x*.3667,y*.3667)],'FLOW',9)
for a,b in [((0,-150),(0,-440)),((0,150),(0,440)),((-150,0),(-440,0)),((150,0),(440,0))]:s.arrow(a,b,'FLOW',9,60)
s=blockdef('HVAC_RG');s.rect(-250,-250,500,500,'SYM',12,'#FFFFFF')
for y in [-150,-75,0,75,150]:
 for a,b in [(-190,-30),(30,190)]:s.line([(a,y),(b,y)],'FLOW',9)
s=blockdef('HVAC_EG');s.rect(-250,-250,500,500,'SYM',12,'#FFFFFF')
for y in [-150,-75,0,75,150]:s.line([(-190,y),(190,y)],'EA',9)
for name,motor,fire in [('HVAC_VCD',False,False),('HVAC_MD',True,False),('HVAC_MFD',True,True),('HVAC_RCD',True,False)]:
 s=blockdef(name);s.rect(-90,-300,180,600,'SYM',9,'#FFFFFF')
 if fire:
  s.line([(-55,-300),(-55,300)],'RA',24);s.line([(55,-300),(55,300)],'RA',24)
 else:s.line([(-80,275),(80,-275)],'RA',14)
 if motor:
  s.line([(0,-300),(0,-405)],'SYM',9);s.rect(-70,-545,140,140,'SYM',10,'#FFFFFF')
  s.text(0,-446,'M',100,'SYM',True,'center')
 s.line([(-130,-300),(-130,300)],'DIM',5)
s=blockdef('HVAC_EH');s.rect(-210,-300,420,600,'SYM',10,'#FFFFFF')
p=[(-165,-230)]
for i in range(7):p.append((-165+(i+1)*330/7,230 if i%2==0 else -230))
s.line(p,'FLOW',12)
s=blockdef('HVAC_FLEX');s.rect(-90,-300,180,600,'SYM',7,'#FFFFFF')
for x in [-45,0,45]:s.line([(x-18,-250),(x+18,-120),(x-18,20),(x+18,150),(x-18,250)],'DIM',9)
s=blockdef('HVAC_AD');s.rect(-90,-90,180,180,'SYM',9,'#FFFFFF');s.poly([(-65,0),(60,-62),(60,62)],'SYM',7,'#333C37')
s=blockdef('HVAC_FAN');s.circle(0,0,300,'SYM',14,'#FFFFFF')
for a in [0,2*pi/3,4*pi/3]:
 p=[(35*cos(a),35*sin(a)),(220*cos(a+.28),220*sin(a+.28)),(220*cos(a+.7),220*sin(a+.7))]
 s.poly(p,'SYM',10,'#F4F5F4')
s.circle(0,0,35,'SYM',10,'#FFFFFF')
for name,label in [('HVAC_TT','TT'),('HVAC_RHT','RH'),('HVAC_DPT','DP'),('HVAC_FIT','FT'),('HVAC_PDT','DP'),('HVAC_PDI','G'),('HVAC_VS','VS'),('HVAC_TSHH','HH'),('HVAC_AFS','AF')]:
 s=blockdef(name);s.circle(0,0,150,'INST',10,'#FFFFFF');s.text(0,40,label,90,'INST',True,'center')
s=blockdef('HVAC_FILTER');s.rect(-100,-300,200,600,'SYM',10,'#FFFFFF')
for y in [-230,-140,-50,40,130]:s.line([(-80,y),(80,y+70)],'DIM',9)
s=blockdef('HVAC_SILENCER');s.rect(-300,-300,600,600,'SYM',10,'#FFFFFF')
for y in [-140,0,140]:s.line([(-230,y),(230,y)],'DIM',24)

# Use actual isolated vector shapes from the provided CAD PDF export. These
# replace generic damper / heater glyphs, while Administration sizes stay intact.
REF=json.loads((BASE/'inputs/Reference_symbol_geometry.json').read_text())
for name,symbol in REF['symbols'].items():
 s=blockdef(name);s.rect(-symbol['core_axial_mm']/2,-300,symbol['core_axial_mm'],600,'SYM',0,'#FFFFFF')
 for op in symbol['ops']:
  if op['closed']:s.poly(op['points'],op['kind'],op['width'],COL[op['kind']] if op['fill'] else None)
  else:s.line(op['points'],op['kind'],op['width'])
 if name=='HVAC_MFD':s.text(0,-413,'M',75,'FLOW',False,'center')
# RCD uses the same motorized-damper graphic as the reference MD; tag defines duty.
BLOCKS['HVAC_RCD']=copy.deepcopy(BLOCKS['HVAC_MD'])
def core_axial(blk):
 return REF['symbols'].get('HVAC_MD' if blk=='HVAC_RCD' else blk,{}).get('core_axial_mm',180)

def rounded_path(points,width):
 out=[points[0]]
 for i,p in enumerate(points[1:-1],1):
  a=points[i-1];b=points[i+1];la=hypot(p[0]-a[0],p[1]-a[1]);lb=hypot(b[0]-p[0],b[1]-p[1]);u=((p[0]-a[0])/la,(p[1]-a[1])/la);v=((b[0]-p[0])/lb,(b[1]-p[1])/lb)
  turn=u[0]*v[1]-u[1]*v[0];r=min(width*.8,la*.4,lb*.4)
  if abs(turn)<.5 or r<width*.51:out.append(p);continue
  enter=(p[0]-u[0]*r,p[1]-u[1]*r);leave=(p[0]+v[0]*r,p[1]+v[1]*r);c=(enter[0]+v[0]*r,enter[1]+v[1]*r)
  a0=atan2(enter[1]-c[1],enter[0]-c[0]);out.append(enter)
  for j in range(1,13):
   angle=a0+(pi/2 if turn>0 else -pi/2)*j/12;out.append((c[0]+r*cos(angle),c[1]+r*sin(angle)))
 out.append(points[-1]);return out
def duct(sc,points,width,k='SA',round_duct=False,arrows=True):
 pp=rounded_path(points,width) if not round_duct else points
 ns=[]
 for a,b in zip(pp,pp[1:]):
  L=hypot(b[0]-a[0],b[1]-a[1]);ns.append((-(b[1]-a[1])/L,(b[0]-a[0])/L))
 sides=[]
 for sign in [1,-1]:
  edge=[]
  for i,p in enumerate(pp):
   n=ns[0] if i==0 else ns[-1] if i==len(pp)-1 else (ns[i-1][0]+ns[i][0],ns[i-1][1]+ns[i][1])
   mag=hypot(*n);n=(n[0]/mag,n[1]/mag);div=n[0]*ns[min(i,len(ns)-1)][0]+n[1]*ns[min(i,len(ns)-1)][1]
   edge.append((p[0]+sign*width*.5*n[0]/div,p[1]+sign*width*.5*n[1]/div))
  sides.append(edge)
 # White fill provides conventional crossing separation, with both clear-width outlines.
 sc.poly(sides[0]+sides[1][::-1],k,10 if round_duct else 13,'#FFFFFF')
 if arrows:
  for a,b in zip(points,points[1:]):
   L=hypot(b[0]-a[0],b[1]-a[1])
   if L>=900:
    aa=(a[0]+.25*(b[0]-a[0]),a[1]+.25*(b[1]-a[1]));bb=(a[0]+.36*(b[0]-a[0]),a[1]+.36*(b[1]-a[1]));sc.arrow(aa,bb,'FLOW',10,80)
def transition(sc,p,a,b,k,vertical=False):
 L=350;rr=[(-L/2,-a/2),(L/2,-b/2),(L/2,b/2),(-L/2,a/2)]
 if vertical:rr=[(-y,x) for x,y in rr]
 sc.poly([(p[0]+x,p[1]+y) for x,y in rr],k,13,'#FFFFFF')

def plot_fill(fill):
 if not MONOCHROME:return HexColor(fill)
 rgb=[int(fill[i:i+2],16) for i in [1,3,5]]
 gray=round(sum(rgb)/3) if min(rgb)>=200 else 0
 return HexColor('#'+f'{gray:02x}'*3)

def _pdf_ops(c,ops):
 for op in ops:
  t=op[0]
  if t=='dimension':
   _pdf_ops(c,op[-1]);continue
  if t in ['line','poly']:
   p,k,lw=op[1:4];fill=op[4] if t=='poly' else None;dash=op[5] if t=='poly' else op[4]
   c.setStrokeColor(HexColor(COL[k]));c.setLineWidth(lw);c.setDash([max(lw*6,2),max(lw*4,1)] if dash else [])
   q=c.beginPath();q.moveTo(*p[0])
   for x,y in p[1:]:q.lineTo(x,y)
   if t=='poly':q.close()
   if fill:c.setFillColor(plot_fill(fill))
   c.drawPath(q,stroke=int(lw>0),fill=int(bool(fill)))
  elif t=='circle':
   _,x,y,r,k,lw,fill=op;c.setStrokeColor(HexColor(COL[k]));c.setLineWidth(lw);c.setDash([])
   if fill:c.setFillColor(plot_fill(fill))
   c.circle(x,y,r,stroke=1,fill=int(bool(fill)))
  elif t=='text':
   _,x,y,s,z,k,bold,align,ang=op;c.saveState();c.translate(x,y);c.scale(1,-1);c.rotate(ang);c.setFillColor(HexColor(COL[k]));c.setFont(BOLD if bold else FONT,z)
   for i,l in enumerate(s.split('\n')):getattr(c,{'left':'drawString','right':'drawRightString','center':'drawCentredString'}[align])(0,-i*z*1.3,l)
   c.restoreState()
  elif t=='block':
   _,name,x,y,a,sx,sy,tag=op;c.saveState();c.translate(x,y);c.rotate(a);c.scale(sx,sy);_pdf_ops(c,BLOCKS[name].ops);c.restoreState()
  elif t=='place':
   _,s,x,y,den,b=op;c.saveState();c.translate(x,y);c.scale(1/den,1/den);q=c.beginPath();q.rect(0,0,b[2]-b[0],b[3]-b[1]);c.clipPath(q,stroke=0,fill=0);c.translate(-b[0],-b[1]);_pdf_ops(c,s.ops);c.restoreState()
def export_pdf(sheets,monochrome=False):
 global MONOCHROME
 MONOCHROME=monochrome
 name='Administration_Detailed_HVAC_Duct_Flow_Diagram_Monochrome.pdf' if monochrome else 'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf'
 c=canvas.Canvas(str(OUT/name),pagesize=(PW*MM,PH*MM));c.setTitle('Administration HVAC - Engineering Duct Drawings Rev12');c.setAuthor('Administration HVAC - coordination design')
 for s in sheets:
  c.saveState();c.translate(0,PH*MM);c.scale(MM,-MM);_pdf_ops(c,s.ops);c.restoreState();c.showPage()
 c.save()
 MONOCHROME=False
def dxf_ops(target,ops,h,mask=True):
 def p(pt):return pt[0],h-pt[1]
 for op in ops:
  t=op[0]
  if t=='place':continue
  if t=='dimension':
   _,a,b,base,angle,z,display=op
   target.add_linear_dim(base=p(base),p1=p(a),p2=p(b),angle=angle,dimstyle='HVAC-DIM',dxfattribs={'layer':'M-DIMENSION'},override={'dimtxt':z,'dimasz':z*.7,'dimexo':z*.4,'dimexe':z*.6,'dimgap':z*.5}).render()
   continue
  if t=='block':
   _,name,x,y,a,sx,sy,tag=op
   e=target.add_blockref(name,p((x,y)),dxfattribs={'xscale':sx,'yscale':sy,'rotation':-a,'layer':'M-DEVICE'})
   if tag:e.add_attrib('TAG',tag,insert=p((x,y)),dxfattribs={'height':100,'flags':1})
   continue
  k=op[2] if t in ['line','poly'] else op[4] if t=='circle' else op[5];attrs={'layer':LAYER[k]}
  if t in ['line','poly','circle']:
   lw=op[3] if t in ['line','poly'] else op[5]
   if lw>0:
    paper_lw=lw if h==PH else lw/50
    attrs['lineweight']=min([9,13,18,25,35,50,70],key=lambda v:abs(v-paper_lw*100))
  if t=='line':
   if op[4]:attrs['linetype']='DASHED'
   if op[4] and h==PH:attrs['ltscale']=.01
   for a,b in zip(op[1],op[1][1:]):target.add_line(p(a),p(b),dxfattribs=attrs)
  elif t=='poly':
   if op[5]:attrs['linetype']='DASHED'
   if op[5] and h==PH:attrs['ltscale']=.01
   if op[4]=='#FFFFFF' and mask:target.add_wipeout([p(a) for a in op[1]],dxfattribs={'layer':'M-MASK'})
   elif op[4]:
    hatch=target.add_hatch(color=256,dxfattribs=attrs)
    hatch.paths.add_polyline_path([p(a) for a in op[1]],is_closed=True)
   if op[3]>0:target.add_lwpolyline([p(a) for a in op[1]],close=True,dxfattribs=attrs)
  elif t=='circle':
   if op[6]=='#FFFFFF' and mask:
    target.add_wipeout([p((op[1]+op[3]*cos(i*2*pi/32),op[2]+op[3]*sin(i*2*pi/32))) for i in range(32)],dxfattribs={'layer':'M-MASK'})
   target.add_circle(p((op[1],op[2])),op[3],dxfattribs=attrs)
  elif t=='text':
   _,x,y,txt,z,k,bold,align,ang=op
   for i,a in enumerate(txt.split('\n')):
    e=target.add_text(a,dxfattribs={**attrs,'height':z,'rotation':ang,'style':'HVAC-BOLD' if bold else 'HVAC'})
    e.set_placement(p((x,y+i*z*1.3)),align={'left':TextEntityAlignment.LEFT,'right':TextEntityAlignment.RIGHT,'center':TextEntityAlignment.CENTER}[align])
def export_cad(sheets,models):
 d=ezdxf.new('R2013');d.units=ezdxf.units.MM;d.header['$MEASUREMENT']=1
 d.header['$LWDISPLAY']=1
 d.header['$LTSCALE']=1
 d.dimstyles.new('HVAC-DIM',dxfattribs={'dimtxsty':'Standard','dimdec':0,'dimzin':8})
 d.styles.new('HVAC',dxfattribs={'font':'arial.ttf'})
 d.styles.new('HVAC-BOLD',dxfattribs={'font':'arialbd.ttf'})
 if 'DASHED' not in d.linetypes:d.linetypes.new('DASHED',dxfattribs={'pattern':[70,42,-28]})
 for k,v in LAYER.items():d.layers.new(v,dxfattribs={'true_color':int(COL[k][1:],16),'lineweight':{'ARCH':9,'DIM':13,'NOTE':13,'INST':18,'FLOW':18,'INK':25,'SYM':25}.get(k,35)})
 d.layers.new('M-MASK',dxfattribs={'lineweight':0})
 d.set_raster_variables(frame=0,quality=1,units='mm')
 d.layers.new('VIEWPORT',dxfattribs={'plot':False})
 for n,s in BLOCKS.items():dxf_ops(d.blocks.new(n),s.ops,0)
 offsets={};m=d.modelspace()
 for i,(n,s) in enumerate(models.items()):
  # Service-specific models are independent editable blocks in model space.
  modelblock=d.blocks.new('PLAN_'+n);dxf_ops(modelblock,s.ops,MH)
  m.add_blockref('PLAN_'+n,(i*27000,0));offsets[id(s)]=i*27000
 for i,s in enumerate(sheets,1):
  l=d.layouts.new(f'D{i:03d}_A1');l.page_setup(size=(PW,PH),margins=(0,0,0,0),units='mm');dxf_ops(l,s.ops,PH)
  for op in s.ops:
   if op[0]!='place':continue
   _,model,x,y,den,b=op;w=(b[2]-b[0])/den;hh=(b[3]-b[1])/den
   l.add_viewport(center=(x+w/2,PH-y-hh/2),size=(w,hh),view_center_point=(offsets[id(model)]+(b[0]+b[2])/2,MH-(b[1]+b[3])/2),view_height=b[3]-b[1],dxfattribs={'layer':'VIEWPORT'})
 d.set_modelspace_vport(height=23500,center=(11000,9500));d.saveas(OUT/'Administration_HVAC_Detailed_Layout.dxf')

def paper_frame(title,idx,total=32,scale='NTS'):
 s=Scene();s.rect(10,10,821,574,'INK',.4);s.text(18,23,'ADMINISTRATION BUILDING - '+title,4.2,'INK',True);s.line([(18,29),(823,29)],'INK',.3)
 s.line([(10,544),(831,544)],'INK',.45)
 for x in [252,628,737]:s.line([(x,544),(x,584)],'INK',.25)
 s.text(17,552,'TAQA TRANSMISSION',3.2,'INK',True);s.text(17,560,'N-19082-RO-012  |  PUMPING STATION STANDARDIZATION',2.5);s.text(17,568,'ADMINISTRATION HVAC',3,'INK',True);s.text(17,578,'DESIGN BASIS: C-H-SS-001 Rev0 / HAP REFERENCE',2.3,'NOTE')
 s.text(259,552,'DRAWING TITLE',2.2,'NOTE');s.text(259,561,title,3.8,'INK',True);s.text(259,578,'FOR COORDINATION  |  CHECKED / APPROVED: PENDING',2.7,'NOTE')
 s.text(636,552,'DRAWING NUMBER',2.2,'NOTE');s.text(636,563,f'ADM-HVAC-D-{idx:03d}',3.2,'INK',True);s.text(636,578,'SCALE: '+scale+' AT A1',2.5)
 s.text(745,552,'REVISION',2.2,'NOTE');s.text(745,561,'12',4,'INK',True);s.text(745,571,'08 OCT 2026',2.5);s.text(745,580,f'SHEET {idx} OF {total}',2.3)
 return s
def table(s,x,y,w,heads,rows,ratios=None,z=2.6,rh=10):
 ratios=ratios or [1]*len(heads);xx=[x]
 for r in ratios:xx.append(xx[-1]+w*r/sum(ratios))
 s.rect(x,y,w,10,'INK',.25,'#F4F4F4')
 for j,t in enumerate(heads):s.para(xx[j]+1.5,y+3.5,t,xx[j+1]-xx[j]-3,z,'INK',True,1.15)
 yy=y+10
 for row in rows:
  for j,t in enumerate(row):s.para(xx[j]+1.5,yy+3.7,str(t),xx[j+1]-xx[j]-3,z,'INK',False,1.15)
  s.line([(x,yy+rh),(x+w,yy+rh)],'DIM',.12);yy+=rh
 return yy
def section_heading(s,x,y,t,w):s.text(x,y,t,3.1,'INK',True);s.line([(x,y+3),(x+w,y+3)],'INK',.25)
def text_bounds(op):
 _,x,y,t,z,k,bold,align,ang=op;lines=t.split('\n')
 w=max(pdfmetrics.stringWidth(q,BOLD if bold else FONT,z) for q in lines)
 left=-w/2 if align=='center' else -w if align=='right' else 0
 pp=[];a=ang*pi/180
 for u,v in [(left,-.23*z-(len(lines)-1)*z*1.3),(left+w,-.23*z-(len(lines)-1)*z*1.3),(left+w,z),(left,z)]:
  pp.append((x+u*cos(a)-v*sin(a),y-u*sin(a)-v*cos(a)))
 return min(p[0] for p in pp),min(p[1] for p in pp),max(p[0] for p in pp),max(p[1] for p in pp)
def view(s,model,x,y,den,bw):
 b=(bw[0],MH-bw[3],bw[2],MH-bw[1]);v=Scene(model.w,model.h,model.fontscale)
 # Crop duct geometry at a match line, but never print half a label. Each
 # viewport model is also retained as its own editable CAD block.
 for op in model.ops:
  if op[0]=='text':
   bb=text_bounds(op)
   if not (bb[0]>=b[0] and bb[1]>=b[1] and bb[2]<=b[2] and bb[3]<=b[3]):
    if v.ops and v.ops[-1][0]=='poly' and v.ops[-1][5]=='LABEL_MASK':v.ops.pop()
    continue
  v.ops.append(op)
 base=next(n for n,q in MODELS.items() if q is model)
 MODELS[base+'_D'+str(len(SHEETS)+1).zfill(3)]=v;s.place(v,x,y,den,b)
 return (bw[2]-bw[0])/den,(bw[3]-bw[1])/den
def note_footer(s,txt):s.para(18,530,txt,805,2.4,'NOTE')

def architecture(sc):
 page=fitz.open(BASE/'inputs/ADMIN_BUILDING_LAYOUT.pdf')[0];x0,y0,scale=342.12,132.17,20000/2184
 def f(p):return (p.x-x0)*scale,(p.y-y0)*scale
 for a in page.get_drawings():
  r=a['rect']
  if r.x0<330 or r.x1>2540 or r.y0<120 or r.y1>2275:continue
  for e in a['items']:
   if e[0]=='l':sc.line([f(e[1]),f(e[2])],'ARCH',5)
   elif e[0]=='re':sc.poly([f(e[1].tl),f(e[1].tr),f(e[1].br),f(e[1].bl)],'ARCH',5)
   elif e[0]=='c':
    a,b,c,d=e[1:];pp=[]
    for j in range(9):
     t=j/8;u=1-t;pp.append(f(fitz.Point(u**3*a.x+3*u*u*t*b.x+3*u*t*t*c.x+t**3*d.x,u**3*a.y+3*u*u*t*b.y+3*u*t*t*c.y+t**3*d.y)))
    sc.line(pp,'ARCH',5)

ROOM_POS={'02':(4350,19100),'05':(14600,19200),'04':(1900,7700),'08':(8700,7900),'06':(500,8600),'07':(13500,4500),'09':(12800,7800),'03':(18900,7800),'01':(18900,4300)}
BOX_POS={'SA':{'02':(5600,15400),'05':(16200,15300),'04':(350,5450),'08':(9300,5800),'07':(12500,900),'03':(18300,5100),'01':(17400,2200)},'RA':{'02':(5900,14800),'05':(16200,13600),'04':(350,5550),'08':(6500,3000),'07':(12600,2500)}}
TERM_OFF={}
for t in TERMINALS:
 tag=t['tag'];air=t['air_type'];rid=t['room'];x=num(t['x_mm']);y=num(t['y_mm'])
 dy=620 if air=='SA' else -650
 if rid=='08':dy=-650 if air=='SA' else 620
 if rid in ['07','03'] and air=='SA':dy=-650
 if air=='EA':dy=-650
 TERM_OFF[tag]=(0,dy)
TERM_OFF.update({'SD-06-02':(1100,450),'SD-08-05':(0,-600),'SD-08-06':(0,-600),'RG-08-05':(-200,850),'RG-08-06':(100,850)})

COORDINATION_BASIS=json.loads((BASE/'inputs/Coordination_basis.json').read_text())
NETWORK=Network(SECTIONS,MH,COORDINATION_BASIS)
GEOMETRY_QA=NETWORK.validate()
def write_register(name,rows):
 with (BASE/'schedules'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['tag','upper','lower','x_mm','y_mm','status']);w.writeheader();w.writerows(rows)
write_register('Transitions_and_takeoffs.csv',NETWORK.register())
write_register('Crossing_register.csv',NETWORK.crossing_register())
write_register('Formed_junctions.csv',NETWORK.formed_junctions)
FITTINGS=[]
for r in SECTIONS:
 pp=json.loads(r['points_mm'])
 for i,(a,q,b) in enumerate(zip(pp,pp[1:],pp[2:]),1):
  if abs((q[0]-a[0])*(b[1]-q[1])-(q[1]-a[1])*(b[0]-q[0]))<1:continue
  FITTINGS.append({'tag':f"F-{r['tag']}-B{i:02d}",'section':r['tag'],'type':'Radius / vaned elbow - see actual plan envelope','x_mm':q[0],'y_mm':q[1],'loss_K':'TBC selected fitting','basis':'Rev11 route vertex; selected radius / turning vanes and vertical development require approval'})
for t in NETWORK.transitions:
 FITTINGS.append({'tag':t['tag'],'section':t['owner'],'type':t['type'],
                  'x_mm':round((t['start'][0]+t['finish'][0])/2,1),
                  'y_mm':round(MH-(t['start'][1]+t['finish'][1])/2,1),
                  'loss_K':'TBC selected fitting',
                  'basis':f"Rev11 replacement profile; proposed axial length {t['length_mm']} mm; clear W x H / D per sections; fitting K and fabrication development pending"})
for tag in ['SA-B06','RA-B06']:
 q=NETWORK.original[tag][0 if tag.startswith('SA') else -1]
 FITTINGS.append({'tag':'TR-'+tag,'section':tag,'type':'Formed straight branch take-off',
                  'x_mm':q[0],'y_mm':MH-q[1],'loss_K':'TBC selected fitting',
                  'basis':'Straight common station for corridor devices; selected fitting / access and OEM face-to-face dimensions pending'})
write_register('Fittings.csv',FITTINGS)

STATIONS=[]
def station(air,rid,blk,xy,ang,ww,tg):
 STATIONS.append({'air':air,'room':rid,'block':blk,'xy':xy,'angle':ang,'width':ww,'tag':tg,'mirror':-1 if tg=='FSD-S05' else 1})
def inline_body(xy,angle,ww,axial):
 u=(cos(angle*pi/180),sin(angle*pi/180));n=(-u[1],u[0]);x,y=xy
 return Polygon([(x+aa*u[0]+bb*n[0],y+aa*u[1]+bb*n[1]) for aa,bb in [(-axial,-ww*.495),(axial,-ww*.495),(axial,ww*.495),(-axial,ww*.495)]])

def locate_branch_devices(air,rid):
 sec=air+'-B'+rid;r=BYSEC[sec];ww=num(r['width_mm']);pp=pts(r)
 poly=NETWORK.polygons[sec];envelope=NETWORK.envelopes[air]
 total_length=sum(hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(pp,pp[1:]))
 # Reserve a proposed straight separation from the vertical-drop elbow.
 # This is based on duct depth, not transverse plan width; selected elbow
 # development and device face-to-face lengths still require OEM approval.
 riser_clearance=max(200,float(r['height_mm'])*.75)
 sequence=[('HVAC_VCD','VCD-S'+rid),('HVAC_MFD','FSD-S'+rid)] if air=='SA' else [('HVAC_RCD','RCD-R'+rid),('HVAC_MFD','FSD-R'+rid)]
 if air=='SA' and rid in ['04','05','06','07','03']:sequence.append(('HVAC_EH','EH-'+rid))
 cursor=0;previous_half=0;placed=[]
 for blk,tg in sequence:
  half=core_axial(blk)/2+5
  spacing=40 if (air,rid) in [('RA','06'),('RA','04'),('RA','02'),('SA','02'),('RA','08')] else 100
  lower=cursor+previous_half+half+spacing if placed else 0
  candidates=[];travelled=0
  for a,b in zip(pp,pp[1:]):
   length=hypot(b[0]-a[0],b[1]-a[1]);u=((b[0]-a[0])/length,(b[1]-a[1])/length);ang=atan2(u[1],u[0])*180/pi
   for dist in range(10,int(length),10):
    distance=travelled+dist
    if distance<lower:continue
    if air=='SA' and distance-half<riser_clearance:continue
    if air=='RA' and total_length-distance-half<riser_clearance:continue
    xy=(a[0]+dist*u[0],a[1]+dist*u[1]);body=inline_body(xy,ang,ww,half)
    if not poly.buffer(.2).covers(body):continue
    # Keep another outlet face out of the device station projection. This
    # prevents an apparent false connection to a neighbouring diffuser.
    if any(body.buffer(90).intersects(box(num(t['x_mm'])-num(t['face_w_mm'])/2,MH-num(t['y_mm'])-num(t['face_h_mm'])/2,num(t['x_mm'])+num(t['face_w_mm'])/2,MH-num(t['y_mm'])+num(t['face_h_mm'])/2)) for t in TERMINALS):continue
    n=(-u[1],u[0]);edgepoints=[Point(xy[0]+du*u[0]+sign*ww/2*n[0],xy[1]+du*u[1]+sign*ww/2*n[1]) for du in [-half,0,half] for sign in [-1,1]]
    if any(envelope.boundary.distance(q)>1 for q in edgepoints):continue
    if any(body.intersection(c['_region'].buffer(50)).area>1 for c in NETWORK.crossings if sec in (c['upper_sections']+' / '+c['lower_sections']).split(' / ')):continue
    candidates.append((distance,xy,ang))
   travelled+=length
  assert candidates,(tg,'No clear straight branch station; revise routing rather than overlay device on a junction')
  cursor,xy,ang=min(candidates,key=lambda x:x[0]);previous_half=half
  station(air,rid,blk,xy,ang,ww,tg);placed.append((blk,xy,ang))
  if blk in ['HVAC_VCD','HVAC_RCD','HVAC_EH']:
   u=(cos(ang*pi/180),sin(ang*pi/180));n=(-u[1],u[0]);axy=(xy[0]+n[0]*ww/2,xy[1]+n[1]*ww/2)
   ad=('AD-H' if blk=='HVAC_EH' else 'AD-'+('S' if air=='SA' else 'R'))+rid
   station(air,rid,'HVAC_AD',axy,ang,ww,ad)

from shapely.geometry import Point,Polygon,box
for rid in ORDER:
 locate_branch_devices('SA',rid)
 if 'RA-B'+rid in BYSEC:locate_branch_devices('RA',rid)
# Common heater/access belongs to the proposed weather-protected roof plant, D-008.
# Verify the inline symbol BODY, excluding external motors, is inside the
# associated branch. This catches devices parked on radius bends / outside it.
from shapely.geometry import Point,Polygon,box
DEVICE_QA=[]
for q in STATIONS:
 if q['room']=='COM':continue
 sec=q['air']+'-B'+q['room'];poly=NETWORK.polygons[sec];x,y=q['xy']
 if q['block']=='HVAC_AD':
  assert poly.boundary.distance(Point(x,y))<2,(q['tag'],'access door is not on duct wall',poly.boundary.distance(Point(x,y)))
 else:
  axial=core_axial(q['block'])/2
  u=(cos(q['angle']*pi/180),sin(q['angle']*pi/180));n=(-u[1],u[0]);half=q['width']*.495
  body=Polygon([(x+aa*u[0]+bb*n[0],y+aa*u[1]+bb*n[1]) for aa,bb in [(-axial,-half),(axial,-half),(axial,half),(-axial,half)]])
  assert poly.buffer(1).covers(body),(q['tag'],'device body outside associated duct',body.difference(poly).area)
 DEVICE_QA.append(q['tag'])
write_register('Device_locations.csv',[{'tag':q['tag'],'service':q['air'],'room':q['room'],'x_mm':round(q['xy'][0],1),'y_mm':round(MH-q['xy'][1],1),'rotation_deg':round(-q['angle'],1),'symbol_actuator_side':'opposite' if q['mirror']==-1 else 'default','status':'Proposed indoor bare BOD +3.400 m; access envelope / OEM clearance TBC'} for q in STATIONS]+[{'tag':'AD-HCOM-01','service':'SA','room':'COM','x_mm':'TBC','y_mm':'TBC','rotation_deg':'TBC','symbol_actuator_side':'TBC','status':'Proposed roof common heater access, D-008 functional only; roof coordinates / weather enclosure / OEM clearance TBC'}])

def restore_device_walls(sc,q):
 if q['block']=='HVAC_AD':return
 xy,ww,blk=q['xy'],q['width'],q['block'];axial=core_axial(blk)/2+2
 u=(cos(q['angle']*pi/180),sin(q['angle']*pi/180));n=(-u[1],u[0])
 win=Polygon([(xy[0]+aa*u[0]+bb*n[0],xy[1]+aa*u[1]+bb*n[1]) for aa,bb in [(-axial,-ww/2-1),(axial,-ww/2-1),(axial,ww/2+1),(-axial,ww/2+1)]])
 for edge in pieces(NETWORK.envelopes[q['air']].boundary.intersection(win),'LineString'):sc.line(list(edge.coords),q['air'],13)

_LABEL_OBSTACLES={}
def annotate_station(sc,q,label,occupied,services=None,bounds=None,z=110):
 # Device tags have leaders and separate, collision-checked text rectangles.
 # Compact dampers must not produce a string of superimposed labels.
 from shapely.geometry import box
 xy,ww=q['xy'],q['width'];u=(cos(q['angle']*pi/180),sin(q['angle']*pi/180));n=(-u[1],u[0])
 services=set(services or [q['air']]);key=tuple(sorted(services))
 obstacles=[NETWORK.envelopes[a].buffer(35) for a in services] if key not in _LABEL_OBSTACLES else []
 for t in TERMINALS if key not in _LABEL_OBSTACLES else []:
  if t['air_type'] not in services:continue
  x,y=P(num(t['x_mm']),num(t['y_mm']));face=num(t['face_w_mm'])/2
  obstacles.append(box(x-face-120,y-face-180,x+face+120,y+face+180))
  dx,dy=TERM_OFF[t['tag']];xx,yy=P(num(t['x_mm'])+dx,num(t['y_mm'])+dy)
  obstacles.append(box(xx-520,yy-270,xx+520,yy+170))
 if key not in _LABEL_OBSTACLES:
  from shapely.prepared import prep
  _LABEL_OBSTACLES[key]=[prep(o) for o in obstacles]
 obstacles=_LABEL_OBSTACLES[key]
 tw=pdfmetrics.stringWidth(label,FONT,z)
 choices=[]
 for sign in [1,-1]:
  for offset in [0,250,-250,500,-500,750,-750,1000,-1000,1250,-1250,1500,-1500,1750,-1750,2000,-2000]:
   for clearance in [250,500,750,1000,1500,2000]:
    x=xy[0]+sign*n[0]*(ww/2+clearance)+u[0]*offset
    y=xy[1]+sign*n[1]*(ww/2+clearance)+u[1]*offset
    align='left' if x>=xy[0] else 'right';left=x if align=='left' else x-tw
    rect=box(left-40,y-z-35,left+tw+40,y+50)
    if bounds is not None and not bounds.covers(rect):continue
    if any(o.intersects(rect) for o in obstacles) or any(rect.intersects(o) for o in occupied):continue
    choices.append((hypot(x-xy[0],y-xy[1]),x,y,align,rect,sign))
 assert choices,('No clear device annotation position',q['tag'],label)
 _,x,y,align,rect,sign=min(choices,key=lambda r:r[0]);occupied.append(rect)
 start=xy if q['block']=='HVAC_AD' else (xy[0]+sign*n[0]*ww/2,xy[1]+sign*n[1]*ww/2)
 sc.line([start,(x,y-z*.45)],'INK',6)
 sc.text(x,y,label,z,'INK',align=align,mask=True)

def flowbox(sc,r,xy):
 x,y=P(*xy);w,h=2450,670
 sc.rect(x,y,w,h,r['air_type'],10,'#FFFFFF')
 sc.line([(x,y+330),(x+w,y+330)],r['air_type'],7)
 sc.text(x+90,y+220,f"{num(r['flow_l_s']):.1f} L/s     {num(r['velocity_m_s']):.2f} m/s",145,r['air_type'])
 sc.text(x+90,y+565,size(r)+'   '+r['tag'],145,r['air_type'])
 # Short leader to the known branch route; other quantities are in the schedules.
 candidates=[]
 for start,direction in [((x,y+h/2),(-1,0)),((x+w,y+h/2),(1,0)),((x+w/2,y),(0,-1)),((x+w/2,y+h),(0,1))]:
  for a,b in zip(pts(r),pts(r)[1:]):
   dx,dy=b[0]-a[0],b[1]-a[1];fac=max(0,min(1,((start[0]-a[0])*dx+(start[1]-a[1])*dy)/(dx*dx+dy*dy)))
   anchor=(a[0]+fac*dx,a[1]+fac*dy);candidates.append((hypot(anchor[0]-start[0],anchor[1]-start[1]),start,direction,anchor))
 _,start,direction,anchor=min(candidates,key=lambda c:c[0]);elbow=(start[0]+direction[0]*180,start[1]+direction[1]*180)
 sc.line([start,elbow,anchor],'INK',7);sc.circle(*anchor,30,'INK',7)

def model(kind,fulltags=False,boxes=False,fontscale=1):
 sc=Scene(24500,MH,fontscale);architecture(sc)
 services=['SA','RA','EA'] if kind=='CO' else ['SA'] if kind=='SA' else ['RA','EA'] if kind=='RA' else []
 # Draw rectangular distribution first and small runouts last, so terminal necks stay distinct.
 rr=[r for r in SECTIONS if r['air_type'] in services]
 rr.sort(key=lambda r:({'Main':0,'Branch':1,'Extract branch':1,'Room header':2,'Runout':3,'Extract runout':3}.get(r['role'],4),r['air_type']))
 NETWORK.draw(sc,rr)
 for r in rr:
  if r['role']=='Branch':
   p=pts(r)[0] if r['air_type']=='SA' else pts(r)[-1];sc.circle(*p,27,r['air_type'],7,COL[r['air_type']])
 if 'EA' in services:
  duct(sc,[P(18600,1500),P(20800,1500)],300,'EA')
  for rid,basey in [('09',7600),('03',5700),('01',1500)]:
   for j in range(2 if rid!='01' else 1):
    yy=basey+(600 if j==0 else -600) if rid!='01' else basey;ww=200 if rid=='09' else 300
    path=[P(20800,basey),P(21200,basey),P(21200,yy),P(21700,yy)] if yy!=basey else [P(20800,yy),P(21700,yy)]
    duct(sc,path,ww,'EA');duct(sc,[P(22300,yy),P(22800,yy),P(22800,yy-450)],ww,'EA')
    sc.block('HVAC_FAN',*P(22000,yy),tag=f'EF-{rid}-{j+1:02d}')
    for xx,tg in [(22540,f'MD-E{rid}-{j+1:02d}')]+([(21440,f'MD-IE{rid}-{j+1:02d}')] if rid!='01' else []):sc.block('HVAC_MD',*P(xx,yy),sx=1,sy=ww/600,tag=tg)
    sc.block('HVAC_FLEX',*P(21600,yy),sx=.65,sy=ww/600)
    sc.text(*P(21800,yy+460),f'EF-{rid}-{j+1:02d}',145,'INK',True,'center',mask=True)
   sc.text(*P(21100,basey+1550),'2 x 100%' if rid!='01' else 'DUTY / QTY TBC',135,'INK',True,mask=True)
 # Tagged maintenance access is beside devices, outside the tapered throat.
 label_boxes=[]
 for q in STATIONS:
  if q['air'] not in services:continue
  blk,xy,ww,tg=q['block'],q['xy'],q['width'],q['tag']
  sc.block(blk,*xy,a=q['angle'],sx=1,sy=1 if blk=='HVAC_AD' else q['mirror']*ww/600,tag=tg)
  restore_device_walls(sc,q)
  if blk=='HVAC_AD' or fulltags or blk=='HVAC_EH':
   label=('MFD-'+('S' if q['air']=='SA' else 'R')+q['room']+'*') if blk=='HVAC_MFD' else tg
   if not fulltags and blk=='HVAC_AD':label='AD'
   annotate_station(sc,q,label,label_boxes,services=services)
 for t in TERMINALS:
  if t['air_type'] not in services:continue
  x,y=num(t['x_mm']),num(t['y_mm']);xy=P(x,y);air=t['air_type'];blk={'SA':'HVAC_SD_4WAY','RA':'HVAC_RG','EA':'HVAC_EG'}[air]
  sc.block(blk,*xy,sx=num(t['face_w_mm'])/(600 if air=='SA' else 500),tag=t['tag'])
  dx,dy=TERM_OFF[t['tag']];prefix,rid,j=t['tag'].split('-');alias=f'{prefix}{rid}-{int(j)}'
  if t['tag']=='SD-06-02':sc.line([P(x+300,y+200),P(x+1000,y+200),P(x+1100,y+300)],'INK',6)
  sc.text(*P(x+dx,y+dy),alias,140,'INK',False,'center',mask=True)
 # Label mains inside their ducts; all flow/velocity/length data belongs in aligned tables.
 for r in rr:
  if r['role']!='Main':continue
  pp=pts(r);a,b=max(zip(pp,pp[1:]),key=lambda ab:hypot(ab[1][0]-ab[0][0],ab[1][1]-ab[0][1]));L=hypot(b[0]-a[0],b[1]-a[1]);vertical=abs(a[0]-b[0])<1
  xy=(a[0]+.66*(b[0]-a[0]),a[1]+.66*(b[1]-a[1]));txt=r['tag']+'  '+size(r) if L>2500 else r['tag']
  sc.text(*xy,txt,140,r['air_type'],False,'center',90 if vertical else 0,mask=not vertical)
 for rid,(x,y) in ROOM_POS.items():sc.text(*P(x,y),'GF-'+rid+('' if rid=='06' else '\n'+SHORT[rid]),155,'DIM',False,'center',mask=True)
 # Independent proposed drops, with a matching numbered roof-riser schedule.
 for r in RISERS:
  if r['air_type'] not in services:continue
  x,y=P(float(r['x_mm']),float(r['y_mm']))
  sc.circle(x,y,120,r['air_type'],9,'#FFFFFF')
  sc.line([(x-80,y-80),(x+80,y+80)],r['air_type'],7)
  sc.line([(x-80,y+80),(x+80,y-80)],r['air_type'],7)
  sc.text(x+180,y-250,r['tag'],100,r['air_type'],mask=True)
 sc.text(*P(1000,20600),'INDOOR BARE BOD +3.400 m PROPOSED / ROOF DROPS: D-022',120,'INK',mask=True)
 # Actual overall dimensions, without invented structural grid references.
 sc.line([P(0,20400),P(20000,20400)],'DIM',8)
 for x in [0,20000]:sc.line([P(x,19500),P(x,20600)],'DIM',6);sc.line([P(x-90,20310),P(x+90,20490)],'DIM',10)
 sc.text(*P(10000,20600),'20000',150,'DIM',False,'center')
 sc.line([P(-650,0),P(-650,19500)],'DIM',8)
 for y in [0,19500]:sc.line([P(-850,y),P(0,y)],'DIM',6);sc.line([P(-740,y-90),P(-560,y+90)],'DIM',10)
 sc.text(*P(-850,9750),'19500',150,'DIM',False,'center',90)
 if boxes:
  for air,positions in BOX_POS.items():
   if air not in services:continue
   for rid,xy in positions.items():flowbox(sc,BYSEC[air+'-B'+rid],xy)
 # All text overlays its own white mask and remains above routes / symbols.
 geometry=[];labels=[]
 for op in sc.ops:
  if op[0]=='text' or (op[0]=='poly' and op[5]=='LABEL_MASK'):labels.append(op)
  else:geometry.append(op)
 sc.ops=geometry+labels
 return sc

MODELS={'COORDINATION':model('CO'),'SUPPLY':model('SA',boxes=True),'RETURN_EXTRACT':model('RA',boxes=True),'NORTH_DETAIL':model('CO',fulltags=True,fontscale=.70),'SOUTH_DETAIL':model('CO',fulltags=True,fontscale=.50)}

# Instrumentation is separate, with faint route context and common-duct walls
# so the leaders visibly end at the physical measurement points.
sc=Scene(24500,MH);architecture(sc)
for r in SECTIONS:
 if r['role'] in ['Main','Branch','Extract branch']:sc.line(pts(r),'ARCH',6,True)
from duct_geometry import pieces
from shapely.geometry import box
for rid,(x,y) in ROOM_POS.items():
 if rid=='02':x,y=6500,18800
 sc.text(*P(x,y),'GF-'+rid+'\n'+SHORT[rid],155,'DIM',False,'center',mask=True)
ipos={'02':(5700,15100),'05':(14600,16700),'04':(2200,5000),'08':(8700,5150),'06':(6700,9450),'07':(13800,2700),'09':(13200,6350),'03':(18800,6100),'01':(18100,2800)}
for rid,(x,y) in ipos.items():
 for i,(prefix,blk) in enumerate([('TT','HVAC_TT'),('RHT','HVAC_RHT'),('DPT','HVAC_DPT')]):
  xx=x+(i-1)*1100;sc.block(blk,*P(xx,y),tag=prefix+'-GF-'+rid);sc.text(*P(xx,y+520),prefix+'-GF-'+rid,140,'INST',False,'center',mask=True)
 sc.text(*P(x,y-650),'ROOM TARGET +'+str(int(ROOMS[rid]['pressure']))+' Pa',140,'INST',False,'center',mask=True)
# Common duct probes are functional roof-plant attachments on D-012; there
# is no surveyed roof route available to assign credible plan coordinates.
INSTRUMENT_LOCATIONS=[{'tag':tg,'section':sec,'zone':'ROOF_PROPOSAL','drawing':'D-012','status':'Functional common-duct attachment; actual roof coordinates / straight run / insertion / weather protection TBC'} for tg,sec in [('FIT-SA-01','SA-M01'),('TT-SA-01','SA-M01'),('FIT-RA-01','RA-M01'),('TT-RA-01','RA-M01'),('RHT-RA-01','RA-M01')]]
write_register('Instrument_locations.csv',INSTRUMENT_LOCATIONS)
sc.rect(*P(8300,11200),700,500,'INST',12,'#FFFFFF');sc.text(*P(8650,11600),'HPCP-01 / HMI-01',145,'INST',False,'center',mask=True)
sc.text(*P(10900,11600),'BMS / SCADA INTERFACE',140,'INST',mask=True)
MODELS['INSTRUMENTATION']=sc

def legend(s,x,y,w=240,small=False):
 section_heading(s,x,y,'DUCT / SYMBOL LEGEND',w);y+=11
 for k,t in [('SA','SA - supply duct'),('RA','RA - return duct'),('EA','EA - dedicated extract')]:
  s.rect(x,y-2,26,5,k,.35,'#FFFFFF');s.arrow((x+3,y+.5),(x+20,y+.5),'FLOW',.22,1.5);s.text(x+34,y+1.8,t,2.7);y+=10
 for n,t in [('HVAC_SD_4WAY','SD - four-way supply diffuser'),('HVAC_RG','RG - ducted return grille'),('HVAC_EG','EG - extract grille'),('HVAC_VCD','VCD - balancing damper'),('HVAC_MFD','MFD* - conditional fire damper'),('HVAC_RCD','RCD - return control damper'),('HVAC_EH','EH - inline electric heater'),('HVAC_AD','AD - access door')]:
  s.block(n,x+10,y+1,sx=.016,sy=.016);s.text(x+34,y+2,t,2.7);y+=13 if n.startswith('HVAC_M') else 12
 s.circle(x+10,y+1,3,'SYM',.25,'#FFFFFF')
 s.line([(x+8,y-1),(x+12,y+3)],'SYM',.2);s.line([(x+8,y+3),(x+12,y-1)],'SYM',.2)
 s.text(x+34,y+2,'RS - proposed roof supply / return drop',2.7);y+=12
 return y
def room_table(s,x,y,w,ids,term=False):
 rows=[]
 for rid in ids:
  r=ROOMS[rid];ea='TBC' if r['ea'] is None else f"{r['ea']:.1f}" if not r['rn'] else '-'
  rows.append([rid,SHORT[rid],f"{r['sa']:.1f}",f"{r['ra']:.1f}" if r['rn'] else '-',ea])
 return table(s,x,y,w,['GF','Room','SA L/s','RA L/s*','EA L/s*'],rows,[.5,2.15,.8,.8,.8],2.5,13)
def main_table(s,x,y,w,air):
 rows=[[r['tag'],size(r),f"{num(r['flow_l_s']):.1f}",f"{num(r['velocity_m_s']):.2f}"] for r in ROOF_MAIN if r['air_type']==air]
 return table(s,x,y,w,['Section','W x H mm','L/s','m/s'],rows,[1.25,1.45,1,1],2.6,11)
def room_cards(s,x,y,w,ids):
 for rid in ids:
  r=ROOMS[rid];s.rect(x,y,w,51,'INK',.25,'#FFFFFF');s.text(x+4,y+6,f'GF-{rid}  '+SHORT[rid],3.2,'INK',True)
  yy=y+14
  for air in ['SA','RA','EA']:
   key=air+'-B'+rid
   if key not in BYSEC:continue
   a=BYSEC[key];s.text(x+4,yy,f"{key}  {size(a)} mm  |  {num(a['flow_l_s']):.2f} L/s  |  {num(a['velocity_m_s']):.2f} m/s",2.6,air);yy+=8
  st=[t for t in TERMINALS if t['room']==rid and t['air_type']=='SA'][0]
  s.text(x+4,yy,f"SD: {r['n']} x {r['sa']/r['n']:.2f} L/s; neck D{st['neck_dia_mm']}; face {st['face_w_mm']}x{st['face_h_mm']}",2.6);yy+=7
  if r['rn']:s.text(x+4,yy,f"RG: {r['rn']} x {r['ra']/r['rn']:.2f} L/s; neck D300; face 500x500",2.6)
  elif rid=='01':s.text(x+4,yy,'EA / grille duty and pickup level: TBC',2.6)
  else:s.text(x+4,yy,'Dedicated extract; no central return',2.6)
  s.text(x+4,y+46,'Room header: branch size. Terminal runout: listed neck.',2.4,'NOTE')
  y+=58
 return y

FULL=(-1200,-500,23900,21100)
SHEETS=[]
s=paper_frame('COORDINATED DUCT PLAN',1,scale='1:50');view(s,MODELS['COORDINATION'],28,42,50,FULL)
section_heading(s,557,45,'ROOM AIRFLOW SCHEDULE',265);room_table(s,557,52,265,ORDER)
yy=legend(s,557,194,265)
s.para(557,yy+5,'Terminal aliases: SD02-1 = SD-02-01; RG / EG follow the same format. Full tags and quantities are in the registers.',260,2.7)
s.para(557,yy+34,'Roof-main OPTION: 15 independent room drops RS-SA / RS-RA. No indoor service crossings. Finished ceiling +3.300 m; proposed bare BOD +3.400 m. Envelope: D-020; roof/drop holds: D-022.',260,2.7)
s.para(557,yy+64,'* Return quantities are assumed balances. Extract references and +50 / +25 Pa targets require final airflow and pressure verification.',260,2.7)
note_footer(s,'Units: mm / L/s / m/s. Terminal faces and clear duct widths are shown. Duct levels, selected fitting development and manufacturer clearances remain pending. No shared return from kitchen, toilet or clean-agent room.');SHEETS.append(s)

s=paper_frame('SUPPLY AIR DUCT PLAN',2,scale='1:50');view(s,MODELS['SUPPLY'],28,42,50,FULL)
section_heading(s,557,45,'PROPOSED ROOF SUPPLY MAIN BASIS',265);yy=main_table(s,557,52,265,'SA')
section_heading(s,557,yy+15,'ROOM SUPPLY BRANCHES',265)
rows=[[rid,size(BYSEC['SA-B'+rid]),f"{ROOMS[rid]['sa']:.1f}",f"{num(BYSEC['SA-B'+rid]['velocity_m_s']):.2f}"] for rid in ORDER]
yy=table(s,557,yy+22,265,['GF','W x H mm','L/s','m/s'],rows,[.6,1.5,1,1],2.7,11)
s.para(557,yy+12,'Room headers retain their branch size. Diffuser tags identify individual outlets. Round runout / neck diameters and each terminal airflow are listed on D-004 to D-006 and D-010.',260,2.7)
s.para(557,yy+39,'MFD* is a conditional rated-penetration provision. VCD-Snn and FSD-Snn correspond to the GF-nn supply branch. Inline heaters are upstream of that room\'s terminal take-offs.',260,2.7)
s.para(557,yy+78,'Continuous main tapers, flared branch boots and terminal adaptors: D-011. AD tags identify maintenance access doors. Proposed taper lengths and device coordinates are in the registers.',260,2.7)
note_footer(s,'Total HAP-reference supply: 3697.80 L/s. Three 50% PAUs: two duty, rotating available alternate. Boxed callouts show branch flow, velocity and clear size. No room sensors are overlaid on this duct plan.');SHEETS.append(s)

s=paper_frame('RETURN AIR AND EXTRACT DUCT PLAN',3,scale='1:50');view(s,MODELS['RETURN_EXTRACT'],28,42,50,FULL)
section_heading(s,557,45,'PROPOSED ROOF RETURN MAIN BASIS',265);yy=main_table(s,557,52,265,'RA')
section_heading(s,557,yy+15,'ROOM RETURN / EXTRACT',265)
rows=[]
for rid in ORDER:
 r=ROOMS[rid];key='RA-B'+rid if r['rn'] else 'EA-B'+rid
 if key in BYSEC:
  a=BYSEC[key];rows.append([rid,a['air_type'],size(a),f"{num(a['flow_l_s']):.1f}"])
 else:rows.append([rid,'EA','TBC','TBC'])
yy=table(s,557,yy+22,265,['GF','Air','W x H mm','L/s*'],rows,[.5,.6,1.6,1.1],2.7,12)
s.para(557,yy+12,'No central return: GF-09 toilets, GF-03 kitchen and GF-01 clean-agent. Kitchen / toilet fans: 2 x 100% with duty rotation. CAG duty and quantity remain unverified.',260,2.7)
s.para(557,yy+43,'Extract fan symbols are schematic equipment markers; actual fan and louver dimensions depend on manufacturer selection. Wall outlets face downwards.',260,2.7)
note_footer(s,'* Return total 3006.68 L/s is an assumed starting balance. Existing extract references do not verify positive pressure or outdoor-air compliance. Confirmed fire shuts down all HVAC; automatic fire extraction is not enabled.');SHEETS.append(s)

s=paper_frame('NORTH ROOMS - DUCT ENLARGEMENT',4,scale='1:35');view(s,MODELS['NORTH_DETAIL'],25,42,35,(-500,10300,20500,21100))
s.line([(25,353),(625,353)],'DIM',.2,True);s.text(325,358,'MATCH LINE - CONTINUED ON D-005 / D-006',2.7,'NOTE',False,'center')
section_heading(s,25,363,'NORTH-ROOM TERMINALS / BRANCHES',790)
room_cards(s,25,375,380,['02']);room_cards(s,426,375,389,['05'])
s.para(25,445,'Plan symbols identify VCD-S02 / S05, conditional MFD-S02 / S05*, RCD-R02 / R05 and conditional return MFDs. The component register retains the FSD tag prefix for the conditional motorized fire/smoke damper symbols.',790,2.8)
s.para(25,466,'Deep common mains are proposed on the roof. Separate supply / return drops feed each room tree. Bare BOD +3.400 m is a proposed indoor level. Actual roof routes and structural penetrations require coordination; D-020 / D-022.',790,2.8)
note_footer(s,'Access doors: AD-Snn / AD-Rnn beside branch dampers; AD-Hnn beside heaters. Taper / access arrangements: D-011. Instrumentation: D-007 / D-012. Catalogue selection remains pending.');SHEETS.append(s)

s=paper_frame('SOUTH-WEST ROOMS - DUCT ENLARGEMENT',5,scale='1:25');view(s,MODELS['SOUTH_DETAIL'],25,42,25,(-500,-500,11800,10800))
s.line([(519,42),(519,494)],'DIM',.2,True);s.text(529,268,'MATCH LINE - CONTINUED ON D-006',2.7,'NOTE',False,'center',90)
s.text(270,38,'NORTH CONTINUATION: D-004',2.6,'NOTE',False,'center')
section_heading(s,544,45,'ROOM BRANCH / TERMINAL DATA',272);yy=room_cards(s,544,56,272,['04','08','06'])
yy=legend(s,544,yy+7,272)
s.para(544,yy+8,'Red arrows show air direction; green outlines are supply and blue outlines are return. Room drops refer to D-022. No indoor service crossovers. Same-service junctions are continuous open tees; headroom envelope: D-020.',265,2.7)
note_footer(s,'GF-04 meeting; GF-08 telecom; GF-06 corridor. Room targets +50 Pa relative to outdoors; actual pressure verification remains pending. Full flow / velocity / horizontal route data is listed on D-010.');SHEETS.append(s)

s=paper_frame('SOUTH-EAST ROOMS - DUCT ENLARGEMENT',6,scale='1:25');view(s,MODELS['SOUTH_DETAIL'],25,42,25,(11500,-500,23900,11300))
s.line([(23,42),(23,514)],'DIM',.2,True);s.text(19,278,'MATCH LINE - CONTINUED ON D-005',2.7,'NOTE',False,'center',90)
s.text(275,38,'NORTH CONTINUATION: D-004',2.6,'NOTE',False,'center')
section_heading(s,544,45,'ROOM BRANCH / TERMINAL DATA',272);yy=room_cards(s,544,56,272,['09','07','03','01'])
section_heading(s,544,yy+10,'EXTRACT ARRANGEMENTS',272)
s.para(544,yy+23,'EF-09-01/02: toilets, 2 x 100%. EF-03-01/02: kitchen, 2 x 100%. EF-01-01: one CAG fan marker shown; final quantity, airflow and pickup elevation require confirmation.',265,2.8)
s.para(544,yy+65,'Kitchen, toilet and CAG targets: +25 Pa to outdoors. Resting room: +50 Pa, with return air. Minimum ventilation: 10 ACH kitchen / toilet; 5 ACH CAG.',265,2.8)
s.para(544,yy+106,'Toilet HAP supply is 46.2 L/s; minimum outdoor-air duty is not established by that mixed-air supply. Resolve the fresh-air duty before final HAP and pressure balance.',265,2.8)
note_footer(s,'CAG receives cooled PAU supply and has dedicated extract. No shared return from kitchen, toilet or CAG. All fan branches have motorized isolation; control / shutdown sequences are on the schematic set.');SHEETS.append(s)

s=paper_frame('ROOM INSTRUMENTATION AND CONTROL LOCATIONS',7,scale='1:50');view(s,MODELS['INSTRUMENTATION'],28,42,50,FULL)
section_heading(s,557,45,'ROOM FIELD INSTRUMENTS',265)
rows=[[rid,f'TT-GF-{rid}',f'RHT-GF-{rid}',f'DPT-GF-{rid}',str(int(ROOMS[rid]['pressure']))] for rid in ORDER]
yy=table(s,557,52,265,['GF','Temperature','Humidity','Pressure','Pa'],rows,[.45,1.35,1.35,1.35,.55],2.6,14)
section_heading(s,557,yy+15,'MAIN DUCT / PLANT MONITORING',265)
for i,t in enumerate(['TT-SA-01 / TT-RA-01: main duct temperature','RHT-RA-01: main return humidity','FIT-SA-01 / FIT-RA-01: common airflow','Each PAU filter: PDT remote + PDI local','DPT-SF-A/B/C: PAU fan pressure proof','VS: PAU and ventilation-fan vibration','EM: feeders >7.5 kW, quantity to confirm']):s.text(557,yy+28+i*10,t,2.7)
s.para(557,yy+106,'Signals report to HPCP-01 dedicated PLC and HMI-01. BMS / SCADA provides the specified monitoring, initial start and emergency-stop interfaces. Protocol, alarm limits, I/O module allocation and actuator fail positions remain pending.',260,2.7)
s.para(557,yy+158,'DPT room references are outdoors, not the adjacent room. DPT-GF-06 is the corridor / building reference. Additional room DPTs and CAG humidity sensing are marked as added provisions in the register.',260,2.7)
note_footer(s,'Room instrument locations are proposed. Plant/filter/fan instruments and heater AFS / TSHH protection: D-012. Final ranges, reference probes, mounting and routes require I&C coordination; operating sequence: S-004.');SHEETS.append(s)

def pd(s,p,w=7,k='SA'):
 tmp=Scene();duct(tmp,[(x*50,y*50) for x,y in p],w*50,k)
 for op in tmp.ops:
  t=op[0]
  if t in ['line','poly']:
   q=list(op);q[1]=[(x/50,y/50) for x,y in op[1]];q[3]/=50;s.ops.append(tuple(q))
def bs(s,n,x,y,w=8,h=8,a=0):
 dims={'HVAC_SD_4WAY':(600,600),'HVAC_RG':(500,500),'HVAC_EG':(500,500),'HVAC_VCD':(180,600),'HVAC_MD':(180,600),'HVAC_MFD':(180,600),'HVAC_RCD':(180,600),'HVAC_EH':(420,600),'HVAC_AD':(180,180),'HVAC_FLEX':(180,600),'HVAC_FILTER':(200,600),'HVAC_SILENCER':(600,600),'HVAC_FAN':(600,600)}
 ww,hh=dims.get(n,(300,300));s.block(n,x,y,a,w/ww,h/hh)

s=paper_frame('PAU BANK AND PROPOSED ROOF COMMON DISTRIBUTION',8)
section_heading(s,18,42,'A  ROOF CONNECTION ARRANGEMENT - SCHEMATIC FOOTPRINTS',805)
pd(s,[(33,64),(805,64)],9,'RA');s.text(33,58,'RETURN HEADER  1400x650  |  3006.68 L/s ASSUMED',2.8,'RA')
pd(s,[(805,231),(33,231)],9,'SA');s.text(33,245,'SUPPLY HEADER  1200x650  |  3697.80 L/s',2.8,'SA')
pd(s,[(805,273),(33,273)],5,'OA');s.text(33,289,'OUTDOOR AIR: FINAL DUTY TBC; INTAKE / EXHAUST SEPARATION TO VERIFY',2.7,'OA')
for i,c in enumerate('ABC'):
 x=62+i*245;s.rect(x,115,197,94,'INK',.35);s.text(x+98,125,'PAU-'+c+'  |  50% UNIT',3.3,'INK',True,'center')
 s.text(x+98,201,'1848.90 L/s  |  OEM SIZE / DUTY TBC',2.6,'INK',False,'center')
 pd(s,[(x+20,64),(x+20,153)],7,'RA');bs(s,'HVAC_MD',x+20,83,4,7,90);s.text(x+25,88,'MD-RA-'+c,2.3)
 pd(s,[(x-17,273),(x-17,155),(x+11,155)],5,'OA');bs(s,'HVAC_MD',x-17,184,4,5,90);s.text(x-13,189,'MD-OA-'+c,2.3)
 s.rect(x+12,147,16,17,'INK',.25,'#FFFFFF');s.text(x+20,157,'MIX',2.4,'INK',False,'center')
 pd(s,[(x+28,155),(x+166,155),(x+166,231)],7,'SA')
 bs(s,'HVAC_FILTER',x+48,155,6,20);s.text(x+48,174,'MERV 8',2.3,'INK',False,'center')
 bs(s,'HVAC_FILTER',x+74,155,8,20);s.text(x+74,174,'MERV 14',2.3,'INK',False,'center')
 s.rect(x+93,143,25,24,'INK',.25,'#FFFFFF');s.text(x+105,157,'DX',2.8,'INK',True,'center')
 s.line([(x+105,167),(x+105,181),(x+121,181)],'INK',.25);s.text(x+111,189,'CD / TRAP',2.2)
 bs(s,'HVAC_FAN',x+137,155,14,14);s.text(x+137,175,'SF-'+c,2.5,'INK',False,'center')
 bs(s,'HVAC_FLEX',x+166,186,3,7,90);bs(s,'HVAC_MD',x+166,219,4,7,90);s.text(x+171,223,'MD-SA-'+c,2.3)
bs(s,'HVAC_FILTER',746,273,5,13);s.rect(776,265,21,16,'INK',.25,'#FFFFFF');s.text(786,274,'STL',2.5,'INK',False,'center');s.text(732,297,'STL + mesh + MERV 8 filter',2.4,'INK',False,'center')
s.line([(18,307),(823,307)],'INK',.25)
section_heading(s,18,319,'B  ROOF COMMON PLANT / DISTRIBUTION OPTION - FUNCTIONAL NTS',805)
pd(s,[(36,376),(805,376)],12,'SA')
for blk,x,tg in [('HVAC_SILENCER',128,'SA-SIL-01'),('HVAC_EH',300,'EH-COM-01'),('HVAC_FIT',541,'FIT-SA-01'),('HVAC_TT',666,'TT-SA-01')]:
 bs(s,blk,x,376,19 if blk in ['HVAC_EH','HVAC_SILENCER'] else 7,16 if blk in ['HVAC_EH','HVAC_SILENCER'] else 7)
 s.text(x,404,tg,2.7,'INK',align='center')
s.rect(404,368,25,16,'SA',.25,'#FFFFFF',True);s.text(416,378,'HUM*',2.5,'INK',align='center')
bs(s,'HVAC_AD',276,382,5,5);s.text(250,420,'AD-HCOM-01',2.6)
s.arrow((731,376),(786,376),'FLOW',.25,2);s.text(735,360,'9 ROOM DROPS',2.7,'SA')
pd(s,[(805,459),(36,459)],12,'RA')
for blk,x,tg in [('HVAC_SILENCER',128,'RA-SIL-01'),('HVAC_FIT',400,'FIT-RA-01'),('HVAC_TT',550,'TT-RA-01'),('HVAC_RHT',683,'RHT-RA-01')]:
 bs(s,blk,x,459,19 if blk=='HVAC_SILENCER' else 7,16 if blk=='HVAC_SILENCER' else 7)
 s.text(x,483,tg,2.7,'INK',align='center')
s.arrow((780,459),(731,459),'FLOW',.25,2);s.text(735,440,'6 ROOM RETURNS',2.7,'RA')
s.para(18,506,'Common heater / conditional humidifier move to a weather-protected roof plant enclosure in this option. Equipment suitability, safety, intake separation, maintenance space and outdoor insulation require OEM / project specification. Actual roof geometry and vertical development: TBC.',804,2.8)
note_footer(s,'ROOF OPTION, NOT CONSTRUCTION ISSUE. Functional connections shown NTS; do not scale as roof routing. Each room drop and structural penetration is proposed, D-022. Common instrument signals remain on D-012 / S-001.');SHEETS.append(s)

s=paper_frame('DUCT SYMBOLS AND INSTALLATION DETAILS',9)
def tile(x,y,number,title):
 s.rect(x,y,258,153,'DIM',.25);s.text(x+5,y+9,f'{number:02d}  '+title,3.1,'INK',True)
def cap(x,y,txt):s.para(x+5,y+137,txt,248,2.5,'NOTE')
for x,y,n,title in [(18,40,1,'DUCT SUPPORT / INSULATION'),(291,40,2,'SUPPLY DIFFUSER CONNECTION'),(564,40,3,'RETURN / EXTRACT GRILLE'),(18,201,4,'RATED PENETRATION / MFD*'),(291,201,5,'BEND / TAPER TRANSITION'),(564,201,6,'ROOM PRESSURE SENSING'),(18,362,7,'FILTER DP MONITORING'),(291,362,8,'COIL DRAIN / TRAP'),(564,362,9,'INTAKE / EXHAUST OUTLET')]:tile(x,y,n,title)
# 01
s.rect(37,73,207,8,'DIM',.25)
for x in [62,220]:s.line([(x,81),(x,145)],'INK',.4);s.rect(x-4,141,8,5,'INK',.25)
s.rect(79,97,124,46,'SA',.35);s.rect(74,92,134,56,'DIM',.25,None,True);s.line([(51,152),(232,152)],'INK',.9)
s.line([(207,98),(223,87)],'INK',.2);s.text(226,88,'INSULATION',2.5)
cap(18,40,'Anchor loads, support spacing, insulation and vapor barrier: approved fabrication / structural selection.')
# 02
pd(s,[(311,94),(363,94),(363,140)],8,'SA');bs(s,'HVAC_VCD',337,94,3,8);bs(s,'HVAC_FLEX',363,119,4,8,90)
s.rect(347,140,36,15,'SA',.25,'#FFFFFF');s.line([(311,160),(528,160)],'DIM',.3);bs(s,'HVAC_SD_4WAY',365,160,16,16)
s.line([(377,146),(404,126)],'INK',.2);s.text(407,127,'PLENUM / OBD',2.6)
s.text(337,84,'VCD',2.6,'INK',False,'center');cap(291,40,'Neck <=2 m/s. Face, throw, noise and loss from selected diffuser catalogue; accessible balancing required.')
# 03
pd(s,[(583,94),(627,94),(627,137)],8,'RA');bs(s,'HVAC_VCD',605,94,3,8)
s.rect(609,137,36,17,'RA',.25,'#FFFFFF');bs(s,'HVAC_RG',627,160,15,15)
s.line([(645,141),(678,119)],'INK',.2);s.text(681,120,'SEALED PLENUM',2.6);s.text(664,158,'REMOVABLE GRILLE',2.6)
cap(564,40,'Return grilles connect to RA duct. Extract grilles connect to their dedicated outdoor duct; pickup height TBC.')
# 04
s.rect(120,230,10,89,'DIM',.25);pd(s,[(36,270),(254,270)],15,'SA');bs(s,'HVAC_MFD',125,270,5,15);bs(s,'HVAC_AD',164,279,5,5)
s.line([(129,287),(153,308)],'INK',.2);s.text(155,310,'SLEEVE / FIRESTOP',2.6);s.text(167,290,'AD',2.5)
cap(18,201,'MFD* only at approved rated boundaries. Select tested sleeve / firestop assembly and allow actuator / inspection access.')
# 05
pd(s,[(312,245),(367,245),(367,300)],13,'SA')
s.poly([(427,261),(481,270),(481,286),(427,295)],'SA',.35,'#FFFFFF');s.arrow((435,279),(470,279),'FLOW',.25,1.7)
s.text(410,318,'TAPERED TRANSITION',2.6);cap(291,201,'Radius bends or miter bends / turning vanes to selected fitting design. Final loss coefficients and development TBC.')
# 06
s.rect(617,230,8,90,'DIM',.25);bs(s,'HVAC_DPT',659,266,12,12)
s.line([(653,263),(586,263)],'INST',.25,True);s.text(583,252,'+ ROOM',2.6,'INST')
s.line([(665,269),(755,269),(755,306)],'INST',.25,True);s.rect(741,309,28,10,'DIM',.25);s.text(720,331,'- OUTDOOR STATIC REF.',2.6,'INST')
s.text(648,246,'DPT-GF-nn',2.6,'INST');cap(564,201,'Weather-shielded outdoor static reference; route tubes to minimize wind / water effects. Range, alarm limits and mounting TBC.')
# 07
pd(s,[(37,430),(249,430)],16,'SA');bs(s,'HVAC_FILTER',126,430,7,23);bs(s,'HVAC_PDT',93,397,11,11);bs(s,'HVAC_PDI',193,467,11,11)
s.line([(115,430),(115,397),(98.5,397)],'INST',.25);s.line([(139,430),(139,388),(87.5,388),(87.5,397)],'INST',.25)
s.line([(115,440),(115,467),(187.5,467)],'INST',.25);s.line([(139,440),(139,477),(198.5,477),(198.5,467)],'INST',.25)
s.text(74,386,'PDT remote',2.6,'INST');s.text(172,487,'PDI local',2.6,'INST');cap(18,362,'Each PAU filter bank has remote DP and local gauge. Upstream / downstream taps; dirty-filter threshold by OEM.')
# 08
s.rect(318,395,99,12,'SA',.25);s.line([(365,407),(365,434),(390,434),(390,465),(420,465),(420,433),(508,433)],'INK',.55);s.arrow((482,433),(509,433),'INK',.25,1.7)
s.circle(390,428,3,'INK',.25);s.text(405,421,'CLEANOUT / PRIME',2.6);s.text(435,450,'APPROVED DRAIN',2.6)
cap(291,362,'Trap seal / invert from actual unit casing pressure. Drain slope, disposal route, cleanout and water seal by OEM / plumbing.')
# 09
s.rect(615,390,8,86,'DIM',.25);s.rect(637,410,18,22,'INK',.25);s.text(646,423,'STL',2.6,'INK',False,'center');bs(s,'HVAC_FILTER',596,421,5,18)
s.arrow((663,421),(581,421),'FLOW',.25,1.7);pd(s,[(704,404),(781,404),(781,461)],9,'EA');s.arrow((781,450),(781,470),'FLOW',.25,1.7)
s.text(700,488,'DOWNWARD EXHAUST OUTLET',2.6)
cap(564,362,'STL face <=1 m/s; exhaust louver <=2.5 m/s. Final face areas, loss, materials and intake separation require selection.')
note_footer(s,'Details are NTS engineering concepts. Duct colours / symbols match the plans; body dimensions are not manufacturer selections. No room pressure, fire rating or equipment clearance is certified by this drawing.');SHEETS.append(s)

s=paper_frame('DUCT AND TERMINAL SCHEDULES',10)
section_heading(s,18,44,'MAIN AND ROOM BRANCH SECTIONS',457)
rows=[]
for r in SECTIONS:
 if r['role'] in ['Main','Branch','Extract branch']:
  rows.append([r['tag'],size(r),f"{num(r['flow_l_s']):.2f}",f"{num(r['velocity_m_s']):.2f}",f"{num(r['horizontal_length_m']):.2f}",f"{num(r['friction_pa_m']):.3f}"])
rows.append(['EA-B01','TBC','TBC','TBC','TBC','TBC'])
yy=table(s,18,51,457,['Section','Size mm','L/s','m/s','Lh m*','Pa/m'],rows,[1.45,1.55,1.35,.85,.9,.9],2.7,12.3)
s.para(18,yy+11,'* Lh is the source orthogonal horizontal route allowance. Final straight lengths, selected elbow development, risers / drops and fitting losses require coordination. Vertical lengths and BOD are unverified.',451,2.7)
section_heading(s,491,44,'TERMINAL GROUPS',330)
rows=[]
for rid in ORDER:
 for air in ['SA','RA','EA']:
  tt=[t for t in TERMINALS if t['room']==rid and t['air_type']==air]
  if not tt:continue
  a=tt[0];q=num(a['flow_l_s']);rows.append([rid,{'SA':'SD','RA':'RG','EA':'EG'}[air],str(len(tt)),f'{q:.2f}' if q is not None else 'TBC','D'+a['neck_dia_mm'] if a['neck_dia_mm']!='TBC' else 'TBC',a['face_w_mm']+'x'+a['face_h_mm']])
yy=table(s,491,51,330,['GF','Type','Qty','Each L/s','Neck mm','Face mm'],rows,[.55,.7,.5,1.05,1.05,1.5],2.7,13)
section_heading(s,491,yy+16,'SYSTEM / DESIGN BASIS',330)
texts=['Total supply: 3697.80 L/s. Assumed return: 3006.68 L/s.','Six return rooms: 59.34 L/s net outward allowance each, based on the accepted 0.01 m2 illustrative equivalent area.','Final room pressure, IAQ outdoor-air duty and revised HAP loads remain unverified. Current 420.70 L/s OA is below the 691.12 L/s assumed-balance makeup requirement.',f'All {len(SECTIONS)} duct sections, {len(FITTINGS)} fitting entries, {len(TERMINALS)} terminals, {len(COMPONENTS)} components and {len(INSTRUMENTS)} instruments are in the editable registers.','Rev11: routing / fitting topology revised; changed sizes and proposed terminal relocations are registered on D-021. Same-service overlaps and duplicated centerlines are rejected.']
yp=yy+29
for t in texts:yp+=s.para(491,yp,t,326,2.7)+7
note_footer(s,'Sizes are clear internal dimensions. Catalogue free area, diffuser throw / noise, coil / filter / louver / silencer losses, fitting coefficients and OEM fan curves are pending. Confirmed fire stops the entire HVAC.');SHEETS.append(s)

# Dedicated fitting / access sheet keeps the enlarged room plans readable.
s=paper_frame('TAPERED FITTINGS AND MAINTENANCE ACCESS',11)
for x,n,title in [(18,1,'CONTINUOUS MAIN REDUCER'),(291,2,'FLARED ROOM-BRANCH BOOT'),(564,3,'RECTANGULAR TO ROUND ADAPTOR')]:
 s.rect(x,40,258,145,'DIM',.25);s.text(x+5,50,f'{n:02d}  '+title,3.1,'INK',True)
# Main reduction: open joints and a single continuous side profile.
s.line([(33,87),(104,87),(158,94),(257,94)],'SA',.5)
s.line([(33,127),(104,127),(158,120),(257,120)],'SA',.5)
s.arrow((45,107),(243,107),'FLOW',.25,2)
s.line([(104,138),(158,138)],'DIM',.2)
for x in [104,158]:s.line([(x,133),(x,143)],'DIM',.2)
s.text(131,148,'PROPOSED L',2.6,'INK',False,'center')
s.text(69,76,'1200 x 650',2.7,'SA',False,'center');s.text(207,83,'1100 x 575',2.7,'SA',False,'center')
s.para(23,163,'Taper replaces the straight duct profile. Both width and height change; actual development / K from selected fitting.',248,2.5,'NOTE')
# Side boot: main wall is genuinely open at the flared throat.
s.line([(308,83),(536,83)],'SA',.5)
s.line([(308,106),(394,106)],'SA',.5);s.line([(442,106),(536,106)],'SA',.5)
s.line([(394,106),(403,134),(403,152)],'SA',.5);s.line([(442,106),(433,134),(433,152)],'SA',.5)
s.arrow((322,94),(510,94),'FLOW',.25,1.8);s.arrow((418,110),(418,150),'FLOW',.25,1.8)
s.text(315,74,'MAIN W x H',2.7,'SA');s.text(454,129,'FLARED BOOT',2.6,'INK');s.line([(452,133),(437,125)],'INK',.2)
s.para(296,163,'Side connection has a tapered throat and open main wall. Place balancing / fire devices on the branch straight.',248,2.5,'NOTE')
# Rectangular / circular conversion, two views without claiming a circular duct is rectangular.
s.line([(582,84),(639,84),(681,93),(799,93)],'SA',.5);s.line([(582,116),(639,116),(681,107),(799,107)],'SA',.5)
s.line([(681,89),(681,111)],'DIM',.2);s.arrow((595,100),(783,100),'FLOW',.25,1.8)
s.text(610,74,'600 x 350',2.7,'SA',False,'center');s.text(748,82,'D350',2.7,'SA',False,'center')
s.text(582,139,'PLAN',2.5,'NOTE');s.text(647,139,'HEIGHT / ROUND CONVERSION: OEM',2.5,'NOTE')
s.para(569,163,'Rectangular header to round neck / plenum conversion. Short direct drops use an integral adaptor: SD07-1 / RG05-5; section D-009.',248,2.5,'NOTE')

section_heading(s,18,204,'04  TYPICAL BRANCH STATIONS - FLOW DIRECTION / ACCESS',805)
pd(s,[(34,243),(530,243)],12,'SA')
for n,x,tg in [('HVAC_VCD',95,'VCD-Snn'),('HVAC_MFD',220,'MFD-Snn*'),('HVAC_EH',387,'EH-nn')]:
 bs(s,n,x,243,4 if n!='HVAC_EH' else 19,12);s.text(x,225,tg,2.8,'INK',False,'center')
for x,tg in [(176,'AD-Snn'),(352,'AD-Hnn')]:bs(s,'HVAC_AD',x,249,5,5);s.text(x,265,tg,2.6,'INK',False,'center')
s.text(34,281,'SUPPLY: boot -> VCD -> conditional MFD* -> room heater where scheduled -> terminals',2.7)
pd(s,[(532,311),(34,311)],12,'RA');bs(s,'HVAC_RCD',346,311,4,12);bs(s,'HVAC_MFD',136,311,4,12);bs(s,'HVAC_AD',196,317,5,5)
s.text(346,297,'RCD-Rnn',2.8,'INK',False,'center');s.text(136,297,'MFD-Rnn*',2.8,'INK',False,'center');s.text(196,333,'AD-Rnn',2.6,'INK',False,'center')
s.text(34,340,'RETURN: room grilles -> RCD / inspection access -> conditional MFD* -> return main',2.7)
s.rect(565,218,258,125,'DIM',.25);s.text(573,229,'05  ACCESS / PROTECTION',3,'INK',True)
s.para(573,242,'AD is a duct maintenance opening, not an inline damper. Access side and ceiling hatch must reach the damper blade / actuator, heater and inspection points.',241,2.7)
s.para(573,283,'AFS proves heater airflow; TSHH independently trips on high temperature. OEM hardwired safety inhibits heating; status reports to HPCP. Wiring: D-012 / S-004.',241,2.7)

section_heading(s,18,367,'MAIN TAPER SCHEDULE - PROPOSED GEOMETRY',392)
maintr=[t for t in NETWORK.transitions if t['type']=='Main tapered transition']
rows=[[t['tag'].replace('F-',''),size(BYSEC[t['upstream']]),size(BYSEC[t['downstream']]),str(t['length_mm'])] for t in maintr]
table(s,18,374,392,['Fitting','Inlet mm','Outlet mm','L mm*'],rows,[1.2,1.1,1.1,.7],2.5,10)
section_heading(s,431,367,'ACCESS-DOOR TAGS / BRANCH MAP',390)
rows=[]
for rid in ORDER:
 rows.append([rid,'AD-S'+rid,'AD-R'+rid if ROOMS[rid]['rn'] else '-','AD-H'+rid if rid in ['04','05','06','07','03'] else '-'])
rows.append(['COM','AD-HCOM-01','-','Common heater'])
yy=table(s,431,374,390,['GF','Supply access','Return access','Heater access'],rows,[.45,1.15,1.15,1.3],2.6,12)
s.para(431,yy+12,'20 indoor AD locations plus AD-HCOM-01 roof plant access are registered. Door clear opening, sealing / insulation, access hatch and OEM working envelope remain to be selected.',386,2.6)
note_footer(s,'* Taper lengths are explicit proposed coordination geometry, not approved fabrication lengths. The indoor register includes terminal adaptors. Main reducers and branch boots above are roof functional typicals; actual roof fittings and vertical drop details remain pending.');SHEETS.append(s)

s=paper_frame('PLANT INSTRUMENTATION AND HEATER PROTECTION',12)
section_heading(s,18,43,'A  EACH PAU: FILTER DIFFERENTIAL PRESSURE / FAN PROOF / VIBRATION',514)
def inst(s,blk,x,y,tag,z=2.5):
 bs(s,blk,x,y,7,7);s.text(x,y-8,tag,z,'INST',False,'center')
for i,c in enumerate('ABC'):
 y=61+i*86;s.rect(18,y,514,78,'DIM',.25);s.text(26,y+9,'PAU-'+c+'  |  50% UNIT',2.9,'INK',True)
 pd(s,[(32,y+43),(514,y+43)],10,'SA')
 for j,x in [(1,137),(2,258)]:
  bs(s,'HVAC_FILTER',x,y+43,6,15)
  inst(s,'HVAC_PDT',x,y+22,f'PDT-F{j}-{c}',2.4)
  inst(s,'HVAC_PDI',x,y+65,f'PDI-F{j}-{c}',2.4)
  for dx,sy in [(-8,-1),(8,1)]:
   s.line([(x+dx,y+43),(x+dx,y+22),(x+sy*3.5,y+22)],'INST',.2)
   s.line([(x+dx,y+48),(x+dx,y+65),(x+sy*3.5,y+65)],'INST',.2)
 bs(s,'HVAC_FAN',385,y+43,13,13)
 inst(s,'HVAC_DPT',368,y+22,'DPT-SF-'+c,2.4);inst(s,'HVAC_VS',461,y+22,'VS-PAU-'+c,2.4)
 s.line([(374,y+43),(357,y+43),(357,y+22),(364.5,y+22)],'INST',.2)
 s.line([(396,y+43),(405,y+43),(405,y+22),(371.5,y+22)],'INST',.2)
 s.line([(457.5,y+22),(426,y+31),(392,y+39)],'INST',.2)
 s.text(385,y+66,'SF-'+c,2.4,'INK',False,'center')

section_heading(s,560,43,'B  OUTDOOR-AIR FILTER / COMMON DUCTS',263)
pd(s,[(572,113),(811,113)],10,'OA');bs(s,'HVAC_FILTER',687,113,6,17)
inst(s,'HVAC_PDT',687,84,'PDT-OA-01',2.6);inst(s,'HVAC_PDI',687,145,'PDI-OA-01',2.6)
for dx,sgn in [(-11,-1),(11,1)]:
 s.line([(687+dx,113),(687+dx,84),(687+sgn*3.5,84)],'INST',.2)
 s.line([(687+dx,119),(687+dx,145),(687+sgn*3.5,145)],'INST',.2)
s.text(571,167,'PDT = AI TO HPCP; PDI = LOCAL GAUGE',2.6,'INST',True)
pd(s,[(572,204),(811,204)],9,'SA');inst(s,'HVAC_FIT',633,204,'FIT-SA-01',2.5);inst(s,'HVAC_TT',742,204,'TT-SA-01',2.5)
pd(s,[(811,255),(572,255)],9,'RA')
for x,blk,tg in [(604,'HVAC_FIT','FIT-RA-01'),(688,'HVAC_TT','TT-RA-01'),(781,'HVAC_RHT','RHT-RA-01')]:inst(s,blk,x,255,tg,2.5)
s.para(560,283,'Filter taps measure pressure across each filter, not between rooms. Fan DP proves the operating fan path; VS monitors fan / unit vibration. Alarm thresholds and OEM signal type TBC.',257,2.6)

section_heading(s,18,340,'C  EXTRACT / BASEMENT FAN PROOF',248)
pd(s,[(32,391),(258,391)],10,'EA');bs(s,'HVAC_FAN',113,391,15,15)
inst(s,'HVAC_DPT',80,369,'DPT-fan',2.7);inst(s,'HVAC_VS',207,369,'VS-fan',2.7)
s.line([(99,391),(63,391),(63,369),(76.5,369)],'INST',.2)
s.line([(127,391),(143,391),(143,369),(83.5,369)],'INST',.2)
s.line([(203.5,369),(177,381),(120,386)],'INST',.2)
s.para(22,418,'Tag suffixes: EF-03-01/02; EF-09-01/02; EF-01-01. Each has DPT- and VS- tags. Basement: SF-B1-01/02 and EF-B1-01/02 use the same convention.',239,2.7)
s.para(22,466,'Fan start / run / fault / ready / local-auto / E-stop and damper proofs are listed in I/O. CAG duty / quantity and basement duties remain pending.',239,2.7)

section_heading(s,291,340,'D  HEATER AIRFLOW / HIGH-LIMIT SAFETY',247)
pd(s,[(305,407),(525,407)],12,'SA');bs(s,'HVAC_EH',420,407,19,16)
inst(s,'HVAC_AFS',343,378,'AFS-EH-nn',2.7);inst(s,'HVAC_TSHH',462,378,'TSHH-EH-nn',2.7)
s.line([(343,381.5),(343,407)],'INST',.2);s.line([(462,381.5),(431,400)],'INST',.2)
bs(s,'HVAC_AD',395,413,5,5);s.text(395,428,'AD-Hnn',2.6,'INK',False,'center')
s.para(295,445,'nn = 04, 05, 06, 07, 03, COM-01. Six AFS DI points are retained from Rev07. Each heater retains independent TSHH; loss of proof / high limit switches heating off.',239,2.7)
s.para(295,493,'AFS proof technology, setpoint and OEM hardwired wiring to be selected. PLC demand cannot override local safety.',239,2.6)

section_heading(s,560,340,'E  PRELIMINARY HPCP I/O',263)
counts={t:sum(q['type']==t for q in IO) for t in ['AI','AO','DI','DO']}
rows=[[t,str(n),str(ceil(n*.2)),str(n+ceil(n*.2))] for t,n in counts.items()]
yy=table(s,560,350,263,['Type','Points','Spare >=20%','Channels'],rows,[.65,.8,1.25,1],2.6,12)
s.para(560,yy+13,'COMM: 3 interfaces; separate from wired channel totals. Signals report to dedicated HPCP-01 PLC / HMI-01 and BMS / SCADA. Final protocol and allocation TBC.',258,2.7)
s.para(560,yy+59,'CONFIRMED FIRE: stop every HVAC fan and heater. No automatic fire extraction / post-fire purge. Reset and damper fire positions follow the approved cause-and-effect.',258,2.7,'INK',True)
note_footer(s,'Instrument glyphs are functional symbols, not equipment dimensions. AFS additions are explicit proposed OEM protection / monitoring provisions. Full tags: Excel / CSV registers. Room TT / RHT / DPT locations: D-007.');SHEETS.append(s)

from engineering_rev11 import enhance
enhance(globals())
from routing_sheets_rev11 import append_sheets
append_sheets(globals())
from sheets_rev12 import enhance as enhance_rev12
enhance_rev12(globals())

USED_MODELS={n:m for n,m in MODELS.items() if any(op[0]=='place' and op[1] is m for sheet in SHEETS for op in sheet.ops)}
export_pdf(SHEETS);export_cad(SHEETS,USED_MODELS)
original_colors=COL.copy()
COL.update({k:('#B5B5B5' if k=='ARCH' else '#666666' if k in ['DIM','NOTE'] else '#000000') for k in COL})
export_pdf(SHEETS,monochrome=True)
COL.update(original_colors)
doc=ezdxf.readfile(OUT/'Administration_HVAC_Detailed_Layout.dxf');audit=doc.audit();assert not audit.errors,[e.message for e in audit.errors]
assert len(SHEETS)==32
for rid,r in ROOMS.items():
 for air,total in [('SA',r['sa']),('RA',r['ra'])]:
  q=sum(num(t['flow_l_s']) for t in TERMINALS if t['room']==rid and t['air_type']==air)
  assert abs(q-total)<1e-5,(rid,air,q,total)
pdf=fitz.open(OUT/'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf');review=OUT/'review';review.mkdir(exist_ok=True)
for i,p in enumerate(pdf,1):
 assert abs(p.rect.width/MM-PW)<.01 and abs(p.rect.height/MM-PH)<.01
 p.get_pixmap(matrix=fitz.Matrix(2100/p.rect.width,2100/p.rect.width)).save(review/f'D-{i:02d}.png')
pdf[0].get_pixmap(matrix=fitz.Matrix(2500/pdf[0].rect.width,2500/pdf[0].rect.width)).save(OUT/'Administration_HVAC_Overview.png')
pdf[4].get_pixmap(matrix=fitz.Matrix(3000/pdf[4].rect.width,3000/pdf[4].rect.width)).save(OUT/'Administration_HVAC_South_West_Detail.png')
assert len({r['tag'] for r in COMPONENTS})==len(COMPONENTS)
assert len({r['tag'] for r in INSTRUMENTS})==len(INSTRUMENTS)
assert len({r['tag'] for r in IO})==len(IO)
assert {q['tag'] for q in STATIONS if q['block']=='HVAC_AD'} <= {r['tag'] for r in COMPONENTS}
qa={'revision':12,'instrumentation_coverage':INSTRUMENTATION_QA,'engineering_rev12':ENGINEERING_REV12,'native_dimensions':NATIVE_DIM_COUNT,'sheets':len(SHEETS),'CAD_blocks':len(BLOCKS),'reference_vector_symbols':list(REF['symbols']),'model_variants':list(USED_MODELS),'DXF_audit':'passed','room_terminal_totals':'passed','dimensions':'A1 landscape','annotation_method':'Continuous topology-aware profiles / separate instruments / access tags / match lines','duct_geometry':GEOMETRY_QA,'branch_device_body_or_AD_wall_checks':{'count':len(DEVICE_QA),'result':'passed'},'common_probe_attachment_checks':{'count':0,'result':'Roof coordinates pending'},'common_probe_functional_references':{'count':len(INSTRUMENT_LOCATIONS),'drawing':'D-012'},'access_doors':21,'retained_heater_airflow_proof_DI':6,'io_counts':counts,'flows_and_selected_sizes':'Room duties retained; changed section sizes and terminal positions documented in Rev11 registers / D-021','routing_revision':'Rev11_route_changes.csv','roof_riser_proposals':15,'distribution_option':'Roof common mains / separate room drops; user selected','terminal_moves':'Rev11_terminal_changes.csv','coordination_basis':COORDINATION_BASIS,'pressure_OA_levels_catalogues':'Pending'}
(OUT/'drawing_validation.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa))
