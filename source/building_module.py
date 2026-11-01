"""Houdini HDA PythonModule. The builder prepends terrace_layout.py at embed time."""
import math
import random
import hou

PALETTE = {
    'wood': (.48, .30, .16), 'wood_light': (.62, .43, .25),
    'concrete': (.72, .71, .65), 'metal': (.095, .12, .125),
    'glass': (.16, .25, .27), 'interior': (.30, .29, .26),
    'deck': (.40, .28, .17), 'roof': (.13, .15, .15),
    'ground': (.48, .49, .45), 'leaf': (.19, .28, .12), 'fabric':(.64,.61,.54),
}


def floor_data(asset):
    result = []
    y = .26
    n = asset.evalParm('floors')
    for f in range(n):
        k = f+1
        w = max(10., asset.evalParm('width%d'%k))
        d = max(6., asset.evalParm('depth%d'%k))
        h = max(2.7, asset.evalParm('height%d'%k))
        bays = max(2, min(12, round(w / asset.evalParm('baywidth'))))
        x = asset.evalParm('offsetx%d'%k)
        z = asset.evalParm('offsetz%d'%k) - f*asset.evalParm('setback')
        ms = modules(w,d,bays,x,z,asset.evalParm('recess'),f)
        result.append({'floor':f,'y':y,'h':h,'width':w,'depth':d,'x':x,'z':z,
                       'modules':ms,'rects':[m['rect'] for m in ms]})
        y += h
    return result


class Mesh:
    def __init__(self, geo):
        self.g = geo
        geo.clear()
        for name, default in [('part',''),('shop_materialpath','')]:
            geo.addAttrib(hou.attribType.Prim,name,default)
        geo.addAttrib(hou.attribType.Prim,'Cd',(.5,.5,.5))
        self.counts = {}

    def poly(self, coords, mat, part, color=None):
        p = self.g.createPolygon()
        for coord in coords:
            v = self.g.createPoint(); v.setPosition(coord); p.addVertex(v)
        p.setAttribValue('shop_materialpath','/mat/HW04_'+mat)
        p.setAttribValue('part',part)
        p.setAttribValue('Cd',color or PALETTE[mat])
        return p

    def box(self, center, size, mat, part, color=None):
        if min(size)<=.0001:return
        x,y,z=center; a,b,c=[v/2 for v in size]
        points=[(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
                (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)]
        for face in [(3,2,1,0),(4,5,6,7),(0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2)]:
            self.poly([points[i] for i in face],mat,part,color)
        self.counts[part]=self.counts.get(part,0)+1

    def beam(self, start, end, width, mat='metal', part='support'):
        a,b=hou.Vector3(start),hou.Vector3(end)
        axis=b-a
        if axis.length()<.01:return
        direction=axis.normalized()
        ref=hou.Vector3(0,1,0) if abs(direction[1])<.95 else hou.Vector3(1,0,0)
        u=direction.cross(ref).normalized()*width/2
        v=direction.cross(u).normalized()*width/2
        corners=[a-u-v,a+u-v,a+u+v,a-u+v,b-u-v,b+u-v,b+u+v,b-u+v]
        for face in [(3,2,1,0),(4,5,6,7),(0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2)]:
            self.poly([tuple(corners[i]) for i in face],mat,part)

    def ellipsoid(self, center, radius, mat='leaf', part='foliage', seed=0):
        rng=random.Random(seed)
        nx,ny=10,6; rings=[]
        for j in range(ny+1):
            phi=math.pi*j/ny
            ring=[]
            for i in range(nx):
                th=2*math.pi*i/nx
                noise=1+rng.uniform(-.12,.12)
                ring.append((center[0]+radius[0]*math.sin(phi)*math.cos(th)*noise,
                             center[1]+radius[1]*math.cos(phi)*noise,
                             center[2]+radius[2]*math.sin(phi)*math.sin(th)*noise))
            rings.append(ring)
        col=tuple(c*rng.uniform(.8,1.15) for c in PALETTE[mat])
        for j in range(ny):
            for i in range(nx):
                self.poly([rings[j][i],rings[j][(i+1)%nx],rings[j+1][(i+1)%nx],rings[j+1][i]],mat,part,col)


def point_attrs(g):
    for name,default in [('N',(0.,0.,1.)),('up',(0.,1.,0.)),('scale',(1.,1.,1.))]:
        g.addAttrib(hou.attribType.Point,name,default)
    g.addAttrib(hou.attribType.Point,'name','window')
    for name in ['floor','column','terrace_access']:
        g.addAttrib(hou.attribType.Point,name,0)


def add_instance(g, position, name, normal=(0.,0.,1.), scale=(1.,1.,1.), floor=0,col=0,access=0):
    p=g.createPoint();p.setPosition(position)
    for key,val in [('N',normal),('up',(0.,1.,0.)),('scale',scale),('name',name),
                    ('floor',floor),('column',col),('terrace_access',access)]:p.setAttribValue(key,val)


def layout(node):
    g=node.geometry();g.clear();a=node.parent();point_attrs(g)
    for f in floor_data(a):
        for m in f['modules']:
            r=m['rect']
            add_instance(g, (m['cx'],f['y']+f['h']/2,(r[2]+r[3])/2),
                         'floor',scale=(m['width'],f['h'],r[3]-r[2]),floor=f['floor'],col=m['col'])


def balcony_required(asset, floor, module, lower):
    if not floor['floor'] or not asset.evalParm('balconies'):
        return False
    if asset.evalParm('terraces') and frontage_access(module,lower):
        return False
    return (module['col']+2*floor['floor'])%3==0


def structure(node):
    a=node.parent();mesh=Mesh(node.geometry());floors=floor_data(a)
    rng=random.Random(a.evalParm('seed'))
    slab=a.evalParm('slab');boardpitch=.17
    win=a.node('CTRL_WINDOW');door=a.node('CTRL_DOOR')
    for f in floors:
        base,h=f['y'],f['h']
        for m in f['modules']:
            x0,x1,z0,z1=m['rect'];w=x1-x0;cx=m['cx'];col=m['col']
            # Two solid slabs enclose each apartment without an opaque wall behind its glazing.
            mesh.box((cx,base,z0/2+z1/2),(w,slab,z1-z0),'concrete','floor_slab')
            mesh.box((cx,base+h-slab/2,(z0+z1)/2),(w,slab,z1-z0),'concrete','ceiling')
            # A recessed neutral interior makes the glass read as an opening.
            mesh.box((cx,base+h/2,z0+1.5),(w-.18,h-slab,.10),'interior','interior_back')
            # Thin internal separation walls; end walls are clad with individual timber boards.
            for side in [-1,1]:
                xx=cx+side*(w/2-.07)
                mesh.box((xx,base+h/2,(z0+z1)/2),(.14,h-slab,z1-z0),'wood','party_wall')
                visible_length=(z1-z0) if (col==0 and side==-1) or (col==len(f['modules'])-1 and side==1) else min(a.evalParm('recess')+.22,z1-z0)
                count=max(1,math.ceil(visible_length/boardpitch))
                for j in range(count):
                    zz=z1-visible_length+(j+.5)*visible_length/count
                    shade=rng.uniform(.88,1.08)
                    color=tuple(c*shade for c in PALETTE['wood_light'])
                    mesh.box((xx+side*.087,base+h/2,zz),(.065,h-slab-.05,visible_length/count-.018),'wood_light','timber_siding',color)
            # Timber fascia and a consistent reveal around every facade bay.
            for zz in [z0,z1]:
                front=zz==z1
                lower=floors[f['floor']-1]['rects'] if f['floor'] else []
                access=bool(f['floor'] and a.evalParm('terraces') and frontage_access(m,lower))
                entry=f['floor']==0 and col==len(f['modules'])//2
                use_door=front and (entry or access or balcony_required(a,f,m,lower))
                comp=door if use_door else win
                opening=min(comp.evalParm('width'),w*.87)
                opening_height=min(comp.evalParm('height'),h-.55)
                opening_bottom=base+(.14 if front else .18)
                low_height=max(.04,opening_bottom-base+slab/2)
                high_height=max(.04,base+h-slab/2-opening_bottom-opening_height)
                mesh.box((cx,base-slab/2+low_height/2,zz),(w-.12,low_height,.16),'wood_light','timber_fascia')
                mesh.box((cx,opening_bottom+opening_height+high_height/2,zz),(w-.12,high_height,.16),'wood_light','timber_fascia')
                # Full-height cladding beside the window is made of spaced boards.
                side_width=max(.08,(w-opening)/2)
                for sign in [-1,1]:
                    xstart=cx+sign*(opening/2+side_width/2)
                    nb=max(1,math.ceil(side_width/boardpitch))
                    for b in range(nb):
                        xx=xstart-side_width/2+(b+.5)*side_width/nb
                        color=tuple(c*rng.uniform(.9,1.05) for c in PALETTE['wood_light'])
                        mesh.box((xx,base+h/2,zz),(side_width/nb-.012,h-slab-.05,.16),'wood_light','timber_siding',color)
                if front and not entry and rng.random()<.60:
                    # A few open curtains distinguish inhabited apartments from office bays.
                    curtain_width=opening*rng.choice([.18,.25,.32])
                    sign=rng.choice([-1,1]);center=cx+sign*(opening/2-curtain_width/2-.04)
                    folds=max(3,int(curtain_width/.07))
                    for j in range(folds):
                        xx=center-curtain_width/2+(j+.5)*curtain_width/folds
                        tint=tuple(v*rng.uniform(.9,1.04) for v in PALETTE['fabric'])
                        mesh.box((xx,opening_bottom+opening_height/2,zz-.12-.015*math.sin(j*1.7)),
                                 (curtain_width/folds+.008,opening_height-.10,.022),'fabric','curtain',tint)
            if a.evalParm('borders'):
                for zz in [z0-.04,z1+.04]:
                    mesh.box((cx,base+h-.045,zz),(w+.12,.13,.16),'concrete','floor_border')
                for xx in [x0,x1]:
                    mesh.box((xx,base+h-.045,(z0+z1)/2),(.13,.13,z1-z0),'concrete','floor_border')
            if a.evalParm('pillars'):
                for xx in [x0+.08,x1-.08]:
                    mesh.box((xx,base+h/2,z1+.09),(.11,h-slab,.11),'wood','facade_upright')
            # Topmost modules get a low, dark coping, retaining the stepped silhouette.
            if f['floor']==len(floors)-1:
                mesh.box((cx,base+h+.015,(z0+z1)/2),(w-.04,.07,z1-z0-.04),'roof','roof_membrane')
                for zz in [z0,z1]:mesh.box((cx,base+h+.13,zz),(w,.22,.12),'wood','roof_coping')
                for xx in [x0,x1]:mesh.box((xx,base+h+.13,(z0+z1)/2),(.12,.22,z1-z0),'wood','roof_coping')


def facade(node):
    a=node.parent();g=node.geometry();g.clear();point_attrs(g);floors=floor_data(a)
    wc=a.node('CTRL_WINDOW');dc=a.node('CTRL_DOOR')
    for f in floors:
        low=floors[f['floor']-1]['rects'] if f['floor'] else []
        for m in f['modules']:
            x0,x1,z0,z1=m['rect'];w=x1-x0;idx=f['floor']
            access=bool(idx and a.evalParm('terraces') and frontage_access(m,low))
            is_entry=idx==0 and m['col']==len(f['modules'])//2
            # Doors occupy a complete facade bay as a door-and-sidelight assembly.
            use_door=is_entry or access or balcony_required(a,f,m,low)
            name='door' if use_door else 'window'
            width=dc.evalParm('width') if use_door else wc.evalParm('width')
            height=dc.evalParm('height') if use_door else wc.evalParm('height')
            scale=(min(1,w*.87/width),min(1,(f['h']-.55)/height),1.)
            add_instance(g,(m['cx'],f['y']+.14,z1+.025),name,scale=scale,floor=idx,col=m['col'],access=int(access))
            add_instance(g,(m['cx'],f['y']+.18,z0-.025),'window',normal=(0.,0.,-1.),
                         scale=(min(1,w*.87/wc.evalParm('width')),min(1,(f['h']-.55)/wc.evalParm('height')),1.),floor=idx,col=m['col'])


def balcony_points(node):
    a=node.parent();g=node.geometry();g.clear();point_attrs(g);floors=floor_data(a)
    if not a.evalParm('balconies'):return
    bc=a.node('CTRL_BALCONY')
    for f in floors[1:]:
        lower=floors[f['floor']-1]['rects']
        for m in f['modules']:
            if not balcony_required(a,f,m,lower):continue
            r=m['rect']
            add_instance(g,(m['cx'],f['y']+.12,r[3]+.04),'balcony',
                         scale=(min(1,m['width']*.86/bc.evalParm('width')),1.,1.),floor=f['floor'],col=m['col'])


def railing(mesh, edge, y, height=1.05, spacing=.22):
    x0,z0,x1,z1=edge;length=math.hypot(x1-x0,z1-z0)
    if length<.08:return
    ux,uz=(x1-x0)/length,(z1-z0)/length
    for yy in [y+.12,y+height]:
        mesh.beam((x0,yy,z0),(x1,yy,z1),.045,part='terrace_rail')
    count=max(1,math.ceil(length/spacing))
    for i in range(count+1):
        x,z=x0+(x1-x0)*i/count,z0+(z1-z0)*i/count
        mesh.box((x,y+height/2,z),(.022,height,.022),'metal','terrace_baluster')


def terraces(node):
    a=node.parent();mesh=Mesh(node.geometry());floors=floor_data(a)
    mesh.g.addAttrib(hou.attribType.Global,'terrace_area',0.)
    mesh.g.addAttrib(hou.attribType.Global,'railing_segments',0)
    if not a.evalParm('terraces'):return
    bc=a.node('CTRL_BALCONY')
    total_area=0.;rail_count=0
    for f,upper in zip(floors,floors[1:]):
        decks,rails=terrace_regions(f['rects'],upper['rects'])
        y=upper['y']+.11
        for x0,x1,z0,z1 in decks:
            total_area+=(x1-x0)*(z1-z0)
            if min(x1-x0,z1-z0)<.04:continue
            mesh.box(((x0+x1)/2,y-.025,(z0+z1)/2),(x1-x0,.05,z1-z0),'deck','terrace_deck')
            # Narrow grooves keep the timber scale visible without texture dependencies.
            count=max(1,int((x1-x0)/.18))
            for i in range(1,count):
                xx=x0+i*(x1-x0)/count
                mesh.box((xx,y+.002,(z0+z1)/2),(.012,.008,z1-z0),'wood','deck_joint')
        for edge in rails:
            railing(mesh,edge,y,bc.evalParm('height'),bc.evalParm('spacing'))
        rail_count+=len(rails)
        if a.evalParm('site'):
            # Sparse, correctly scaled furniture makes the generated roof areas legible.
            for m in upper['modules']:
                if m['col']%2 or not frontage_access(m,f['rects'],.85):continue
                cx=m['cx']-.55;zz=m['rect'][3]+.60
                mesh.box((cx,y+.73,zz),(.62,.045,.48),'wood_light','terrace_table')
                for dx in [-.25,.25]:
                    for dz in [-.17,.17]:mesh.box((cx+dx,y+.36,zz+dz),(.025,.72,.025),'metal','table_leg')
                seatx=cx+.63
                mesh.box((seatx,y+.43,zz),(.40,.045,.42),'wood_light','chair_seat')
                mesh.box((seatx+.19,y+.68,zz),(.035,.47,.42),'wood_light','chair_back')
                for dx in [-.15,.15]:
                    for dz in [-.15,.15]:mesh.box((seatx+dx,y+.21,zz+dz),(.025,.42,.025),'metal','chair_leg')
                px=m['cx']+m['width']*.32;pz=m['rect'][3]+.48
                mesh.box((px,y+.20,pz),(.35,.40,.35),'concrete','terrace_pot')
                for j in range(4):
                    angle=math.pi*j/2
                    mesh.ellipsoid((px+.10*math.cos(angle),y+.48+.05*j,pz+.10*math.sin(angle)),(.18,.27,.16),seed=m['col']*20+j+upper['floor']*100)
    mesh.g.setGlobalAttribValue('terrace_area',total_area)
    mesh.g.setGlobalAttribValue('railing_segments',rail_count)


def supports(node):
    a=node.parent();mesh=Mesh(node.geometry());floors=floor_data(a)
    if not a.evalParm('supports'):return
    for f,lower in zip(floors[1:],floors):
        segments=support_segments(f['rects'],lower['rects'])
        for x,z,tx,tz in segments:
            drop=min(lower['h']*.6,max(.6,math.hypot(x-tx,z-tz)*.8))
            mesh.beam((x,f['y']-.10,z),(tx,f['y']-drop,tz),.12,'wood','overhang_brace')
            mesh.beam((x,f['y']-.10,z),(tx,f['y']-.10,tz),.12,'wood','overhang_beam')


def site(node):
    a=node.parent();mesh=Mesh(node.geometry());floors=floor_data(a)
    if not a.evalParm('site'):return
    bounds=[v for f in floors for v in f['rects']]
    x0=min(r[0] for r in bounds);x1=max(r[1] for r in bounds)
    z0=min(r[2] for r in bounds);z1=max(r[3] for r in bounds)
    mesh.box(((x0+x1)/2,-.10,(z0+z1)/2),(x1-x0+8,.25,z1-z0+9),'ground','site_plinth')
    # Pavement is drawn as a small forecourt rather than an unbounded empty plane.
    for row in range(4):
        for col in range(math.ceil((x1-x0+3)/1.4)):
            xx=x0-1.5+(col+.5)*1.4+(row%2)*.7
            zz=z1+.7+row*.7
            mesh.box((xx,.035,zz),(1.37,.05,.67),'concrete','paving')
    for xx in [x0+1.5,x1-1.5]:
        zz=z1+3.4
        mesh.box((xx,.30,zz),(2.1,.52,.85),'concrete','planter')
        mesh.box((xx,.57,zz),(1.95,.04,.7),'interior','soil')
        for j in range(7):
            rng=random.Random(j+round(xx)*5)
            mesh.ellipsoid((xx+rng.uniform(-.8,.8),.85+rng.uniform(0,.25),zz+rng.uniform(-.22,.22)),(.38,.42,.30),seed=j+round(xx)*20)
    # Simple timber bench provides a recognizable human-scale cue.
    xx=(x0+x1)/2-4;zz=z1+3.1
    for j in range(4):mesh.box((xx,.52,zz+j*.12),(2.2,.075,.10),'wood_light','bench')
    for dx in [-.8,.8]:mesh.box((xx+dx,.27,zz+.18),(.09,.48,.42),'metal','bench_leg')
    # The entrance step aligns to the actual ground floor door module.
    ground=floors[0];entry=ground['modules'][len(ground['modules'])//2]
    for i in range(2):
        mesh.box((entry['cx'],.09+i*.08,entry['rect'][3]+.48-i*.13),(3.2,.16+i*.16,.9-i*.26),'concrete','entry_step')


def cook(stage, node):
    {'layout':layout,'structure':structure,'facade':facade,'balconies':balcony_points,
     'terraces':terraces,'supports':supports,'site':site}[stage](node)


def apply_preset(kwargs, preset):
    a=kwargs['node']
    if preset=='dortheavej':
        rows=[(26.4,10.8,3.2,0,0),(26.4,10.8,3.2,0,0),(24.2,10.8,3.2,-1.1,0),(22.,10.8,3.2,-2.2,0)]
        a.setParms({'setback':.16,'recess':1.25,'baywidth':4.4,'terraces':1,'supports':1})
    else:
        rows=[(22.,11.2,3.2,0,0),(22.,11.2,3.2,0,-.4),(19.8,10.5,3.2,-1.1,-.5),(17.6,9.6,3.2,-2.2,-.6),(13.2,8.8,3.2,-2.2,-.7)]
        a.setParms({'setback':.22,'recess':1.15,'baywidth':4.4,'terraces':1,'supports':1})
    a.parm('floors').set(len(rows))
    for i,(w,d,h,x,z) in enumerate(rows,1):
        a.setParms({'width%d'%i:w,'depth%d'%i:d,'height%d'%i:h,'offsetx%d'%i:x,'offsetz%d'%i:z})
