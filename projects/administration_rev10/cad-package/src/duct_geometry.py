"""Rev10 physical duct envelopes, formed junctions and explicit crossing checks.

All walls of a connected service are rendered from one union, after every fill.
Adapters replace the corresponding constant-width throat; they do not overlay
a closed rectangle. Unintended same-service intersections fail validation.
"""
import json
from math import hypot, atan2, cos, sin, pi
from itertools import combinations
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
    def __init__(self, rows, mh, coordination_basis=None):
        self.rows={r['tag']:r for r in rows}; self.mh=mh;self.coordination_basis=coordination_basis
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
        self.form_junctions()
        self.envelopes={air:unary_union([self.polygons[t] for t,r in self.rows.items() if r['air_type']==air])
                        for air in {r['air_type'] for r in rows}}
        self.boundaries={tag:p.boundary.intersection(self.envelopes[self.rows[tag]['air_type']].boundary.buffer(.02))
                         for tag,p in self.polygons.items()}
        self.crossings=self.find_crossings()

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
        L=min(300,max(100,available*.4))
        if child in ['SA-B06','RA-B06']:
            # The common corridor branch uses a straight formed take-off,
            # preserving its measured device station before the header tee.
            self.connect(child,parent,q,max(pw,cw)*1.5)
            return
        if available<=150 or (not perp and abs(mouth-cw)<1):
            self.connect(child,parent,q,max(pw,cw)*1.5);return
        finish=shift(start,u,L)
        # Replace the throat. Unioning a cone over the original full rectangle
        # leaves a shoulder / cap and hides walls of neighbouring tee legs.
        cone=taper(start,finish,mouth,cw)
        trimmed=list(self.points[child])
        trimmed[endpoint]=finish
        self.polygons[child]=outline(trimmed,cw,bool(r['diameter_mm'])).union(cone)
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

    def joint_groups(self):
        groups=[]
        for a,b,q,_ in self.connections:
            tags={a,b}
            radius=max(float(self.rows[t]['width_mm']) for t in tags)*1.7
            for x,y,p,_ in self.connections:
                if self.rows[x]['air_type']!=self.rows[a]['air_type']:continue
                # Adjacent short header stations are one manufactured fitting.
                if Point(q).distance(Point(p))<min(radius,max(float(self.rows[x]['width_mm']),float(self.rows[y]['width_mm']))):
                    if tags.intersection({x,y}):tags.update([x,y])
            groups.append((tags,Point(q).buffer(radius)))
        return groups

    def form_junctions(self):
        self.formed_junctions=[]
        handled=set()
        for a,b,q,_ in self.connections:
            key=(self.rows[a]['air_type'],round(q[0],1),round(q[1],1))
            if key in handled:continue
            handled.add(key)
            tags=set()
            for x,y,p,_ in self.connections:
                if Point(p).distance(Point(q))<1:tags.update([x,y])
            tags={t for t in tags if self.rows[t]['air_type']==key[0]}
            if len(tags)<2 or any(t.startswith(('SA-B06','RA-B06')) for t in tags):continue
            if 'SA-B02' in tags and Point(q).distance(Point(self.original['SA-B02'][-1]))<1:
                # Keep a straight distributor tee station beside the two
                # branch devices; turning vanes / selected fitting are pending.
                continue
            # Axial continuations / tapered reducers do not have an elbow
            # crotch. Closing them here can eat the required straight station.
            directions=[]
            for t in tags:
                for start,end in zip(self.original[t],self.original[t][1:]):
                    if LineString([start,end]).distance(Point(q))<1:directions.append(unit(start,end))
            if directions and all(abs(u[0]*directions[0][1]-u[1]*directions[0][0])<.1 for u in directions):continue
            w=min(float(self.rows[t]['width_mm']) for t in tags)
            # Add only the concave fillet material, retaining scheduled straight
            # widths. Work with the identified joint legs, never nearby ducts.
            profile=unary_union([self.polygons[t] for t in tags])
            radius=min(225,w*.55)
            filled=profile.buffer(radius,quad_segs=24).buffer(-radius,quad_segs=24).difference(profile)
            filled=filled.intersection(Point(q).buffer(w*1.1))
            blockers=[p.buffer(1) for t,p in self.polygons.items() if t not in tags and self.rows[t]['air_type']==key[0]]
            if blockers:filled=filled.difference(unary_union(blockers))
            if filled.area>1:
                owner=sorted(tags)[0]
                self.polygons[owner]=self.polygons[owner].union(filled).buffer(0)
                self.formed_junctions.append({'air':key[0],'x_mm':q[0],'y_mm':self.mh-q[1],
                                              'radius_mm':round(radius,1),'legs':' / '.join(sorted(tags))})

    def unintended_overlaps(self):
        errors=[]
        groups=self.joint_groups()
        for a,b in combinations(self.rows,2):
            if self.rows[a]['air_type']!=self.rows[b]['air_type']:continue
            overlap=self.polygons[a].intersection(self.polygons[b])
            if overlap.area<1:continue
            for tags,window in groups:
                if a in tags and b in tags:overlap=overlap.difference(window)
            if overlap.area>2:
                q=overlap.representative_point()
                errors.append({'a':a,'b':b,'area_mm2':round(overlap.area,1),
                               'x_mm':round(q.x,1),'y_mm':round(self.mh-q.y,1)})
        return errors

    def find_crossings(self):
        hits=[]
        order={'SA':0,'RA':1,'EA':2,'OA':3}
        for a,b in combinations(sorted(self.envelopes,key=lambda x:order[x]),2):
            overlap=self.envelopes[a].intersection(self.envelopes[b])
            for region in pieces(overlap,'Polygon'):
                if region.area<100:continue
                c=region.representative_point()
                own=[t for t,p in self.polygons.items() if p.intersection(region).area>10]
                hits.append({'upper':a,'lower':b,'x_mm':round(c.x,1),'y_mm':round(self.mh-c.y,1),
                             'upper_sections':' / '.join(t for t in own if self.rows[t]['air_type']==a),
                             'lower_sections':' / '.join(t for t in own if self.rows[t]['air_type']==b),
                             'status':'Proposed over/under arrangement; set BOD and verify insulation / access before approval',
                             '_region':region})
        hits.sort(key=lambda r:(-r['y_mm'],r['x_mm']))
        for i,r in enumerate(hits,1):r['tag']=f'CX-{i:02d}'
        return hits

    def draw(self,sc,rows):
        services={r['air_type'] for r in rows}
        # Every fill precedes every outline. A later child can no longer erase
        # an earlier header wall or leave a closed cap across a live junction.
        for air in sorted(services):
            for poly in pieces(self.envelopes[air],'Polygon'):
                sc.poly(list(poly.exterior.coords)[:-1],air,0,'#FFFFFF')
        for air in sorted(services):
            edge=self.envelopes[air].boundary
            for crossing in self.crossings:
                if crossing['lower']!=air or crossing['upper'] not in services:continue
                window=crossing['_region'].buffer(65)
                hidden=edge.intersection(window)
                for line in pieces(hidden,'LineString'):sc.line(list(line.coords),air,7,True)
                edge=edge.difference(window)
            for line in pieces(edge,'LineString'):sc.line(list(line.coords),air,13)
        for r in rows:
            tag=r['tag']
            for a,b in zip(self.original[tag],self.original[tag][1:]):
                if Point(a).distance(Point(b))>=900:
                    sc.arrow(shift(a,unit(a,b),Point(a).distance(Point(b))*.35),shift(a,unit(a,b),Point(a).distance(Point(b))*.43),'FLOW',9,60)
        if len(services)>1:
            for r in self.crossings:
                if not {r['upper'],r['lower']}<=services:continue
                x,y=r['x_mm'],self.mh-r['y_mm']
                sc.line([(x,y),(x+400,y-380)],'NOTE',6)
                sc.text(x+425,y-395,r['tag'],85,'NOTE',mask=True)

    def crossing_register(self):
        result=[{k:v for k,v in r.items() if not k.startswith('_')} for r in self.crossings]
        if self.coordination_basis:
            basis=self.coordination_basis;t=basis['external_insulation_mm'];gap=basis['clear_gap_between_insulation_mm'];roof=basis['structure_to_insulation_allowance_mm'];slab=basis['structural_underside_mm_affl']
            for r in result:
                depth=lambda names:max(float(self.rows[tag]['height_mm'] or self.rows[tag]['diameter_mm']) for tag in names.split(' / '))
                hu,hl=depth(r['upper_sections']),depth(r['lower_sections'])
                ub=slab-roof-t-hu;lb=ub-2*t-gap-hl
                r.update({'upper_depth_mm':hu,'lower_depth_mm':hl,'structural_underside_mm_affl':slab,
                          'assumed_insulation_mm':t,'assumed_insulated_gap_mm':gap,'assumed_structure_allowance_mm':roof,
                          'upper_max_local_bod_mm_affl':ub,'lower_max_local_bod_mm_affl':lb,
                          'lowest_insulated_surface_mm_affl':lb-t,'required_stack_mm':hu+hl+4*t+gap+roof,
                          'envelope_status':'Local upper bounds only; BOD, finished ceiling / beams / supports / access and plenum heights not approved'})
        return result

    def check_node_flows(self):
        nodes={}
        for tag,r in self.rows.items():
            p=self.original[tag];q=float(r['flow_l_s']);air=r['air_type']
            for point,sign in [(p[0],-1),(p[-1],1)]:
                nodes.setdefault((air,point),[]).append((tag,q*sign))
        checked=0
        for key,edges in nodes.items():
            if len(edges)<2:continue
            residual=sum(q for _,q in edges)
            assert abs(residual)<.0001,('Airflow imbalance at node',key,edges,residual)
            checked+=1
        return checked

    def register(self):
        return [{'tag':t['tag'],'type':t['type'],'air':t['air'],'upstream':t['upstream'],'downstream':t['downstream'],'start_x_mm':round(t['start'][0],1),'start_y_mm':round(self.mh-t['start'][1],1),'end_x_mm':round(t['finish'][0],1),'end_y_mm':round(self.mh-t['finish'][1],1),'plan_mouth_mm':t['wide_mm'],'plan_neck_mm':t['narrow_mm'],'proposed_length_mm':t['length_mm'],'status':'Proposed plan geometry; height conversion / fitting K / fabrication development TBC'} for t in self.transitions]

    def validate(self):
        assert all(p.is_valid and not p.is_empty for p in self.polygons.values())
        assert len([t for t in self.transitions if t['type']=='Main tapered transition'])==13
        # Each taper is joined to its owner, and each connected main has an
        # open seam rather than a superimposed closed reducer rectangle.
        for t in self.transitions:
            assert self.polygons[t['owner']].covers(t['polygon'].representative_point())
        errors=self.unintended_overlaps()
        assert not errors,('Unintended same-service intersections',errors)
        balanced=self.check_node_flows()
        for a,b in combinations(self.rows,2):
            if self.rows[a]['air_type']!=self.rows[b]['air_type']:continue
            overlap=LineString(self.original[a]).intersection(LineString(self.original[b]))
            assert overlap.length<.1,('Duplicated / retraced centreline',a,b,overlap.length)
        assert all(p.is_valid for p in self.envelopes.values()), 'Invalid service envelope'
        assert all(len([g for g in pieces(self.envelopes[a],'Polygon') if g.area>1])==1 for a in ['SA','RA']), 'Disconnected distribution service'
        return {'valid_section_polygons':len(self.polygons),'main_transitions':13,
                'branch_and_terminal_adaptors':len(self.transitions)-13,
                'topological_connections':len(self.connections),'formed_junctions':len(self.formed_junctions),
                'unintended_same_service_intersections':errors,
                'duplicated_centerlines':'none',
                'balanced_airflow_nodes':balanced,
                'independent_service_crossings':len(self.crossings),
                'crossings_status':'Explicit numbered proposals; elevations and insulation clearance still require coordination',
                'outline_method':'One continuous exterior per service; no per-section wall masking'}
