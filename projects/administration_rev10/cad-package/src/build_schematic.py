"""Rebuild editable A1 HVAC schematic / layout drawings from explicit design data.
Install: pip install ezdxf reportlab pymupdf pypdf
Run from the extracted package: python cad-package/src/build_schematic.py
All geometry / tags are proposed coordination inputs; see drawing design holds.
"""
from pathlib import Path
from math import sqrt,pi,atan2,cos,sin,ceil,hypot,log10
import json,csv,argparse
import fitz,ezdxf
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument("--output-dir",default=str(BASE.parent));ap.add_argument("--input-design",default=str(BASE/"inputs/Administration_design_basis.json"));ap.add_argument("--architecture",default=str(BASE/"inputs/ADMIN_BUILDING_LAYOUT.pdf"));args=ap.parse_args()
OUT=Path(args.output_dir);OUT.mkdir(parents=True,exist_ok=True);TMP=OUT/"review";TMP.mkdir(exist_ok=True)
DATA=json.loads(Path(args.input_design).read_text());ROOMS=DATA["rooms"];BYID={r["id"]:r for r in ROOMS}
MM=72/25.4;W,H=841,594
COL={"SA":"#239321","RA":"#1567BD","EA":"#B14B15","OA":"#597D96","RL":"#765196","INST":"#764070","CTRL":"#735779","ARCH":"#B5B7BB","INK":"#171C25","DIM":"#5A5D63","PENDING":"#A23A34","FILL":"#F0F3F5"}
LAYER={k:("A-ARCH" if k=="ARCH" else "M-"+k) for k in COL}
ACI={"SA":5,"RA":3,"EA":30,"OA":4,"RL":6,"INST":6,"CTRL":6,"ARCH":8,"INK":7,"DIM":8,"PENDING":1,"FILL":9}
fontpath=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
if fontpath.exists():
 pdfmetrics.registerFont(TTFont("HV",str(fontpath)));pdfmetrics.registerFont(TTFont("HVB",str(fontpath.with_name("DejaVuSans-Bold.ttf"))))
else:pass
FONT="HV" if fontpath.exists() else "Helvetica";BOLD="HVB" if fontpath.exists() else "Helvetica-Bold"
SECTIONS=[];FITTINGS=[];COMPONENTS={};INSTRUMENTS={};TERMINALS=[]

def vel(q,w,h=None):return q/1000/(w*(h or w)/1e6 if h else pi*(w/1000)**2/4)
def friction(q,w,h=None):
 v=vel(q,w,h);dh=2*w*h/(w+h)/1000 if h else w/1000;Re=1.2*v*dh/1.81e-5;ff=.02
 if q<=0:return 0
 for _ in range(20):ff=1/(-2*log10(.00009/(3.7*dh)+2.51/(Re*sqrt(ff))))**2
 return ff*1.2*v*v/(2*dh)
def addcomp(tag,service,basis,status="Proposed; OEM selection TBC"):
 COMPONENTS[tag]={"tag":tag,"service":service,"basis":basis,"selection_status":status}
def addinst(tag,parameter,location,basis,io="AI",status="Required",action="Monitor / alarm; final range and limits TBC"):
 INSTRUMENTS[tag]={"tag":tag,"parameter":parameter,"location":location,"io":io,"basis":basis,"provision":status,"action":action}

class Scene:
 def __init__(self,w=W,h=H):self.w=w;self.h=h;self.ops=[]
 def line(self,pts,k="INK",lw=.25,dash=False):self.ops.append(("line",pts,k,lw,dash))
 def rect(self,x,y,w,h,k="INK",fill=None,lw=.25,dash=False):
  self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],k,fill,lw,dash)
 def poly(self,pts,k="INK",fill=None,lw=.25,dash=False):self.ops.append(("poly",pts,k,fill,lw,dash))
 def circle(self,x,y,r,k="INK",lw=.25,fill=None):self.ops.append(("circle",x,y,r,k,lw,fill))
 def text(self,x,y,t,size=2.5,k="INK",bold=False,align="left",angle=0):self.ops.append(("text",x,y,str(t),size,k,bold,align,angle))
 def para(self,x,y,t,width,size=2.5,k="INK",bold=False,leading=1.45):
  lines=[];line=""
  for word in t.split():
   test=(line+" "+word).strip()
   if line and pdfmetrics.stringWidth(test,BOLD if bold else FONT,size*MM)>width*MM:lines.append(line);line=word
   else:line=test
  if line:lines.append(line)
  for i,a in enumerate(lines):self.text(x,y+i*size*leading,a,size,k,bold)
  return len(lines)*size*leading
 def arrow(self,a,b,k="INK",lw=.25,z=2.5,dash=False):
  self.line([a,b],k,lw,dash);angle=atan2(b[1]-a[1],b[0]-a[0]);x,y=b
  self.poly([(x,y),(x-z*cos(angle)+z*.45*sin(angle),y-z*sin(angle)-z*.45*cos(angle)),(x-z*cos(angle)-z*.45*sin(angle),y-z*sin(angle)+z*.45*cos(angle))],k,COL[k],.1)
 def leader(self,x,y,tx,ty,text,k="INK",size=2.4):
  self.line([(x,y),(tx,ty+1.2)],k,.2);self.circle(x,y,.6,k);self.text(tx,ty,text,size,k)
 def duct(self,points,width,k="SA",lw=.32,filled=False):
  # Orthogonal mitered duct outline; width is the drawn clear width.
  normals=[]
  for a,b in zip(points,points[1:]):
   dx=b[0]-a[0];dy=b[1]-a[1];L=hypot(dx,dy)
   normals.append((-dy/L,dx/L))
  sides=[]
  for sign in [1,-1]:
   q=[]
   for i,p in enumerate(points):
    n=normals[0] if i==0 else normals[-1] if i==len(points)-1 else (normals[i-1][0]+normals[i][0],normals[i-1][1]+normals[i][1])
    q.append((p[0]+sign*width/2*n[0],p[1]+sign*width/2*n[1]))
   sides.append(q)
  self.poly(sides[0]+sides[1][::-1],k,{"SA":"#EAF5FA","RA":"#EFF7EE","EA":"#FBF1E9","OA":"#EFF4F7"}.get(k) if filled else None,lw)
  for a,b in zip(points,points[1:]):
   L=hypot(b[0]-a[0],b[1]-a[1])
   if L>width*2.2:
    aa=(a[0]+.45*(b[0]-a[0]),a[1]+.45*(b[1]-a[1]));bb=(a[0]+.59*(b[0]-a[0]),a[1]+.59*(b[1]-a[1]));self.arrow(aa,bb,k,lw,z=max(width*.15,.8))
  return sides
 def reducer(self,x,y,a,b,length=12,k="SA",vertical=False):
  pts=[(-length/2,-a/2),(length/2,-b/2),(length/2,b/2),(-length/2,a/2)]
  if vertical:pts=[(-yy,xx) for xx,yy in pts]
  self.poly([(x+xx,y+yy) for xx,yy in pts],k,None,.3)
 def damper(self,x,y,tag="",k="SA",motor=False,size=7,vertical=False,fire=False):
  self.rect(x-size/2,y-size/2,size,size,k,"#FFFFFF",.3);self.line([(x-size*.38,y+size*.38),(x+size*.38,y-size*.38)],k,.3)
  if motor:self.rect(x-size*.3,y-size*1.05,size*.6,size*.45,k,"#FFFFFF",.2);self.text(x,y-size*.69,"M",size*.28,k,True,"center")
  if fire:self.text(x,y+size*.22,"F",size*.38,"PENDING",True,"center")
  if tag:self.text(x,y+size*.95,tag,size*.3,k,False,"center")
 def fan(self,x,y,tag,k="SA",r=9):
  self.circle(x,y,r,k,.45,"#FFFFFF")
  for a in [0,2*pi/3,4*pi/3]:self.line([(x,y),(x+r*.72*cos(a),y+r*.72*sin(a))],k,.4)
  if tag:self.text(x,y+r+5,tag,2.7,k,True,"center")
 def filter(self,x,y,w,h,tag,k="INK"):
  self.rect(x,y,w,h,k,"#FFFFFF",.3)
  for i in range(1,6):self.line([(x+1,y+i*h/7),(x+w-1,y+(i+.65)*h/7)],k,.18)
  if tag:self.text(x+w/2,y+h+5,tag,2.5,k,False,"center")
 def sensor(self,x,y,tag,label=None,size=5,k="INST"):
  self.circle(x,y,size,k,.25,"#FFFFFF");self.text(x,y+size*.3,label or tag.split("-")[0],size*.44 if size<50 else size*.55,k,True,"center")
  self.text(x,y-size-max(2,size*.3),tag,size*.44 if size<50 else max(110,size*.75),k,False,"center")
 def terminal(self,x,y,tag,kind="SD",size=9,k="SA"):
  self.rect(x-size/2,y-size/2,size,size,k,"#FFFFFF",.35)
  if kind=="SD":self.line([(x-size*.5,y-size*.5),(x+size*.5,y+size*.5)],k,.2);self.line([(x-size*.5,y+size*.5),(x+size*.5,y-size*.5)],k,.2)
  else:
   for d in [-.3,0,.3]:self.line([(x-size*.4,y+size*d),(x+size*.4,y+size*d)],k,.2)
  if tag:self.text(x,y+size*.8,tag,size*.26,k,True,"center")
 def flex(self,x,y,k="SA",w=7,h=12):
  self.rect(x-w/2,y-h/2,w,h,k,"#FFFFFF",.25)
  for i in [-.25,0,.25]:self.line([(x+w*i-w*.1,y-h*.4),(x+w*i+w*.1,y-h*.1),(x+w*i-w*.1,y+h*.2),(x+w*i+w*.1,y+h*.4)],k,.18)
 def silencer(self,x,y,w=22,h=16,k="SA",tag=""):
  self.rect(x,y,w,h,k,"#FFFFFF",.3)
  for a in [1,2,3]:self.line([(x+3,y+h*a/4),(x+w-3,y+h*a/4)],k,.8)
  if tag:self.text(x+w/2,y+h+5,tag,2.4,k,False,"center")
 def heater(self,x,y,tag,k="SA",w=15,h=18):
  self.rect(x,y,w,h,k,"#FFFFFF",.3)
  pts=[(x+2,y+h*.15)]
  for i in range(7):pts.append((x+2+(i+1)*(w-4)/7,y+h*(.8 if i%2==0 else .15)))
  self.line(pts,"EA",.4);self.text(x+w/2,y+h+(5 if w<100 else 160),tag,2.4 if w<100 else 120,"EA",True,"center")
 def access(self,x,y,tag="AD",k="INK",size=6):
  self.rect(x-size/2,y-size/2,size,size,k,None,.2,dash=True);self.text(x,y+size*.9,tag,size*.32,k,False,"center")
 def place(self,scene,x,y,denom=50,clip=None):self.ops.append(("place",scene,x,y,denom,clip or (0,0,scene.w,scene.h)))


def frame(title,number,index,count,notes,scale="NTS"):
 s=Scene();s.rect(10,10,821,574,"INK",None,.55);s.line([(675,10),(675,584)],"INK",.4)
 s.text(18,23,title.upper(),4.2,"INK",True);s.line([(18,29),(665,29)],"INK",.2)
 s.text(683,23,"GENERAL NOTES / DESIGN HOLDS",3,"INK",True)
 yy=34
 for i,t in enumerate(notes,1):yy+=s.para(683,yy,f"{i}. {t}",140,2.5)+4
 if yy>345:raise ValueError("Right notes overflow: "+number)
 s.line([(675,360),(831,360)],"INK",.3)
 s.para(683,373,"FOR COORDINATION - NOT FOR CONSTRUCTION",140,3.3,"PENDING",True)
 s.para(683,391,"Unconfirmed routes, levels, outdoor air and OEM selections: Insufficient data to verify.",140,2.4,"PENDING")
 s.line([(675,416),(831,416)],"INK",.25)
 s.text(683,426,"CLIENT / DESIGN BASIS",2.1,"DIM",True);s.text(683,435,"TAQA TRANSMISSION",3.5,"INK",True)
 s.para(683,445,DATA["project"],140,2.6)
 s.line([(675,469),(831,469)],"INK",.25);s.text(683,478,"DRAWING TITLE",2.1,"DIM",True);s.para(683,488,title,140,3.2,"INK",True)
 s.line([(675,518),(831,518)],"INK",.25);s.text(683,527,"DRAWING NUMBER",2.1,"DIM",True);s.text(683,537,number,3.5,"INK",True)
 for y in [543,560,574]:s.line([(675,y),(831,y)],"INK",.2)
 s.text(683,551,f"REV 09   |   07 Oct 2026   |   {index}/{count}",2.5,"INK",True)
 s.text(683,568,"SCALE "+scale+"   |   A1 / mm / L/s / Pa",2.4)
 s.text(683,581,"Prepared: draft   Checked / approved: pending",2.1,"DIM")
 s.text(18,579,"SOURCE: HAP / ADMIN ARCHITECTURE / C-H-SS-001 Rev0. All new equipment and instrument tags are proposed.",2.2,"DIM")
 return s

BASE_NOTES=["All duct sizes are clear internal W x H in mm; round sizes are diameters. Add approved insulation outside these dimensions.","HAP reference supply 3697.80 L/s. Assumed return 3006.68 L/s. Final IAQ, outdoor air, revised thermal loads and OEM fan pressure remain open.","Room targets: +50 Pa normal rooms; +25 Pa kitchen, toilet and clean-agent relative to outdoors. Actual pressure / outward paths are unverified.","Confirmed fire stops the entire HVAC system. Fire ESD restart requires local manual reset; post-fire purge is a separate approved design.","Reference substation drawings guide drafting style only. Project requirements follow the supplied TAQA specification and accepted room basis."]

def table(s,x,y,w,headers,rows,ratios=None,size=2.35,rh=8):
 ratios=ratios or [1]*len(headers);xs=[x]
 for r in ratios:xs.append(xs[-1]+w*r/sum(ratios))
 hh=13;s.rect(x,y,w,hh,"INK","#F0F3F5",.25)
 for j,h in enumerate(headers):s.para(xs[j]+2,y+4,h,xs[j+1]-xs[j]-4,size,"INK",True,1.15)
 yy=y+hh
 for row in rows:
  s.line([(x,yy+rh),(x+w,yy+rh)],"DIM",.12)
  for j,t in enumerate(row):s.para(xs[j]+2,yy+3.2,str(t),xs[j+1]-xs[j]-4,size,"INK",False,1.15)
  yy+=rh
 return yy

def pdf_render_scene(c,s,origin=(0,0),factor=1,clip=None):
 c.saveState();c.translate(origin[0]*MM,(H-origin[1])*MM);c.scale(factor*MM,-factor*MM)
 if clip:
  p=c.beginPath();p.rect(clip[0],clip[1],clip[2]-clip[0],clip[3]-clip[1]);c.clipPath(p,stroke=0,fill=0)
 for op in s.ops:
  typ=op[0]
  if typ=="place":
   _,sub,x,y,den,b=op;c.saveState();c.translate(x,y);c.scale(1/den,1/den);p=c.beginPath();p.rect(0,0,b[2]-b[0],b[3]-b[1]);c.clipPath(p,stroke=0,fill=0);c.translate(-b[0],-b[1]);_pdf_ops(c,sub.ops);c.restoreState()
  else:_pdf_ops(c,[op])
 c.restoreState()
def _pdf_ops(c,ops):
 for op in ops:
  typ=op[0]
  if typ in ("line","poly"):
   pts,k=op[1:3];fill=None
   if typ=="line":lw,dash=op[3:5]
   else:fill,lw,dash=op[3:6]
   c.setStrokeColor(HexColor(COL[k]));c.setLineWidth(lw);c.setDash([2*max(1,lw),max(1,lw)] if dash else [])
   p=c.beginPath();p.moveTo(*pts[0])
   for pt in pts[1:]:p.lineTo(*pt)
   if typ=="poly":p.close()
   if fill:c.setFillColor(HexColor(fill))
   c.drawPath(p,stroke=1,fill=1 if fill else 0)
  elif typ=="circle":
   _,x,y,r,k,lw,fill=op;c.setStrokeColor(HexColor(COL[k]));c.setLineWidth(lw);c.setDash([])
   if fill:c.setFillColor(HexColor(fill))
   c.circle(x,y,r,stroke=1,fill=1 if fill else 0)
  elif typ=="text":
   _,x,y,t,z,k,bold,align,angle=op;c.saveState();c.translate(x,y);c.scale(1,-1);c.rotate(angle);c.setFont(BOLD if bold else FONT,z);c.setFillColor(HexColor(COL[k]));
   for i,l in enumerate(t.split("\n")):getattr(c,{"left":"drawString","center":"drawCentredString","right":"drawRightString"}[align])(0,-i*z*1.4,l)
   c.restoreState()

def make_doc():
 doc=ezdxf.new("R2013");doc.units=ezdxf.units.MM;doc.header["$LTSCALE"]=1;doc.header["$MEASUREMENT"]=1
 if "DASHED" not in doc.linetypes:doc.linetypes.new("DASHED",dxfattribs={"description":"Dashed control / unconfirmed","pattern":[4,2,-2]})
 for k,l in LAYER.items():doc.layers.new(l,dxfattribs={"color":ACI[k],"true_color":int(COL[k][1:],16),"lineweight":25 if k!="ARCH" else 9,"linetype":"DASHED" if k=="CTRL" else "CONTINUOUS"})
 doc.layers.new("VIEWPORT",dxfattribs={"color":8,"plot":False})
 return doc

def dxf_scene(target,s,offset=(0,0)):
 def p(a):return a[0]+offset[0],s.h-a[1]+offset[1]
 for op in s.ops:
  typ=op[0]
  if typ=="place":continue
  k=op[2] if typ in ["line","poly"] else op[4] if typ=="circle" else op[5]
  attrs={"layer":LAYER[k]}
  if typ=="line":
   if op[4]:attrs["linetype"]="DASHED"
   for a,b in zip(op[1],op[1][1:]):target.add_line(p(a),p(b),dxfattribs=attrs)
  elif typ=="poly":
   if op[5]:attrs["linetype"]="DASHED"
   target.add_lwpolyline([p(a) for a in op[1]],close=True,dxfattribs=attrs)
  elif typ=="circle":target.add_circle(p((op[1],op[2])),op[3],dxfattribs=attrs)
  elif typ=="text":
   _,x,y,t,z,k,bold,align,angle=op
   for i,a in enumerate(t.split("\n")):
    e=target.add_text(a,dxfattribs={**attrs,"height":z,"rotation":angle,"style":"Standard"})
    from ezdxf.enums import TextEntityAlignment
    e.set_placement(p((x,y+i*z*1.4)),align={"left":TextEntityAlignment.LEFT,"right":TextEntityAlignment.RIGHT,"center":TextEntityAlignment.CENTER}[align])

def export_schematic(sheets,path):
 doc=make_doc();m=doc.modelspace()
 for i,s in enumerate(sheets):
  dxf_scene(m,s,(i*900,0));l=doc.layouts.new(f"S{i+1:02d}_A1");l.page_setup(size=(841,594),margins=(0,0,0,0),units="mm");l.add_viewport(center=(420.5,297),size=(841,594),view_center_point=(i*900+420.5,297),view_height=594,dxfattribs={"layer":"VIEWPORT"})
 doc.set_modelspace_vport(height=594,center=(420.5,297));doc.saveas(path)

def export_detail(sheets,plan,path):
 doc=make_doc();dxf_scene(doc.modelspace(),plan)
 for i,s in enumerate(sheets):
  l=doc.layouts.new(f"D{i+1:02d}_A1");l.page_setup(size=(841,594),margins=(0,0,0,0),units="mm");dxf_scene(l,s)
  for op in s.ops:
   if op[0]=="place":
    _,sub,x,y,den,b=op;ww=(b[2]-b[0])/den;hh=(b[3]-b[1])/den
    l.add_viewport(center=(x+ww/2,H-y-hh/2),size=(ww,hh),view_center_point=((b[0]+b[2])/2,plan.h-(b[1]+b[3])/2),view_height=b[3]-b[1],dxfattribs={"layer":"VIEWPORT"})
 doc.set_modelspace_vport(height=23000,center=(10000,9750));doc.saveas(path)

# Real model coordinates use the supplied architecture's 20,000 x 19,500 mm outline.
PLAN=Scene(20000,19500)
def P(x,y):return x,19500-y

def arch_background():
 page=fitz.open(args.architecture)[0];x0,y0,scale=342.12,132.17,20000/2184
 def pp(p):return (p.x-x0)*scale,(p.y-y0)*scale
 for d in page.get_drawings():
  rr=d['rect']
  if rr.x0<330 or rr.x1>2540 or rr.y0<120 or rr.y1>2275:continue
  for it in d['items']:
   if it[0]=='l':PLAN.line([pp(it[1]),pp(it[2])],'ARCH',4)
   elif it[0]=='re':
    r=it[1];PLAN.poly([pp(r.tl),pp(r.tr),pp(r.br),pp(r.bl)],'ARCH',None,4)
   elif it[0]=='c':
    a,b,c,e=it[1:];q=[]
    for j in range(13):
     t=j/12;u=1-t;q.append(pp(fitz.Point(u**3*a.x+3*u*u*t*b.x+3*u*t*t*c.x+t**3*e.x,u**3*a.y+3*u*u*t*b.y+3*u*t*t*c.y+t**3*e.y)))
    PLAN.line(q,'ARCH',4)
 arch_labels=[(4000,19200,'ELECTRICAL PANEL ROOM'),(14300,19300,'OPERATOR CONSOLE ROOM'),(2700,7800,'MEETING'),(8800,7800,'TELECOM'),(12900,7650,'TOILETS'),(18800,7900,'KITCHEN'),(14100,4200,'BEDROOM / REST'),(18200,4200,'CLEAN AGENT'),(11800,10100,'CORRIDOR')]
 for x,y,t in arch_labels:PLAN.text(*P(x,y),t,145,'ARCH',True,'center')
 # Overall dimensions traced from the source, not inferred from HAP areas.
 for a,b,lab in [((0,20600),(20000,20600),'20000 - SOURCE ARCHITECTURE'),((21200,0),(21200,19500),'19500 - SOURCE ARCHITECTURE')]:
  PLAN.line([P(*a),P(*b)],'DIM',8)
  if a[1]==b[1]:
   for x in [a[0],b[0]]:PLAN.line([P(x,19500),P(x,20800)],'DIM',5)
   PLAN.text(*P(10000,20800),lab,160,'DIM',False,'center')
  else:
   for y in [0,19500]:PLAN.line([P(20000,y),P(21400,y)],'DIM',5)
   PLAN.text(*P(21600,9750),lab,160,'DIM',False,'center',90)
arch_background()

# North-room take-offs occur before the corridor run, keeping corridor duct widths practical.
SA_MAIN=[
 ('SA-M01',[(1800,19000),(1800,16600)],3697.8,1200,650,(300,18400)),
 ('SA-M02',[(1800,16600),(1800,13200)],3033.0,1100,575,(250,15500)),
 ('SA-M03',[(1800,13200),(1800,9300),(3500,9300)],2255.3,950,500,(2500,10400)),
 ('SA-M04',[(3500,9300),(7000,9300)],1806.1,850,425,(4700,9850)),
 ('SA-M05',[(7000,9300),(11000,9300)],921.5,650,300,(8200,9850)),
 ('SA-M06',[(11000,9300),(13200,9300)],503.3,500,250,(11600,9850)),
 ('SA-M07',[(13200,9300),(15500,9300)],457.1,450,250,(13900,9850)),
 ('SA-M08',[(15500,9300),(17800,9300)],288.9,400,200,(16200,9850)),
 ('SA-M09',[(17800,9300),(18500,9300)],141.3,300,200,(17900,10300)),
]
rv=lambda ids:sum(BYID[i]['ra'] for i in ids)
RA_MAIN=[
 ('RA-M01',[(3500,16400),(3500,19000)],rv(['02','05','04','08','06','07']),1400,650,(4400,18400)),
 ('RA-M02',[(3500,12200),(3500,16400)],rv(['05','04','08','06','07']),1200,600,(4400,15100)),
 ('RA-M03',[(4100,8350),(3500,8350),(3500,12200)],rv(['04','08','06','07']),850,550,(4200,11100)),
 ('RA-M04',[(7500,8350),(4100,8350)],rv(['08','06','07']),800,450,(4750,8030)),
 ('RA-M05',[(11300,8350),(7500,8350)],rv(['06','07']),650,300,(8200,8030)),
 ('RA-M06',[(15350,8350),(11300,8350)],rv(['07']),450,225,(12200,8030)),
]

def section(tag,points,q,w,h,k,labelpt=None,role='Main',room=None,routebasis='Proposed 2D centre-line; vertical length TBC'):
 L=sum(hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(points,points[1:]))/1000
 PLAN.duct([P(*p) for p in points],w,k,12,True)
 for j,p in enumerate(points[1:-1],1):
  ft=f'F-{tag}-B{j:02d}';FITTINGS.append({'tag':ft,'section':tag,'type':'90 deg miter bend / turning vanes','x_mm':p[0],'y_mm':p[1],'loss_K':'TBC selected fitting','basis':'Proposed geometry'})
  PLAN.line([P(p[0]-w*.3,p[1]-w*.3),P(p[0]+w*.3,p[1]+w*.3)],k,7)
 if labelpt:
  PLAN.text(*P(*labelpt),f'{tag} {w}x{h if h else "D"}\n{q:.2f} L/s | {vel(q,w,h):.2f} m/s\nLh {L:.2f} m | BOD TBC',110,k,True)
 SECTIONS.append({'tag':tag,'air_type':k,'role':role,'room':room or '', 'flow_l_s':round(q,6),'width_mm':w,'height_mm':h or '', 'diameter_mm':w if not h else '', 'velocity_m_s':round(vel(q,w,h),5),'friction_pa_m':round(friction(q,w,h),5),'horizontal_length_m':round(L,4),'vertical_length_m':'TBC','level':'BOD TBC','route_basis':routebasis,'points_mm':json.dumps(points)})
 return L
for tag,pts,q,w,h,lp in SA_MAIN:section(tag,pts,q,w,h,'SA',lp)
for tag,pts,q,w,h,lp in RA_MAIN:section(tag,pts,q,w,h,'RA',lp)
for arr,k in [(SA_MAIN,'SA'),(RA_MAIN,'RA')]:
 for i in range(len(arr)-1):
  p=arr[i][1][-1] if k=='SA' else arr[i+1][1][-1]
  PLAN.reducer(*P(*p),arr[i][3],arr[i+1][3],400,k,arr[i][1][-2][0]==arr[i][1][-1][0])
  FITTINGS.append({'tag':f'F-{k}-RED-{i+1:02d}','section':arr[i][0],'type':'Transition / reducer','x_mm':p[0],'y_mm':p[1],'loss_K':'TBC geometry / ASHRAE fitting','basis':'Nominal transition shown; final length TBC'})
PLAN.rect(*P(1100,19350),1400,650,'SA',None,12);PLAN.text(*P(1000,19900),'SA RISER FROM ROOF: 1200x650',130,'SA',True)
PLAN.rect(*P(2650,19350),1700,650,'RA',None,12);PLAN.text(*P(2950,19550),'RA RISER TO ROOF: 1400x650',130,'RA',True)

SA_POINTS={'02':[(2700,18000),(7100,18000),(2700,13100),(7100,13100)],'05':[(10900,18100),(16600,18100),(18300,15800),(10900,13600),(16600,13600)],'04':[(1800,6600),(4300,4300),(1900,1900)],'08':[(6500,6500),(10600,6500),(6500,4200),(10600,4200),(6500,1700),(10600,1700)],'06':[(5400,9800),(14700,9800),(16300,6000)],'07':[(13900,3200)],'09':[(13200,7000),(13200,5200)],'03':[(18600,6600)],'01':[(18100,3200)]}
RA_POINTS={'02':[(1200,16800),(7700,16800),(1200,11900),(7700,11900)],'05':[(9700,18800),(19000,18800),(9700,14600),(19000,12500),(15100,10700)],'04':[(700,7000),(4900,4300),(700,1000)],'08':[(5900,7100),(11200,7100),(5900,4600),(11200,4600),(5900,900),(11200,900)],'06':[(3100,8550),(9700,8550),(17200,8550),(15100,5600)],'07':[(14400,1400)]}
SA_TAKE={'02':(1800,16600),'05':(1800,13200),'04':(3500,9300),'08':(7000,9300),'06':(11000,9300),'09':(13200,9300),'07':(15500,9300),'03':(17800,9300),'01':(18500,9300)}
RA_TAKE={'02':(3500,16400),'05':(3500,12200),'04':(4100,8350),'08':(7500,8350),'06':(11300,8350),'07':(15350,8350)}
SA_HUB={'02':(4800,16600),'05':(14000,13200),'04':(2900,6500),'08':(8500,6300),'06':(11800,9800),'09':(13000,7100),'07':(14100,3600),'03':(18200,7300),'01':(16800,3500)}
RA_HUB={'02':(4400,15700),'05':(14900,12200),'04':(3000,6900),'08':(8900,6900),'06':(13000,8550),'07':(15000,2200)}
INST_POS={'02':(6000,14500),'05':(14600,17100),'04':(2800,5600),'08':(8700,5200),'06':(5700,8900),'07':(13600,2600),'09':(13300,6300),'03':(18300,5800),'01':(17800,2450)}

def device_on_plan(x,y,tag,k='SA',motor=False,fire=False):
 PLAN.damper(*P(x,y),'',k,motor,240,fire=fire);PLAN.text(*P(x+200,y+330),tag,100,'PENDING' if fire else k)
def branch_path(take,hub,rid,k):
 # Explicit orthogonal routes; room devices / separation remain to coordinate in height.
 x,y=take;hx,hy=hub
 if rid=='06' and k=='SA':return [(x,y),(x,hy),(hx,hy)]
 if rid=='01':return [(x,y),(16800,y),(16800,hy),(hx+1,hy)]
 if rid in ['04','08','07','09','03']:return [(x,y),(x,hy),(hx,hy)] if hx!=x else [(x,y),(hx,hy)]
 return [(x,y),(hx,y),(hx,hy)] if hy!=y else [(x,y),(hx,hy)]
def make_headers(hub,points,qeach,w,h,k,rid):
 hx,hy=hub
 for direction in [1,-1]:
  levels=sorted({y for x,y in points if (y-hy)*direction>0},reverse=direction<0)
  a=(hx,hy)
  for j,y in enumerate(levels,1):
   q=sum(qeach for x,yy in points if (yy-y)*direction>=0)
   b=(hx,y);path=[a,b] if k=="SA" else [b,a]
   section(f"{k}-H{rid}-{'U' if direction>0 else 'D'}{j:02d}",path,q,w,h,k,None,"Room header",rid)
   a=b
 for j,(x,y) in enumerate(points,1):
  FITTINGS.append({"tag":f"F-{k}-HDR-{rid}-{j:02d}","section":f"{k}-B{rid}","type":"Header-to-terminal take-off","x_mm":hx,"y_mm":y,"loss_K":"TBC selected fitting","basis":"Proposed"})

for r in ROOMS:
 rid=r['id'];take=SA_TAKE[rid];hub=SA_HUB[rid];path=branch_path(take,hub,rid,'SA')
 label=(11700,10850) if rid=='06' else (hub[0]+350,hub[1]+650)
 section(f'SA-B{rid}',path,r['sa'],r['sw'],r['sh'],'SA',label,'Branch',rid)
 a,b=path[0:2];dx,dy=b[0]-a[0],b[1]-a[1];L=hypot(dx,dy)
 for fac,tg,mot,fire in [(.23,f'VCD-S{rid}',False,False),(.65,f'FSD-S{rid}*',True,True)]:
  if rid=='06':device_on_plan(11200 if fire else 11000,9800 if fire else 9550,tg,'SA',mot,fire)
  else:device_on_plan(a[0]+fac*dx,a[1]+fac*dy,tg,'SA',mot,fire)
 addcomp(f'VCD-S{rid}','Supply branch balancing damper',f'Room GF-{rid}')
 addcomp(f'FSD-S{rid}','Conditional fire/smoke damper at rated penetration','Compartment / cause-and-effect approval required','Conditional; quantity and rating TBC')
 FITTINGS.append({'tag':f'F-SA-TEE-{rid}','section':f'SA-B{rid}','type':'Main-to-room take-off / tee','x_mm':take[0],'y_mm':take[1],'loss_K':'TBC actual fitting','basis':'Proposed'})
 # The branches are explicit plenums; runouts individually carry the terminal flow.
 sdneck=ceil(sqrt(4*(r['sa']/r['n']/1000)/(pi*2))*1000/25)*25
 r['new_neck']=max(150 if rid=='09' else 300,sdneck);r['shown_runout']=r['new_neck']
 make_headers(hub,SA_POINTS[rid],r['sa']/r['n'],r['sw'],r['sh'],'SA',rid)
 for j,(x,y) in enumerate(SA_POINTS[rid],1):
  q=r['sa']/r['n'];hx,hy=hub
  pts=[(hx,y),(x,y)]
  pts=[p for i,p in enumerate(pts) if i==0 or p!=pts[i-1]]
  if len(pts)>1:section(f'SA-R{rid}-{j:02d}',pts,q,r['shown_runout'],None,'SA',None,'Runout',rid)
  PLAN.terminal(*P(x,y),'','SD',600 if rid!='09' else 300,'SA')
  PLAN.text(*P(x+420,y+380),f'SD-{rid}-{j:02d}\n{q:.2f} L/s | D{r["new_neck"]}',105,'SA',True)
  PLAN.access(*P(x-420,y+100),'AD','SA',180)
  addcomp(f'SD-{rid}-{j:02d}','Supply diffuser with integral OBD',f'Room GF-{rid}; {q:.3f} L/s')
  TERMINALS.append({'tag':f'SD-{rid}-{j:02d}','room':rid,'air_type':'SA','flow_l_s':q,'neck_dia_mm':r['new_neck'],'face_w_mm':600 if rid!='09' else 300,'face_h_mm':600 if rid!='09' else 300,'x_mm':x,'y_mm':y,'level':'Ceiling / BOD TBC','catalogue':'TBC; neck chosen for <=2 m/s, model / throw / NC / loss unverified'})
 if r['rn']:
  hub=RA_HUB[rid];take=RA_TAKE[rid];path=branch_path(take,hub,rid,'RA')[::-1]
  section(f'RA-B{rid}',path,r['ra'],r['rw'],r['rh'],'RA',(6100,16000) if rid=='02' else (hub[0]+300,hub[1]-500),'Branch',rid)
  a,b=path[-2:];dx,dy=b[0]-a[0],b[1]-a[1]
  device_on_plan(a[0]+.35*dx,a[1]+.35*dy,f'RCD-R{rid}','RA',True)
  device_on_plan(a[0]+.7*dx,a[1]+.7*dy,f'FSD-R{rid}*','RA',True,True)
  addcomp(f'RCD-R{rid}','Modulating room return damper','Proposed +50 Pa pressure control; provisional fixed-return starting balance')
  addcomp(f'FSD-R{rid}','Conditional fire/smoke damper','Compartment / cause-and-effect approval required','Conditional; quantity and rating TBC')
  FITTINGS.append({'tag':f'F-RA-TEE-{rid}','section':f'RA-B{rid}','type':'Room-to-main junction','x_mm':take[0],'y_mm':take[1],'loss_K':'TBC actual fitting','basis':'Proposed'})
  make_headers(hub,RA_POINTS[rid],r['ra']/r['rn'],r['rw'],r['rh'],'RA',rid)
  for j,(x,y) in enumerate(RA_POINTS[rid],1):
   q=r['ra']/r['rn'];hx,hy=hub;pts=[(x,y),(hx,y)]
   section(f'RA-R{rid}-{j:02d}',pts,q,300,None,'RA',None,'Runout',rid)
   PLAN.terminal(*P(x,y),'','RG',500,'RA');PLAN.text(*P(x+350,y-420),f'RG-{rid}-{j:02d}\n{q:.2f} L/s | D300',105,'RA',True)
   addcomp(f'RG-{rid}-{j:02d}','Ducted return grille with OBD',f'Room GF-{rid}; {q:.3f} L/s')
   TERMINALS.append({'tag':f'RG-{rid}-{j:02d}','room':rid,'air_type':'RA','flow_l_s':q,'neck_dia_mm':300,'face_w_mm':500,'face_h_mm':500,'x_mm':x,'y_mm':y,'level':'Ceiling / BOD TBC','catalogue':'TBC; 60% free area is teaching assumption only'})
 # All room sensors are identifiable in plan and in the signal register.
 ix,iy=INST_POS[rid]
 for j,(pre,label,param) in enumerate([('TT','TT','Dry bulb temperature'),('RHT','RH','Relative humidity'),('DPT','DP','Room pressure vs outdoor')]):
  tag=f'{pre}-GF-{rid}';PLAN.sensor(*P(ix+(j-1)*950,iy),tag,label,110)
  basis='8.4.1 / 15.10.1' if pre=='TT' else '8.4.1 humidity provision' if pre=='RHT' else '7.13.2 / 8.4.1 minimum; added room balancing provision'
  status='Additional proposal' if (pre=='DPT' and rid!='06') or (pre=='RHT' and rid=='01') else 'Required'
  addinst(tag,param,f'GF-{rid} {r["name"]}',basis,status=status)
 PLAN.text(*P(ix,iy-470),f'TARGET +{r["pressure"]:.0f} Pa / OUTDOOR',110,'INST',True,'center')
 if rid in ['04','05','06','07','03']:
  # Heater bodies are in the branch, upstream of all room terminal take-offs.
  hp=branch_path(SA_TAKE[rid],SA_HUB[rid],rid,'SA');aa,bb=hp[0:2]
  cx,cy=(11600,9800) if rid=='06' else (aa[0]+.86*(bb[0]-aa[0]),aa[1]+.86*(bb[1]-aa[1]))
  axial=300 if rid in ['03','06'] else 420
  ww,hh=(r['sw'],axial) if aa[0]==bb[0] and rid!='06' else (axial,r['sw'])
  px,py=P(cx,cy);PLAN.heater(px-ww/2,py-hh/2,f'EH-{rid}','SA',ww,hh)
  addcomp(f'EH-{rid}','Indoor room comfort duct heater','7.8.2; load / losses / high-limit and airflow proof TBC')
  addinst(f'TSHH-EH-{rid}','Heater high temperature limit',f'EH-{rid}','Proposed heater protection','DI','OEM safety provision','Trip / inhibit heater; reset per OEM')

# Dedicated general extract; no clean-agent, kitchen or toilet return junction.
for rid,pts,q,w,h in [('09',[(14700,7000),(14700,7600),(20800,7600)],BYID['09']['ea'],250,200),('03',[(18900,5700),(20800,5700)],BYID['03']['ea'],300,200),('01',[(18600,1500),(20800,1500)],None,300,200)]:
 if q is not None:section(f'EA-B{rid}',pts,q,w,h,'EA',(17700,pts[-1][1]+650),'Extract branch',rid)
 else:PLAN.duct([P(*p) for p in pts],w,'EA',12);PLAN.text(*P(17900,2300),'EA-B01 SIZE / FLOW TBC\nMIN NORMAL 5 ACH = 67.56 L/s',120,'EA',True)
 if rid=='09':
  section('EA-R09-01',[(14200,7000),(14700,7000)],q/2,150,None,'EA',None,'Extract runout','09')
  section('EA-R09-02',[(14200,5200),(14700,5200),(14700,7000)],q/2,150,None,'EA',None,'Extract runout','09')
  egpts=[(14200,7000),(14200,5200)]
 else:egpts=[pts[0]]
 for j,p in enumerate(egpts,1):
  PLAN.terminal(*P(*p),'','EG',300 if rid=='09' else 500,'EA');PLAN.text(*P(p[0]-900,p[1]-430),f'EG-{rid}-{j:02d}\n'+('DUTY / HEIGHT TBC' if q is None else f'{q/len(egpts):.2f} L/s'),110,'EA',True)
  addcomp(f'EG-{rid}-{j:02d}','Dedicated extract grille',f'GF-{rid}; final pickup height / model TBC')
  TERMINALS.append({'tag':f'EG-{rid}-{j:02d}','room':rid,'air_type':'EA','flow_l_s':q/len(egpts) if q is not None else 'TBC','neck_dia_mm':150 if rid=='09' else 'TBC' if rid=='01' else 300,'face_w_mm':300 if rid=='09' else 500,'face_h_mm':300 if rid=='09' else 500,'x_mm':p[0],'y_mm':p[1],'level':'Pickup height TBC','catalogue':'TBC'})
 for j in range(2 if rid!='01' else 1):
  fx=22000;fy=pts[-1][1]+(600 if j==0 else -600) if rid!='01' else pts[-1][1]
  PLAN.duct([P(20800,pts[-1][1]),P(21200,pts[-1][1]),P(21200,fy),P(21700,fy)],200 if rid=='09' else 300,'EA',10) if fy!=pts[-1][1] else PLAN.duct([P(20800,fy),P(21700,fy)],300,'EA',10)
  PLAN.duct([P(22300,fy),P(22800,fy),P(22800,fy-450)],200 if rid=='09' else 300,'EA',10)
  PLAN.fan(*P(fx,fy),'','EA',300);PLAN.text(*P(fx-400,fy-600),f'EF-{rid}-{j+1:02d}',120,'EA',True)
  device_on_plan(fx+350,fy,f'MD-E{rid}-{j+1:02d}','EA',True)
  if rid!='01':
   device_on_plan(fx-520,fy,f'MD-IE{rid}-{j+1:02d}','EA',True)
   addcomp(f'MD-IE{rid}-{j+1:02d}','Motorized extract fan inlet isolation','7.14.1 isolation provision; final individual outlet arrangement to confirm')
  addcomp(f'EF-{rid}-{j+1:02d}','Axial extract fan' if rid in ['03','09'] else 'Clean-agent extract fan','7.19.1 2 x 100%' if rid!='01' else 'One fan shown; quantity / agent suitability TBC')
  addcomp(f'MD-E{rid}-{j+1:02d}','Motorized fan isolation damper','7.14.1; standby discharge isolation')
 PLAN.text(*P(20900,pts[-1][1]+1450),'2 x 100% / ONE DUTY / ROTATION' if rid!='01' else 'FAN QUANTITY / FINAL DUTY TBC',115,'EA',True)
# Transfer direction is pressure-dependent; values remain unresolved.
for a,b,text in [((15100,6800),(14500,6800),'TOILET TA: PATH / FLOW TBC'),((16600,4400),(17400,4100),'CAG TA: PATH / FLOW TBC')]:
 PLAN.arrow(P(*a),P(*b),'DIM',10,100,True);PLAN.text(*P(a[0]-400,a[1]+500),text,95,'DIM')
PLAN.rect(*P(8300,10900),650,420,'INST',None,12);PLAN.text(*P(8350,11050),'HPCP-01 / PLC + HMI',130,'INST',True)
PLAN.text(*P(10300,10900),'BMS / SCADA WORKSTATION: LOCATION TBC',105,'INST')
PLAN.text(*P(6500,8900),'SIDE-BY-SIDE CORRIDOR MAINS; BOD / BEAMS / INSULATION CLEARANCE TBC',110,'PENDING',True)

# Physical component and monitoring register. Additional provisions are distinguished from TAQA minimums.
for pre,param,loc in [('TT-SA-01','Supply air temperature','Common supply'),('TT-RA-01','Return air temperature','Common return'),('RHT-RA-01','Return relative humidity','Common return'),('FIT-SA-01','Common supply airflow','Common supply straight length per manufacturer'),('FIT-RA-01','Common return airflow','Common return straight length per manufacturer')]:
 addinst(pre,param,loc,'8.4.1 air temperature / humidity / airflow')
# DPT-GF-06 is the building / common-corridor pressure reference; no duplicate device.
addinst('PDT-OA-01','Outdoor intake filter differential pressure','F-OA-01','Additional intake filter monitoring','AI','Additional proposal')
addinst('PDI-OA-01','Local intake filter differential pressure gauge','F-OA-01','Additional intake filter monitoring','LOCAL','Additional proposal')
addcomp('HPCP-01','Dedicated PLC HVAC power and control panel','15.1 / 15.10 / 15.11; 20% spare I/O and CPU; separate duty / standby modules')
addcomp('HMI-01','Local colour touchscreen HMI, >=10 inch','15.12.1; alarms, trends, security, operating hours and energy')
addcomp('BMS-IF-01','BMS / SCADA interface and operator workstation','8.5.1 / 8.5.2; protocol and point mapping TBC')
addcomp('STL-01','Outdoor sand trap louver / bird mesh','7.12.1 / 7.7.1; mesh <=13 mm; SS316L when within 5 km of sea')
addcomp('F-OA-01','Washable MERV 8 outdoor intake filter','7.12.1; clean / dirty loss and face area TBC')
addcomp('OA-SIL-01','Common outdoor intake sound attenuator','Catalogue insertion loss / pressure loss TBC')
for rid in ['03','09','01']:addcomp(f'EA-SIL-{rid}','Dedicated extract sound attenuator',f'GF-{rid}; catalogue loss / insertion loss TBC')
for tag,service in [('STL-B1','Cable basement sand trap louver / bird mesh'),('F-OA-B1','Basement intake MERV 8 filter'),('OA-SIL-B1','Basement intake sound attenuator'),('EA-SIL-B1-01','Basement extract sound attenuator 1'),('EA-SIL-B1-02','Basement extract sound attenuator 2')]:addcomp(tag,service,'Proposed ventilation inlet / outlet arrangement; catalogue loss and final area TBC')
addcomp('MD-OA-01','Common outdoor-air modulating damper','Proposed minimum OA / building pressure control; final OA TBC')
addcomp('PRD-01','Common outdoor relief path and relief control','7.13 / user relief basis; Qrelief = QOA - 691.12 only under current assumed RA')
addcomp('SA-SIL-01','Common supply sound attenuator','Catalogue insertion loss / pressure loss TBC')
addcomp('RA-SIL-01','Common return sound attenuator','Catalogue insertion loss / pressure loss TBC')
addcomp('EH-COM-01','Common indoor electric duct heater','7.8.2; heating load / high-limit / airflow proof TBC')
addcomp('HUM-01','Steam humidifier in main supply, if required','7.10.1; conditional requirement / duty TBC','Conditional; humidity duty to verify')
addinst('TSHH-EH-COM-01','Common heater high-limit','EH-COM-01','Proposed OEM heater safety','DI','OEM safety provision','Trip common heater; reset per OEM')
for c in 'ABC':
 addcomp(f'PAU-{c}','Packaged DX unit, 3 x 50% bank',f'7.17.1; 1848.9 L/s per unit, 2 duty + 1 available; rotating duty pair')
 for p,service in [('MD-RA','Unit return shut-off damper'),('MD-OA','Unit outdoor-air shut-off damper'),('MD-SA','Unit supply shut-off damper')]:addcomp(f'{p}-{c}',service,'7.14.1; close standby paths, open / close proof')
 for i,m in [(1,8),(2,14)]:
  addcomp(f'F{i}-{c}',f'MERV {m} filter bank','9.3.2; washable prefilter / disposable bag final')
  addinst(f'PDT-F{i}-{c}','Filter differential pressure',f'PAU-{c} filter {i}','9.3.4','AI','Required','Dirty filter alarm; OEM threshold TBC')
  addinst(f'PDI-F{i}-{c}','Local filter differential pressure gauge',f'PAU-{c} filter {i}','9.3.4','LOCAL','Required','Local indication; not a PLC input')
 addinst(f'DPT-SF-{c}','Evaporator fan differential pressure',f'PAU-{c} fan','8.4.1','AI','Required','Fan proof / alarm; limit TBC')
 addinst(f'VS-PAU-{c}','RMS vibration velocity',f'PAU-{c} frame / fan bearing','8.4.1','AI','Required','Alarm / trip limits TBC')
 addcomp(f'CD-PAU-{c}','Coil drain pan, trapped drain and cleanout','OEM pressure-based trap geometry; pipe route / invert TBC')
for rid,n in [('03',2),('09',2),('01',1)]:
 for j in range(1,n+1):
  addinst(f'DPT-EF-{rid}-{j:02d}','Extract fan pressure proof',f'EF-{rid}-{j:02d}','Additional fan-proof proposal','AI','Additional proposal','Fault changeover / alarm; final OEM proof method TBC')
  addinst(f'VS-EF-{rid}-{j:02d}','RMS vibration velocity',f'EF-{rid}-{j:02d}','8.4.1','AI','Required','Alarm / trip limits TBC')
for typ in ['SF','EF']:
 for j in [1,2]:
  addcomp(f'{typ}-B1-{j:02d}','Cable basement axial ventilation fan','7.18.3; each group 2 x 100%, final flow = greater of 4 ACH and heat duty')
  addcomp(f'MD-{typ}-B1-{j:02d}','Basement fan motorized isolation','7.14.1; standby isolated')
  addcomp(f'MD-I{typ}-B1-{j:02d}','Basement fan motorized inlet isolation','7.14.1; isolate both sides of parallel fan paths')
  addinst(f'DPT-{typ}-B1-{j:02d}','Fan pressure proof',f'{typ}-B1-{j:02d}','Additional fan proof provision','AI','Additional proposal')
  addinst(f'VS-{typ}-B1-{j:02d}','RMS vibration velocity',f'{typ}-B1-{j:02d}','8.4.1')
addinst('TT-B1-01','Cable basement air temperature','Cable basement','8.4.1')
addinst('DPT-B1-01','Basement pressure vs outdoor','Cable basement','Additional coordination provision','AI','Additional proposal')
addinst('EM-HPCP-01','Energy metering: V, I, kW, kWh, PF, Hz; THD for VFD','HPCP feeders >7.5 kW','8.4.1','COMM','Required where threshold met','Power ratings / feeder quantity / protocol TBC')

for rid in ['04','05','06','07','03','COM-01']:
 addinst('AFS-EH-'+rid,'Heater airflow proof','EH-'+rid,'Explicit Rev08 OEM protection / monitoring provision','DI','Proposed; OEM selection TBC','Hardwired heater inhibit; status / alarm to HPCP')

# Preliminary wired I/O includes shown physical equipment, not OEM-internal refrigerant protections.
IO=[]
def io(tag,typ,signal,action,basis='Proposed interface; confirm OEM / I&C'):
 IO.append({'tag':tag,'type':typ,'signal':signal,'action':action,'basis':basis,'status':'Draft point allocation; safety integrity / module allocation TBC'})
for tag,i in INSTRUMENTS.items():
 if i['io'] in ['AI','DI','COMM']:io(tag,i['io'],i['parameter'],i['action'],i['basis'])
unit_tags=[f'PAU-{c}' for c in 'ABC']+[f'EF-{rid}-{j:02d}' for rid,n in [('03',2),('09',2),('01',1)] for j in range(1,n+1)]+[f'{typ}-B1-{j:02d}' for typ in ['SF','EF'] for j in [1,2]]
for tag in unit_tags:
 for suff,param in [('RUN','Run feedback'),('FLT','Fault feedback'),('RDY','Ready feedback'),('AUTO','Auto / local selector feedback'),('EST','Local lockable E-stop feedback')]:io(f'{tag}-{suff}','DI',param,'Display / interlock', '7.20.4 / 8.3.1 / 15.5')
 io(f'{tag}-START','DO','Start / stop command','Normal automatic operation; fire ESD inhibits','8.2.1 / 15.10.1')
 if not tag.startswith('PAU'):io(f'{tag}-SPD','AO','Speed demand','Proposed EC/VFD speed control; fan drive and ACH lower limit TBC')
md_tags=[t for t,c in COMPONENTS.items() if t.startswith('MD-') or t.startswith('RCD-')]
for tag in md_tags:
 mod=tag=='MD-OA-01' or tag.startswith('RCD-')
 io(f'{tag}-CMD','AO' if mod else 'DO','Position demand' if mod else 'Open / close command','Pressure / standby isolation; final fail state TBC','7.14.1 / 15.10.1')
 for suff in ['OPEN','CLOSED']:io(f'{tag}-{suff}','DI',suff+' limit feedback','Proof / travel fault alarm','7.20.4')
for tag,c in COMPONENTS.items():
 if tag.startswith('EH-'):
  io(f'{tag}-ENABLE','DO','Heater enable','Only with healthy high-limit and airflow proof')
  io(f'{tag}-DUTY','AO','Heating demand','Room / supply temperature control; staged or modulating OEM interface TBC')
for tag,typ,signal,action in [('FACP-FIRE-01','DI','Confirmed fire from FACP','Stop entire HVAC; latch fire ESD'),('HPCP-ESTOP-01','DI','Panel emergency stop','Stop / isolate per approved ESD'),('RESET-01','DI','Local manual reset','Only after fire signal / fault clears'),('BMS-START-01','COMM','Initial start','Normal permissives apply'),('BMS-ESD-01','COMM','Remote emergency stop','Stop HVAC; approved mapping TBC')]:io(tag,typ,signal,action,'8.2.1 / 8.5.1 / 15.11.11')
IO_COUNTS={t:sum(i['type']==t for i in IO) for t in ['AI','AO','DI','DO','COMM']}
CAUSE=[
 ('Confirmed fire','FACP -> HPCP','STOP all PAUs, extract and basement fans; heaters off','Damper fire positions per approved cause-and-effect; not inferred','Local manual reset after fire clears','8.2.1 / 15.11.11'),
 ('Normal start','HMI / BMS start + Auto','Prove duty path dampers; start chosen duty pair and duty extract fans','Standby PAU and parallel fan inlet / outlet paths isolated','Sequence / delays by approved OEM logic','7.14 / 15.10.1'),
 ('Duty PAU fault','Unit fault / fan DP','Alarm; isolate failed unit; enable available alternate','Maintain two healthy 50% units when available','Automatic fault changeover; minimum-runtime delay TBC','7.20.3 / 15.10.1'),
 ('Low / high room pressure','Room DPT','Proposed RCD / OA or extract-speed adjustment within airflow constraints','Respect cooling, fresh-air and minimum ACH limits','Alarm if targets cannot be met; revise supply / balance','7.13.2 / 15.10.1'),
 ('Extract duty fan fault','Fan fault / proof','Start standby for kitchen / toilet / basement','Prove available path; isolate failed path','CAG standby arrangement TBC','7.19.1 / 7.18.3'),
 ('Heater high limit / no flow','TSHH / AFS','Heater OFF','Fans / dampers per OEM sequence; fire overrides','Manual or OEM reset only after fault clears','Proposed OEM protection'),
 ('Power loss / return','Mains / feeder status','HVAC stops; normal restart on restored power','Fire ESD latch overrides automatic restart','Automatic power-return restart only without fire latch','15.11.9 / 10 / 11'),
 ('Post-fire purge','Separate approved command','Not enabled by this drawing','Agent, fire fan suitability and makeup to be approved','No automatic purge assumed','C-H-SS-001 1.5; C-FF-SS-004 required')]

SC=[]
s=frame('Administration HVAC - central PAU duct and instrumentation schematic','ADM-HVAC-S-001',1,4,BASE_NOTES+['3 x 50% PAUs: two duty, one available. Any unit may be standby; programmed rotation and fault changeover apply.','Common and comfort heaters are indoors. Humidifier is conditional; no heating or humidification duty has been selected.'])
s.text(24,43,'OUTDOOR / ROOF PLANT',3.4,'INK',True)
s.line([(65,93),(65,367)],'RA',.55);s.text(22,82,'RETURN MAIN',2.5,'RA',True);s.text(22,88,'3006.68 L/s ASSUMED',2.4,'RA')
s.line([(65,93),(65,51),(140,51)],'RL',.35);s.damper(101,51,'PRD-01','RL',True);s.arrow((115,51),(149,51),'RL');s.text(150,48,'RELIEF Q = FINAL OA - 691.12 L/s',2.4,'RL',True);s.text(150,54,'Flow / setpoint / actuator selection TBC',2.2,'RL')
s.duct([(640,78),(175,78),(175,354)],6,'OA',.4)
s.rect(602,65,23,26,'OA',None,.3);s.text(613,80,'STL',3,'OA',True,'center');s.text(600,61,'STL-01 / MESH',2.4,'OA',False,'center')
s.filter(548,65,14,26,'F-OA-01','OA');s.silencer(474,66,24,23,'OA','OA-SIL-01');s.damper(415,78,'MD-OA-01','OA',True)
s.text(350,63,'FINAL OA TBC; MIN MAKEUP 691.12 L/s',2.4,'OA',True);s.text(350,88,'Current 420.70 L/s is 270.42 L/s short',2.3,'PENDING')
s.sensor(552,43,'PDT-OA-01','DP',3.5);s.sensor(520,43,'PDI-OA-01','G',3.5)
for xx in [546,566]:s.line([(xx,78),(xx,44),(555 if xx==566 else 549,44)],'INST',.18)
for xx in [546,566]:
 gx=517 if xx==546 else 523;gy=99 if xx==546 else 103
 s.line([(xx,78),(xx,gy),(gx,gy),(gx,43)],'INST',.18)
s.line([(625,137),(625,355),(625,463)],'SA',.55)
for i,c in enumerate('ABC'):
 cy=137+i*109;s.rect(247,cy-39,345,87,'INK',None,.3)
 s.text(251,cy-29,f'PAU-{c}  |  50% = 1848.90 L/s  |  DX DUTY / STANDBY ROTATES',2.8,'INK',True)
 s.line([(65,cy),(205,cy)],'RA',.45);s.damper(108,cy,f'MD-RA-{c}','RA',True);s.flex(154,cy,'RA')
 s.rect(204,cy-13,31,27,'OA',None,.3);s.text(219,cy+2,'MIX',3,'OA',True,'center')
 s.line([(175,cy-20),(219,cy-20),(219,cy-13)],'OA',.3);s.damper(191,cy-20,f'MD-OA-{c}','OA',True,size=5)
 s.arrow((235,cy),(625,cy),'SA',.45)
 s.filter(272,cy-11,13,25,f'F1-{c} / M8');s.filter(315,cy-11,17,25,f'F2-{c} / M14')
 for x,n in [(278,1),(323,2)]:
  s.sensor(x,cy-21,f'PDT-F{n}-{c}','DP',3.5);s.line([(x-6,cy-11),(x-6,cy-21),(x-3.5,cy-21)],'INST',.2);s.line([(x+6,cy-11),(x+6,cy-21),(x+3.5,cy-21)],'INST',.2)
  s.sensor(x,cy+33,f'PDI-F{n}-{c}','G',3);s.line([(x-6,cy+9),(x-6,cy+33),(x-3,cy+33)],'INST',.18);s.line([(x+6,cy+9),(x+6,cy+33),(x+3,cy+33)],'INST',.18)
 s.rect(383,cy-12,32,28,'SA',None,.3);s.text(399,cy+2,'DX COIL',2.8,'SA',True,'center');s.text(399,cy+23,f'CD-PAU-{c}',2.2,'DIM',False,'center');s.line([(399,cy+16),(399,cy+30),(421,cy+30)],'DIM',.2)
 s.fan(483,cy,f'SF-{c}','SA',10);s.sensor(486,cy-20,f'DPT-SF-{c}','DP',3.5);s.line([(469,cy),(469,cy-20),(482,cy-20)],'INST',.18);s.line([(497,cy),(497,cy-20),(490,cy-20)],'INST',.18)
 s.sensor(516,cy+29,f'VS-PAU-{c}','VS',3.4);s.line([(516,cy+25),(493,cy+7)],'INST',.2)
 s.flex(562,cy,'SA');s.damper(607,cy,f'MD-SA-{c}','SA',True)
 s.access(362,cy-11,f'AD-{c}')
s.text(26,383,'PDI = LOCAL GAUGE; PDT / DPT = PLC PRESSURE INPUT',2.5,'INST',True)
s.text(26,391,'Each unit: OEM refrigerant HP / LP / oil safety, compressor delay and motor protections.',2.4)
s.text(26,399,'Catalogue coil duty, available external total pressure, weights and access clearances: TBC.',2.4,'PENDING')
s.rect(26,436,626,119,'DIM',None,.3,dash=True);s.text(34,445,'INDOOR COMMON SUPPLY / RETURN SECTIONS',3,'INK',True)
s.duct([(625,463),(45,463)],8,'SA',.35);s.silencer(542,451,27,24,'SA','SA-SIL-01');s.heater(451,449,'EH-COM-01','SA',20,28)
s.sensor(485,442,'TSHH-EH-COM-01','HH',3);s.line([(461,449),(485,446)],'INST',.2)
s.sensor(520,438,'AFS-EH-COM-01','AF',3);s.line([(500,463),(520,441)],'INST',.2)
s.rect(357,452,28,23,'SA',None,.25,True);s.text(371,466,'HUM',2.8,'SA',True,'center');s.text(371,482,'HUM-01 IF REQUIRED',2.2,'SA',False,'center')
s.sensor(276,463,'FIT-SA-01','FT',5);s.sensor(195,463,'TT-SA-01','TT',5);s.access(114,460,'AD-SA')
s.text(44,493,'TO GF: SA-M01 1200x650; 3697.80 L/s; 4.74 m/s; BOD TBC',2.6,'SA',True)
s.duct([(625,530),(65,530),(65,367)],8,'RA',.35);s.silencer(99,518,27,24,'RA','RA-SIL-01');s.sensor(195,530,'FIT-RA-01','FT',5);s.sensor(285,530,'TT-RA-01','TT',5);s.sensor(375,530,'RHT-RA-01','RH',5)
s.text(453,519,'FROM GF RETURN TO ROOF',2.5,'RA',True);s.text(453,545,'1400x650; 3006.68 L/s; 3.30 m/s',2.5,'RA')
SC.append(s)

s=frame('Administration HVAC - room supply and return schematic','ADM-HVAC-S-002',2,4,BASE_NOTES+['The common net equivalent area is 0.01 m2 per +50 Pa return room. C=0.65, density=1.2 and delta-P=50 give 59.34 L/s offset per room.','RCD return modulation is a proposed pressure-control provision. Confirm range, fail state and tuning; fixed flows are initial balancing values.','FSD shown with * is conditional on approved fire compartmentation. Exact ratings, locations and fire positions remain TBC.'])
s.duct([(28,82),(656,82)],5,'SA',.3);s.text(30,66,'PAU COMMON SUPPLY: 3697.80 L/s',3,'SA',True)
s.duct([(656,135),(28,135)],5,'RA',.3);s.text(30,122,'DUCTED RETURN: 3006.68 L/s ASSUMED; CAG / KITCHEN / TOILET EXCLUDED',3,'RA',True)
order=['02','05','04','08','06','07','09','03','01']
for i,rid in enumerate(order):
 r=BYID[rid];x=28+i*70;mid=x+33;xx=x+12;rx=x+51
 s.rect(x,168,66,234,'DIM',None,.22);s.para(x+3,179,f'GF-{rid} {r["name"]}',60,2.6,'INK',True)
 s.text(mid,199,f'TARGET +{r["pressure"]:.0f} Pa',2.6,'INST',True,'center')
 s.line([(xx,82),(xx,331)],'SA',.35);s.damper(xx,220,f'VCD-S{rid}','SA',size=5);s.damper(xx,250,f'FSD-S{rid}*','SA',True,size=5,fire=True)
 if rid in ['04','05','06','07','03']:
  s.heater(xx-5,279,f'EH-{rid}','SA',10,17)
  s.sensor(xx+14,286,f'TSHH-EH-{rid}','HH',2.8);s.line([(xx+5,287),(xx+11.2,286)],'INST',.18)
  s.sensor(xx+14,310,f'AFS-EH-{rid}','AF',2.8);s.line([(xx,304),(xx+11.2,310)],'INST',.18)
 s.terminal(xx,330,'','SD',8,'SA');s.text(x+3,348,f'{r["n"]} x {r["sa"]/r["n"]:.2f} L/s',2.2,'SA');s.text(x+3,357,f'SA {r["sa"]:.2f}',2.5,'SA',True);s.text(x+3,366,f'{r["sw"]}x{r["sh"]} / D{r["new_neck"]}',2.1,'SA')
 if r['rn']:
  s.arrow((rx,327),(rx,135),'RA',.35);s.terminal(rx,331,'','RG',8,'RA');s.damper(rx,276,f'RCD-R{rid}','RA',True,size=5);s.damper(rx,220,f'FSD-R{rid}*','RA',True,size=5,fire=True)
  s.text(x+3,380,f'RA {r["ra"]:.2f} ASSUMED',2.4,'RA',True);s.text(x+3,390,f'{r["rn"]} RG x {r["ra"]/r["rn"]:.2f}',2.2,'RA')
 else:
  s.terminal(rx,331,'','EG',8,'EA');s.arrow((rx,335),(rx,393),'EA',.35);s.text(x+3,380,'NO RETURN',2.7,'EA',True);s.text(x+3,390,'EA SEE S-003',2.2,'EA')
 for j,(pre,label) in enumerate([('TT','TT'),('RHT','RH'),('DPT','DP')]):s.sensor(x+11+j*21,432,f'{pre}-GF-{rid}',label,3.7)
 s.text(mid,450,'PRESSURE: PENDING',2.1,'INST',False,'center')
s.text(30,466,'DAMPERS / TERMINALS',3,'INK',True)
s.para(30,477,'Supply diffusers and return grilles: integral OBD, tagged neck, face, flow, plenum, test point and access. Drawn room branch paths have VCD; return pressure-control damper RCD is additional. Main and each room temperature / humidity / pressure values report to HPCP-01. Pressure sensor reference is outdoors, not the adjacent room.',620,2.6)
s.text(30,506,'ROOM AIRFLOW BALANCE',3,'INK',True)
s.para(30,517,'For the six +50 Pa return rooms, supply - return = 59.34 L/s as a NET outward allowance. It includes the net effect of transfer, relief and envelope outflow; it is not an additional HAP duct loss. Allocate actual paths before pressure verification. +25 Pa extract rooms must meet both minimum ACH and the full room / transfer balance.',620,2.6)
s.text(30,552,'SA = cooled mixed PAU air. Delivered room outdoor air must be checked separately from total supply / extract ACH.',2.7,'PENDING',True)
SC.append(s)

s=frame('Administration HVAC - dedicated extracts and cable basement','ADM-HVAC-S-003',3,4,BASE_NOTES+['Kitchen and toilet: 2 x 100% extract with automatic duty rotation. No central return from these rooms.','Clean-agent: normal 5 ACH minimum; dedicated extract, fan quantity / pickup level / agent suitability TBC.','Basement: separate 2 x 100% supply + 2 x 100% extract; greater of 4 ACH and heat removal. Volume and heat load are missing.'])
for j,rid in enumerate(['03','09','01']):
 x=27+j*211;r=BYID[rid];s.text(x,48,f'GF-{rid} {r["name"].upper()}',3.1,'INK',True)
 s.rect(x,68,191,53,'DIM',None,.25);s.arrow((x+8,81),(x+36,81),'SA',.3);s.text(x+45,82,f'PAU SA {r["sa"]:.2f} L/s',2.8,'SA',True)
 s.text(x+8,95,'+25 Pa target / NO RETURN',2.6,'INST',True)
 minflow=67.5555555556 if rid in ['03','01'] else 64.8888888889
 s.text(x+8,108,f'MIN NORMAL {5 if rid=="01" else 10} ACH = {minflow:.2f} L/s',2.5,'EA')
 s.terminal(x+17,143,'EG-'+rid,'EG',8,'EA');s.line([(x+17,143),(x+17,177),(x+48,177)],'EA',.3);s.damper(x+37,177,'VCD','EA',size=5)
 s.silencer(x+53,166,18,21,'EA','EA-SIL-'+rid)
 fan_n=1 if rid=='01' else 2
 s.line([(x+71,177),(x+83,177),(x+83,153)],'EA',.3)
 if fan_n==2:s.line([(x+83,153),(x+83,214)],'EA',.3)
 for z in range(fan_n):
  cy=153+61*z;s.arrow((x+83,cy),(x+177,cy),'EA',.3);s.flex(x+90,cy,'EA',5,10);s.fan(x+114,cy,f'EF-{rid}-{z+1:02d}','EA',8);s.damper(x+146,cy,f'MD-E{rid}-{z+1:02d}','EA',True,size=5)
  if fan_n==2:s.damper(x+98,cy,f'MD-IE{rid}-{z+1:02d}','EA',True,size=5)
  s.sensor(x+111,cy-20,f'DPT-EF-{rid}-{z+1:02d}','DP',3.4);s.sensor(x+171,cy-20,f'VS-EF-{rid}-{z+1:02d}','VS',3.4)
  s.line([(x+103,cy),(x+103,cy-20),(x+107.6,cy-20)],'INST',.18);s.line([(x+125,cy),(x+125,cy-20),(x+114.4,cy-20)],'INST',.18)
  s.line([(x+167.6,cy-20),(x+151,cy-12),(x+120,cy-5)],'INST',.18)
 s.line([(x+177,153),(x+177,240),(x+194,240),(x+194,249)],'EA',.3);s.arrow((x+194,239),(x+194,249),'EA',.3)
 s.text(x+5,251,'DOWNWARD-FACING OUTDOOR DISCHARGE',2.2,'EA',True)
 s.para(x+5,263,'CAG: final duty / fan quantity TBC. No automatic fire extraction; entire HVAC shuts down.' if rid=='01' else f'EA reference {r["ea"]:.2f} L/s; final +25 Pa balance / OA compliance and catalogue loss remain TBC.',188,2.5,'PENDING')
s.line([(25,303),(655,303)],'DIM',.25)
s.text(28,318,'CABLE BASEMENT - SEPARATE VENTILATION CIRCUIT',3.6,'INK',True)
s.text(28,329,'AIRFLOW DUTY TBC: Q >= max(4 x V / 3.6, 1000 x heat_kW / (1.06 x 1.0216 x 5)) L/s',2.8,'PENDING',True)
s.filter(36,351,12,30,'STL-B1 / F-OA-B1','OA');s.silencer(65,354,22,24,'OA','OA-SIL-B1');s.line([(28,366),(107,366),(107,418)],'OA',.3)
for j,cy in enumerate([366,418],1):
 s.arrow((107,cy),(217,cy),'SA',.3);s.fan(145,cy,f'SF-B1-{j:02d}','SA',8);s.damper(192,cy,f'MD-SF-B1-{j:02d}','SA',True,size=5);s.line([(217,cy),(228,cy),(228,394)],'SA',.3)
 s.sensor(153,cy-20,f'DPT-SF-B1-{j:02d}','DP',3.2);s.sensor(204,cy-20,f'VS-SF-B1-{j:02d}','VS',3.2)
 s.damper(120,cy,f'MD-ISF-B1-{j:02d}','SA',True,size=5)
 s.line([(133,cy),(133,cy-20),(149.8,cy-20)],'INST',.18);s.line([(163,cy),(163,cy-20),(156.2,cy-20)],'INST',.18)
 s.line([(200.8,cy-20),(183,cy-12),(151,cy-5)],'INST',.18)
s.rect(267,349,142,110,'DIM',None,.3);s.text(338,365,'CABLE BASEMENT',3.2,'INK',True,'center');s.arrow((228,394),(280,394),'SA',.35);s.terminal(287,394,'SF OUTLETS','SD',9,'SA')
s.terminal(387,394,'EF GRILLES','EG',9,'EA');s.arrow((393,394),(452,394),'EA',.35);s.line([(452,366),(452,418)],'EA',.3)
s.sensor(312,435,'TT-B1-01','TT',4);s.sensor(367,435,'DPT-B1-01','DP',4)
for j,cy in enumerate([366,418],1):
 s.arrow((452,cy),(623,cy),'EA',.3);s.flex(460,cy,'EA',5,11);s.fan(491,cy,f'EF-B1-{j:02d}','EA',8);s.damper(538,cy,f'MD-EF-B1-{j:02d}','EA',True,size=5);s.silencer(566,cy-11,23,22,'EA',f'EA-SIL-B1-{j:02d}')
 s.sensor(500,cy-20,f'DPT-EF-B1-{j:02d}','DP',3.2);s.sensor(600,cy-20,f'VS-EF-B1-{j:02d}','VS',3.2)
 s.damper(471,cy,f'MD-IEF-B1-{j:02d}','EA',True,size=5)
 s.line([(479,cy),(479,cy-20),(496.8,cy-20)],'INST',.18);s.line([(509,cy),(509,cy-20),(503.2,cy-20)],'INST',.18)
 s.line([(596.8,cy-20),(564,cy-13),(497,cy-5)],'INST',.18)
s.line([(623,366),(623,452),(640,452),(640,465)],'EA',.35);s.arrow((640,451),(640,465),'EA',.35)
s.text(27,487,'NORMAL / FIRE / POST-FIRE',3.1,'INK',True)
s.para(27,499,'Normal fans satisfy temperature, fresh-air, ACH and pressure criteria together. Confirmed fire stops ALL HVAC fans and heaters, including CAG and basement. Fire damper positions follow the approved compartment and cause-and-effect design. Same-fan post-fire purge remains a separate proposal; no smoke-control fan rating or automatic purge is established here.',623,2.7)
s.text(27,550,'Basement plan, duct sizes, equipment clearances, penetrations, fan curve and full pressure loss circuit: TBC.',2.7,'PENDING',True)
SC.append(s)

s=frame('Administration HVAC - controls, I/O and cause-and-effect','ADM-HVAC-S-004',4,4,BASE_NOTES+['Control logic, alarm limits, delays, communication protocol and actuator fail positions require I&C / OEM approval.','Room DPTs beyond the TAQA minimum and extract fan pressure proof are explicit added provisions, not quoted minimum requirements.','Point schedule is preliminary. CAG quantity, conditional fire dampers, humidifier and final energy-meter feeder count can change I/O.'])
s.rect(27,47,173,149,'INST',None,.3);s.text(35,61,'FIELD MONITORING',3.2,'INST',True)
for j,t in enumerate(['TT: all GF rooms, basement, main SA / RA','RHT: occupied / electrical rooms + return','DPT: room pressure, fan proof','PDT + local PDI: every PAU filter bank','FIT: common supply / return ducts','VS: PAUs and ventilation fans','AFS / TSHH: heater airflow / high limit','EM: feeders >7.5 kW; final quantity TBC']):s.text(35,76+j*15,t,2.5,'INST')
s.rect(274,48,168,149,'INK',None,.4);s.text(283,62,'HPCP-01 / DEDICATED PLC',3.3,'INK',True)
s.para(283,75,'Separate AI / AO / DI / DO cards. Separate duty / standby loop modules. >=20% spare connected I/O terminals and CPU capacity.',150,2.6)
s.rect(290,118,136,37,'INST',None,.3);s.text(358,132,'HMI-01: >=10 inch',3,'INST',True,'center');s.text(358,143,'Mimic / alarms / trends / hours / security',2.4,'INST',False,'center')
s.text(283,171,'Manual-test / Stop / Auto selectors',2.5);s.text(283,181,'Run GREEN / Standby YELLOW / Trip RED',2.4)
s.arrow((200,105),(274,105),'CTRL',.3,2.5,True);s.text(231,95,'AI / DI',2.7,'CTRL',True,'center')
s.rect(507,48,146,149,'SA',None,.3);s.text(515,62,'CONTROLLED EQUIPMENT',3.1,'SA',True)
for j,t in enumerate(['3 x 50% PAUs: rotating duty pair','Kitchen / toilet 2 x 100% fans','CAG fan quantity / duty TBC','Basement SF / EF: 2 x 100% each','Motorized shut-off / RCD dampers','Common and comfort heaters','Conditional HUM / final OEM interfaces']):s.text(515,77+j*15,t,2.4,'SA')
s.arrow((442,105),(507,105),'CTRL',.3,2.5,True);s.text(474,95,'DO / AO',2.7,'CTRL',True,'center')
s.rect(28,220,172,32,'PENDING',None,.3);s.text(35,231,'FACP: CONFIRMED FIRE',2.9,'PENDING',True);s.text(35,242,'Hardwired signal to HPCP: stop entire HVAC',2.4,'PENDING')
s.arrow((200,235),(275,235),'PENDING',.4);s.line([(275,235),(275,198)],'PENDING',.4)
s.rect(306,219,159,34,'INST',None,.3);s.text(314,231,'BMS / SCADA + CONTROL-ROOM MONITOR',2.6,'INST',True);s.text(314,243,'Initial start / E-stop / all monitoring',2.5,'INST');s.arrow((358,198),(358,219),'CTRL',.3,2.5,True)
s.rect(507,220,145,32,'PENDING',None,.3);s.para(515,231,'Local lockable E-stop hardwired directly to related feeder; status to PLC (8.3.1).',128,2.5,'PENDING')
s.text(28,273,'PRELIMINARY WIRED I/O ALLOCATION',3.1,'INK',True)
rows=[[t,str(IO_COUNTS[t]),str(ceil(IO_COUNTS[t]*.2)),str(IO_COUNTS[t]+ceil(IO_COUNTS[t]*.2))] for t in ['AI','AO','DI','DO']]
table(s,28,279,290,['Type','Shown points','20% spare minimum','Minimum channels'],rows,[1,1,1.5,1.5],2.4,7)
s.para(337,284,'Full unique tag register, equipment list and individual points are included as CSV files in the CAD package. COMM values and OEM-internal safety circuits are not counted as wired AI/DI points. All new tags are draft allocations.',312,2.6)
s.text(28,330,'DRAFT OPERATING SEQUENCE / CAUSE-AND-EFFECT',3.2,'INK',True)
rows=[[r[0],r[1],r[2],r[3],r[4]] for r in CAUSE]
table(s,28,337,624,['Trigger','Input','Equipment action','Damper / permissive action','Restart / limits'],rows,[1.1,1,2.2,2.1,1.7],2.25,27)
SC.append(s)


def export_pdf(sheets,name,title):
 c=canvas.Canvas(str(OUT/name),pagesize=(W*MM,H*MM),pageCompression=1);c.setTitle(title);c.setAuthor('HVAC coordination draft');c.setSubject('Rev10 / heater airflow proof and instrument register synchronized; coordination design holds open')
 for s in sheets:pdf_render_scene(c,s);c.showPage()
 c.save()
export_pdf(SC,'Administration_HVAC_Schematic.pdf','Administration HVAC - Duct and Instrumentation Schematic Rev10')
export_schematic(SC,OUT/'Administration_HVAC_Schematic.dxf')
assert len(SC)==4
io_register=list(csv.DictReader((BASE/'schedules/IO_points.csv').open()))
counts={t:sum(r['type']==t for r in io_register) for t in IO_COUNTS}
assert counts==IO_COUNTS,(counts,IO_COUNTS)
assert not ezdxf.readfile(OUT/'Administration_HVAC_Schematic.dxf').audit().errors
p=fitz.open(OUT/'Administration_HVAC_Schematic.pdf')
for i,page in enumerate(p,1):page.get_pixmap(matrix=fitz.Matrix(2100/page.rect.width,2100/page.rect.width)).save(TMP/f'S-{i:02d}.png')
print(json.dumps({'schematic_revision':10,'sheets':len(SC),'io_counts':IO_COUNTS,'register_match':'passed','DXF_audit':'passed'}))
