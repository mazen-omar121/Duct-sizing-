"""Vector drafting primitives adapted from the preserved Rev12 source.
NTS method diagrams use paper-space millimetres; they are not fabrication plans.
"""
from math import hypot,atan2,cos,sin,pi
import ezdxf
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor
MM=72/25.4;W,H=841,594
FONT='Helvetica';BOLD='Helvetica-Bold'
COL={'SA':'#239321','RA':'#1567BD','EA':'#B95A18','OA':'#408A95','RL':'#AD497E','INST':'#703779','CTRL':'#703779','ARCH':'#B7B7B7','INK':'#171C20','DIM':'#74787B','PENDING':'#A23A34','FILL':'#F4F4F4'}
LAYER={k:'M-'+k for k in COL};ACI={'SA':3,'RA':5,'EA':30,'OA':4,'RL':6,'INST':6,'CTRL':6,'ARCH':8,'INK':7,'DIM':8,'PENDING':1,'FILL':9}
class Scene:
 def __init__(self,w=W,h=H):self.w=w;self.h=h;self.ops=[]
 def line(self,pts,k="INK",lw=.25,dash=False):self.ops.append(("line",pts,k,lw,dash))
 def rect(self,x,y,w,h,k="INK",fill=None,lw=.25,dash=False):
  self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],k,fill,lw,dash)
 def poly(self,pts,k="INK",fill=None,lw=.25,dash=False):self.ops.append(("poly",pts,k,fill,lw,dash))
 def circle(self,x,y,r,k="INK",lw=.25,fill=None):self.ops.append(("circle",x,y,r,k,lw,fill))
 def text(self,x,y,t,size=2.5,k="INK",bold=False,align="left",angle=0,mask=False):
  if mask and not angle:
   width=pdfmetrics.stringWidth(str(t),BOLD if bold else FONT,size)
   left=x-width/2 if align=='center' else x-width if align=='right' else x
   self.rect(left-.7,y-size*.83,width+1.4,size*1.1,k,'#FFFFFF',0)
  self.ops.append(("text",x,y,str(t),size,k,bold,align,angle))
 def para(self,x,y,t,width,size=2.5,k="INK",bold=False,leading=1.45):
  lines=[]
  for paragraph in t.splitlines():
   line=''
   for word in paragraph.split():
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
  if tag:self.text(x,y+size*.95,tag,size*.3,k,False,"center",mask=True)
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
  if tag:self.text(x,y+size*.8,tag,size*.26,k,True,"center",mask=True)
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
 def dimension(self,a,b,base,scale=1,angle=0):
  self.ops.append(('dimension',a,b,base,float(scale),angle))

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
  if typ=='dimension':
   _,a,b,base,scale,angle=op
   horizontal=angle==0
   aa=(a[0],base[1]) if horizontal else (base[0],a[1])
   bb=(b[0],base[1]) if horizontal else (base[0],b[1])
   sub=Scene();sub.line([a,aa],'DIM',.18);sub.line([b,bb],'DIM',.18);sub.line([aa,bb],'DIM',.18)
   sub.arrow(aa,bb,'DIM',.18,1.5);sub.arrow(bb,aa,'DIM',.18,1.5)
   value=abs(b[0]-a[0] if horizontal else b[1]-a[1])*scale
   sub.text((aa[0]+bb[0])/2,(aa[1]+bb[1])/2-2,f'{value:g}',2.5,'INK',False,'center',mask=True)
   _pdf_ops(c,sub.ops);continue
  if typ in ("line","poly"):
   pts,k=op[1:3];fill=None
   if typ=="line":lw,dash=op[3:5]
   else:fill,lw,dash=op[3:6]
   c.setStrokeColor(HexColor(COL[k]));c.setLineWidth(lw);c.setDash([2*max(1,lw),max(1,lw)] if dash else [])
   p=c.beginPath();p.moveTo(*pts[0])
   for pt in pts[1:]:p.lineTo(*pt)
   if typ=="poly":p.close()
   if fill:c.setFillColor(HexColor(fill))
   c.drawPath(p,stroke=1 if lw>0 else 0,fill=1 if fill else 0)
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
 doc.set_wipeout_variables(frame=0)
 doc.styles.get('Standard').dxf.font='Arial.ttf'
 doc.styles.new('MDR-BOLD',dxfattribs={'font':'Arialbd.ttf'})
 if "DASHED" not in doc.linetypes:doc.linetypes.new("DASHED",dxfattribs={"description":"Dashed control / unconfirmed","pattern":[4,2,-2]})
 for k,l in LAYER.items():doc.layers.new(l,dxfattribs={"color":ACI[k],"true_color":int(COL[k][1:],16),"lineweight":25 if k!="ARCH" else 9,"linetype":"DASHED" if k=="CTRL" else "CONTINUOUS"})
 doc.layers.new("VIEWPORT",dxfattribs={"color":8,"plot":False})
 doc.layers.new("VIEWPORTS",dxfattribs={"color":8,"plot":False})
 doc.layers.new("M-MASK",dxfattribs={"color":7,"plot":True})
 doc.dimstyles.new('MDR-DETAIL',dxfattribs={'dimtxsty':'Standard','dimtxt':2.5*.718,'dimasz':1.5,'dimexo':.5,'dimexe':1,'dimgap':.6,'dimdec':0})
 return doc

def dxf_scene(target,s,offset=(0,0)):
 def p(a):return a[0]+offset[0],s.h-a[1]+offset[1]
 def fill_polygon(points,fill,layer):
  if not fill:return
  if fill=='#FFFFFF':target.add_wipeout(points,dxfattribs={'layer':'M-MASK'})
  else:
   hatch=target.add_hatch(dxfattribs={'layer':layer,'true_color':int(fill[1:],16)})
   hatch.paths.add_polyline_path(points,is_closed=True)
 weights=[0,5,9,13,15,18,20,25,30,35,40,50,53,60,70,80,90,100,106,120,140,158,200,211]
 for op in s.ops:
  typ=op[0]
  if typ=="place":continue
  if typ=='dimension':
   _,a,b,base,scale,angle=op
   target.add_linear_dim(base=p(base),p1=p(a),p2=p(b),angle=angle,dimstyle='MDR-DETAIL',dxfattribs={'layer':'M-DIM'},override={'dimlfac':scale}).render()
   continue
  k=op[2] if typ in ["line","poly"] else op[4] if typ=="circle" else op[5]
  attrs={"layer":LAYER[k]}
  if typ in ['line','poly','circle']:
   lw=op[3] if typ=='line' else op[4] if typ=='poly' else op[5]
   attrs['lineweight']=min(weights,key=lambda a:abs(a-lw*100))
  if typ=="line":
   if op[4]:attrs["linetype"]="DASHED"
   for a,b in zip(op[1],op[1][1:]):target.add_line(p(a),p(b),dxfattribs=attrs)
  elif typ=="poly":
   if op[5]:attrs["linetype"]="DASHED"
   fill_polygon([p(a) for a in op[1]],op[3],attrs['layer'])
   if op[4]>0:target.add_lwpolyline([p(a) for a in op[1]],close=True,dxfattribs=attrs)
  elif typ=="circle":
   _,x,y,r,k,lw,fill=op
   fill_polygon([p((x+r*cos(a*pi/16),y+r*sin(a*pi/16))) for a in range(32)],fill,attrs['layer'])
   target.add_circle(p((x,y)),r,dxfattribs=attrs)
  elif typ=="text":
   _,x,y,t,z,k,bold,align,angle=op
   for i,a in enumerate(t.split("\n")):
    # AutoCAD TEXT height is cap height; PDF fontsize includes ascent/descent.
    e=target.add_text(a,dxfattribs={**attrs,"height":z*.718,"rotation":angle,"style":"MDR-BOLD" if bold else "Standard"})
    from ezdxf.enums import TextEntityAlignment
    e.set_placement(p((x,y+i*z*1.4)),align={"left":TextEntityAlignment.LEFT,"right":TextEntityAlignment.RIGHT,"center":TextEntityAlignment.CENTER}[align])

def export_schematic(sheets,path,numbers=None):
 doc=make_doc();m=doc.modelspace()
 for i,s in enumerate(sheets):
  number=numbers[i] if numbers is not None else i+1
  dxf_scene(m,s,(i*900,0));l=doc.layouts.new(f"MDR{number:02d}_A1");l.page_setup(size=(841,594),margins=(0,0,0,0),units="mm");l.add_viewport(center=(420.5,297),size=(841,594),view_center_point=(i*900+420.5,297),view_height=594,dxfattribs={"layer":"VIEWPORT"})
 doc.set_modelspace_vport(height=594,center=(420.5,297));doc.saveas(path)
