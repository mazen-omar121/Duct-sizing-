"""Continuous, topology-aware duct outlines for the Rev08 coordination plan.

Only identified connections are opened. Unconnected duct crossings are left
independent. Tapers are drawn as actual replacement profiles, not as symbols
superimposed on an unchanged rectangular duct. Lengths are proposed geometry.
"""
import json
from math import hypot, atan2, cos, sin, pi
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union


def unit(a, b):
    L = hypot(b[0]-a[0], b[1]-a[1])
    return ((b[0]-a[0])/L, (b[1]-a[1])/L)


def shift(p, u, d):
    return (p[0]+u[0]*d, p[1]+u[1]*d)


def taper(a, b, wa, wb):
    u = unit(a, b); n = (-u[1], u[0])
    return Polygon([shift(a,n,wa/2), shift(b,n,wb/2),
                    shift(b,n,-wb/2), shift(a,n,-wa/2)])


def outline(points, width, circular=False):
    pp = [points[0]]
    for i,p in enumerate(points[1:-1],1):
        a,b = points[i-1],points[i+1]
        la,lb = hypot(p[0]-a[0],p[1]-a[1]),hypot(b[0]-p[0],b[1]-p[1])
        u,v = unit(a,p),unit(p,b)
        turn = u[0]*v[1]-u[1]*v[0]; r = min(width*.8,la*.4,lb*.4)
        if circular or abs(turn)<.5 or r<width*.51:
            pp.append(p); continue
        enter,leave = shift(p,u,-r),shift(p,v,r)
        c = shift(enter,v,r); a0 = atan2(enter[1]-c[1],enter[0]-c[0])
        pp.append(enter)
        for j in range(1,13):
            ang = a0+(pi/2 if turn>0 else -pi/2)*j/12
            pp.append((c[0]+r*cos(ang),c[1]+r*sin(ang)))
    pp.append(points[-1]); ns=[]
    for a,b in zip(pp,pp[1:]):
        u=unit(a,b); ns.append((-u[1],u[0]))
    sides=[]
    for sign in [1,-1]:
        edge=[]
        for i,p in enumerate(pp):
            n=ns[0] if i==0 else ns[-1] if i==len(pp)-1 else (ns[i-1][0]+ns[i][0],ns[i-1][1]+ns[i][1])
            mag=hypot(*n);n=(n[0]/mag,n[1]/mag)
            div=n[0]*ns[min(i,len(ns)-1)][0]+n[1]*ns[min(i,len(ns)-1)][1]
            edge.append(shift(p,n,sign*width*.5/div))
        sides.append(edge)
    p=Polygon(sides[0]+sides[1][::-1])
    return p if p.is_valid else p.buffer(0)


def pieces(g, kind):
    if g.is_empty: return
    if g.geom_type == kind: yield g
    elif hasattr(g,'geoms'):
        for part in g.geoms: yield from pieces(part,kind)


class Network:
    def __init__(self, rows, mh):
        self.rows={r['tag']:r for r in rows}; self.mh=mh
        self.points={}; self.polygons={}; self.connections=[]; self.transitions=[]
        for tag,r in self.rows.items():
            p=json.loads(r['points_mm']); p=[p[0]]+[q for i,q in enumerate(p[1:],1) if hypot(q[0]-p[i-1][0],q[1]-p[i-1][1])>=10]
            self.points[tag]=[(x,mh-y) for x,y in p]
        self.original={t:list(p) for t,p in self.points.items()}
        self.make_main_transitions()
        for tag,r in self.rows.items():
            # RA-B08 retains the registered miter / turning-vane elbow. Its
            # short straight station cannot contain the previous radius bend
            # and the branch devices at the same time.
            self.polygons[tag]=outline(self.points[tag],float(r['width_mm']),bool(r['diameter_mm']) or tag=='RA-B08')
        for tr in self.transitions:
            owner=tr['owner'];self.polygons[owner]=self.polygons[owner].union(tr['polygon'])
        self.connect_branches()
        self.connect_room_networks()
        self.boundaries={}
        for tag,p in self.polygons.items():
            boundary=p.boundary
            for a,b,q,rad in self.connections:
                other=b if a==tag else a if b==tag else None
                if other:
                    # Keep the exterior of the connected UNION. Subtracting a
                    # buffered neighbour erased shared OUTSIDE walls and left
                    # the gaps visible in the user's Rev07 close-ups.
                    window=Point(q).buffer(rad)
                    external=p.union(self.polygons[other]).boundary.buffer(.02)
                    boundary=boundary.difference(window).union(boundary.intersection(window).intersection(external))
            self.boundaries[tag]=boundary

    def connect(self,a,b,q,rad):
        if a==b:return
        if not any({a,b}=={x,y} and Point(q).distance(Point(p))<1 for x,y,p,_ in self.connections):
            self.connections.append((a,b,q,rad))

    def make_main_transitions(self):
        for air in ['SA','RA']:
            mains=[r for r in self.rows.values() if r['air_type']==air and r['role']=='Main']
            for i,(previous,nxt) in enumerate(zip(mains,mains[1:]),1):
                pt,nt=previous['tag'],nxt['tag']; pp,qq=self.points[pt],self.points[nt]
                q=pp[-1] if air=='SA' else pp[0]
                end=qq[0] if air=='SA' else qq[-1]
                if Point(q).distance(Point(end))>.1:continue
                # Leave a constant-width tee station before the downstream taper.
                branches=[r for r in self.rows.values() if r['role']=='Branch' and r['air_type']==air and Point(self.original[r['tag']][0 if air=='SA' else -1]).distance(Point(q))<1]
                bw=max([float(r['width_mm']) for r in branches]+[0])
                offset=bw*.625+80
                if air=='SA': u=unit(qq[0],qq[1]);available=Point(qq[0]).distance(Point(qq[1])); wa,wb=float(previous['width_mm']),float(nxt['width_mm']);owner=pt
                else: u=unit(pp[0],pp[1]);available=Point(pp[0]).distance(Point(pp[1]));wa,wb=float(nxt['width_mm']),float(previous['width_mm']);owner=nt
                L=max(350,abs(wa-wb)*2.5)
                L=min(L,available-offset-75)
                if L<180:offset=40;L=max(180,min(350,available-100))
                start,finish=shift(q,u,offset),shift(q,u,offset+L)
                if air=='SA':pp[-1]=start;qq[0]=finish
                else:qq[-1]=start;pp[0]=finish
                self.transitions.append({'tag':f'F-{air}-RED-{i:02d}','air':air,'owner':owner,'upstream':pt if air=='SA' else nt,'downstream':nt if air=='SA' else pt,'q':q,'start':start,'finish':finish,'length_mm':round(L),'wide_mm':max(wa,wb),'narrow_mm':min(wa,wb),'polygon':taper(start,finish,wa,wb),'type':'Main tapered transition'})
                self.connect(pt,nt,finish if air=='SA' else finish,max(wa,wb)*1.5+L+offset)

    def parent_at(self,child,q,roles):
        r=self.rows[child];candidates=[]
        for tag,p in self.original.items():
            o=self.rows[tag]
            if tag==child or o['air_type']!=r['air_type'] or o['role'] not in roles:continue
            if 'Main' not in roles and o['room']!=r['room']:continue
            if LineString(p).distance(Point(q))<1:
                # At a main step choose the upstream wider station for supply,
                # downstream station for return; both adjoining mains get an opening.
                candidates.append(tag)
        # A return enlargement is downstream of the tee. The wider section's
        # ORIGINAL endpoint is at the tee but its actual profile starts after
        # the taper; attach the boot to the section that really contains it.
        return sorted(candidates,key=lambda t:(not self.polygons[t].covers(Point(q)),-float(self.rows[t]['width_mm'])))

    def adapt(self,child,parent,q,tag,kind):
        r,par=self.rows[child],self.rows[parent];p=self.original[child]
        endpoint=0 if r['air_type']=='SA' else -1
        a,b=(p[0],p[1]) if endpoint==0 else (p[-1],p[-2])
        u=unit(a,b); pw,cw=float(par['width_mm']),float(r['width_mm'])
        pl=self.original[parent];segments=[(aa,bb) for aa,bb in zip(pl,pl[1:]) if LineString([aa,bb]).distance(Point(q))<1]
        pa,pb=max(segments,key=lambda ab:Point(ab[0]).distance(Point(ab[1])))
        pu=unit(pa,pb);perp=abs(u[0]*pu[0]+u[1]*pu[1])<.2
        # A flared boot for a side takeoff; an inline reducer for an axial takeoff.
        start=shift(q,u,pw/2 if perp else 0)
        mouth=cw*1.25 if perp else pw
        available=Point(a).distance(Point(b))-(pw/2 if perp else 0)
        L=min(300,max(100,available*.6))
        if available<100 or (not perp and abs(mouth-cw)<1):
            self.connect(child,parent,q,max(pw,cw)*1.5);return
        finish=shift(start,u,L)
        # Trim the child's opening to the taper mouth, while retaining the same
        # network centreline and terminal airflow data.
        cone=taper(start,finish,mouth,cw)
        self.polygons[child]=self.polygons[child].union(cone)
        self.transitions.append({'tag':tag,'air':r['air_type'],'owner':child,'upstream':parent if r['air_type']=='SA' else child,'downstream':child if r['air_type']=='SA' else parent,'q':q,'start':start,'finish':finish,'length_mm':round(L),'wide_mm':round(mouth),'narrow_mm':round(cw),'polygon':cone,'type':kind})
        self.connect(child,parent,q,pw+L+cw)

    def connect_branches(self):
        for tag,r in self.rows.items():
            if r['role']!='Branch':continue
            q=self.original[tag][0 if r['air_type']=='SA' else -1]
            candidates=self.parent_at(tag,q,['Main'])
            if not candidates:continue
            self.adapt(tag,candidates[0],q,'TR-'+tag,'Tapered room-branch boot')
            for parent in candidates[1:]:
                if self.polygons[parent].covers(Point(q)):
                    self.connect(tag,parent,q,float(self.rows[parent]['width_mm'])*1.5)

    def connect_room_networks(self):
        tags=[t for t,r in self.rows.items() if r['role']!='Main']
        for i,tag in enumerate(tags):
            r=self.rows[tag]
            if r['role'] in ['Runout','Extract runout']:
                q=self.original[tag][0 if r['air_type']=='SA' else -1]
                parents=self.parent_at(tag,q,['Room header','Branch','Extract branch'])
                if parents:self.adapt(tag,parents[0],q,'TR-'+tag,'Rectangular-to-round terminal adaptor')
                for parent in parents[1:]:self.connect(tag,parent,q,float(self.rows[parent]['width_mm'])*1.5)
            for other in tags[i+1:]:
                o=self.rows[other]
                if r['room']!=o['room'] or r['air_type']!=o['air_type']:continue
                for q in [self.original[tag][0],self.original[tag][-1]]:
                    if LineString(self.original[other]).distance(Point(q))<1:
                        self.connect(tag,other,q,max(float(r['width_mm']),float(o['width_mm']))*1.6)
                for q in [self.original[other][0],self.original[other][-1]]:
                    if LineString(self.original[tag]).distance(Point(q))<1:
                        self.connect(tag,other,q,max(float(r['width_mm']),float(o['width_mm']))*1.6)

    def draw(self,sc,rows):
        for r in rows:
            tag=r['tag'];k=r['air_type']
            for poly in pieces(self.polygons[tag],'Polygon'):
                sc.poly(list(poly.exterior.coords)[:-1],k,0,'#FFFFFF')
            for line in pieces(self.boundaries[tag],'LineString'):
                sc.line(list(line.coords),k,10 if r['diameter_mm'] else 13)
            for a,b in zip(self.original[tag],self.original[tag][1:]):
                if Point(a).distance(Point(b))>=900:
                    sc.arrow(shift(a,unit(a,b),Point(a).distance(Point(b))*.25),shift(a,unit(a,b),Point(a).distance(Point(b))*.36),'FLOW',10,80)

    def register(self):
        return [{'tag':t['tag'],'type':t['type'],'air':t['air'],'upstream':t['upstream'],'downstream':t['downstream'],'start_x_mm':round(t['start'][0],1),'start_y_mm':round(self.mh-t['start'][1],1),'end_x_mm':round(t['finish'][0],1),'end_y_mm':round(self.mh-t['finish'][1],1),'plan_mouth_mm':t['wide_mm'],'plan_neck_mm':t['narrow_mm'],'proposed_length_mm':t['length_mm'],'status':'Proposed plan geometry; height conversion / fitting K / fabrication development TBC'} for t in self.transitions]

    def validate(self):
        assert all(p.is_valid and not p.is_empty for p in self.polygons.values())
        assert len([t for t in self.transitions if t['type']=='Main tapered transition'])==13
        # Each taper is joined to its owner, and each connected main has an
        # open seam rather than a superimposed closed reducer rectangle.
        for t in self.transitions:
            assert self.polygons[t['owner']].covers(t['polygon'].representative_point())
        # Regression checks at the commented return junctions: the connected
        # envelope must not lose its exterior when internal seams are opened.
        checks=[]
        cases=[('GF02-main',['RA-B02','RA-M01','RA-M02'],(3500,16400),1200),
               ('GF02-header',['RA-B02','RA-H02-U01','RA-H02-D01'],(6000,16400),500),
               ('RA07-main',['RA-B07','RA-M06'],(15350,8350),700),
               ('RA06-main',['RA-B06','RA-M05','RA-M06'],(11300,8350),700)]
        for name,tags,q,radius in cases:
            if not all(t in self.polygons for t in tags):continue
            window=Point(q[0],self.mh-q[1]).buffer(radius)
            expected=unary_union([self.polygons[t] for t in tags]).boundary.intersection(window)
            actual=unary_union([self.boundaries[t] for t in tags])
            missing=expected.difference(actual.buffer(.1)).length
            assert missing<.1,(name,'missing connected exterior',missing)
            checks.append({'junction':name,'missing_exterior_mm':round(missing,3),'result':'passed'})
        return {'valid_section_polygons':len(self.polygons),'main_transitions':13,'branch_and_terminal_adaptors':len(self.transitions)-13,'topological_connections':len(self.connections),'connected_exterior_checks':checks,'unconnected_crossings':'Preserved as independent section geometry'}
