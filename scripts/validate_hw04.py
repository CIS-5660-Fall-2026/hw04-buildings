"""Validate actual HDA geometry, parameter behavior and conditional supports."""
from pathlib import Path
import collections,json,math,hashlib
import hou
ROOT=Path(__file__).resolve().parents[1]
labs_before=[p for p in hou.hda.loadedFiles() if 'sidefxlabs' in p.lower()]
hou.hipFile.load(str(ROOT/'hw04_residences.hipnc'),suppress_save_prompt=True,ignore_load_warnings=True)
a=hou.node('/obj/BUILDING_A/BUILDING_GENERATOR');b=hou.node('/obj/BUILDING_B/BUILDING_GENERATOR')
report={'houdini':hou.applicationVersionString(),'labs_loaded_before_open':labs_before,'cases':[]}
assert a.type()==b.type()
assert a.type().definition().libraryFilePath()=='Embedded'
assert a.node('SIDE_WALLS').type().definition().libraryFilePath()=='Embedded'

def groupcount(g,name):
    group=g.findPrimGroup(name);return len(group.prims()) if group else 0
def panes(g):
    group=g.findPrimGroup('glazing');assert group
    bypt=collections.defaultdict(list)
    for p in group.prims():
        for pt in p.points():bypt[pt.number()].append(p)
    visited=set();result=[]
    for p in group.prims():
        if p.number() in visited:continue
        stack=[p];pts={};part=[]
        while stack:
            q=stack.pop()
            if q.number() in visited:continue
            visited.add(q.number());part.append(q)
            for pt in q.points():pts[pt.number()]=pt.position();stack.extend(bypt[pt.number()])
        assert len(part)==6
        centre=sum(pts.values(),hou.Vector3())/len(pts)
        result.append((part[0].intAttribValue('floor_index'),part[0].intAttribValue('ID'),tuple(centre)))
    return result
def check(n,label):
    g=n.geometry();assert g is not None and len(g.prims())>0
    errs=[(x.path(),x.errors()) for x in n.allSubChildren() if x.errors()];assert not errs,str(errs)
    assert all(math.isfinite(x) for pt in g.points() for x in pt.position())
    fl=n.evalParm('floors');ps=panes(g);sides=collections.defaultdict(set)
    for i,asset,pos in ps:
        x,y,z=pos;ox=n.evalParm(f'offsetx_{i+1}');oz=n.evalParm(f'offsetz_{i+1}')
        w=n.evalParm(f'x_{i+1}');d=n.evalParm(f'z_{i+1}')
        if abs(abs(x-ox)-(w/2-.025))<.01:sides[i].add('X+' if x>ox else 'X-')
        elif abs(abs(z-oz)-(d/2-.025))<.01:sides[i].add('Z+' if z>oz else 'Z-')
        else:raise AssertionError(f'Pane off facade {i,asset,pos}')
        base=sum(n.evalParm(f'y_{j}') for j in range(1,i+1))
        expected=base+(n.evalParm('door_h')/2+(.12 if asset==3 else 0) if asset>=2 else n.evalParm(f'y_{i+1}')/2)
        assert abs(y-expected)<.015,(label,i,y,expected)
        if asset==3:assert i>0 and n.evalParm(f'balconies_{i+1}')
    assert len(sides)==fl and all(len(s)==4 for s in sides.values()),sides
    assert sum(asset==2 for _,asset,_ in ps)==1
    height=sum(n.evalParm(f'y_{i}') for i in range(1,fl+1))+.73
    assert abs(g.boundingBox().maxvec().y()-height)<.015,(g.boundingBox(),height)
    col=groupcount(g,'columns');assert col==24*sum(n.evalParm(f'pillars_{i}') for i in range(1,fl+1))
    assert groupcount(g,'borders')>0
    result={'case':label,'passed':True,'floors':fl,'panes':len(ps),'balconies':sum(k==3 for _,k,_ in ps),'support_primitives':groupcount(g,'supports'),
            'primitives':len(g.prims()),'height':height,'pattern':hashlib.sha256(repr(sorted(ps)).encode()).hexdigest()}
    report['cases'].append(result);print('PASS',label,result['panes'],result['support_primitives'],flush=True);return result

ra=check(a,'preset_A');rb=check(b,'preset_B')
assert ra['support_primitives']==0,'Setbacks should not create supports'
assert rb['support_primitives']>0,'Projecting floors need supports'

# Dedicated Null nodes control original geometry, including the extra parameter.
w=a.node('WINDOW_CTRL');oldb=b.evalParm('window_w')
w.parm('width').set(2.85);w.parm('height').set(2.5);w.parm('mullions').set(3)
wg=a.node('WINDOW_ASSETS/WINDOW_0').geometry()
assert abs(wg.boundingBox().sizevec().x()-2.93)<.01
assert abs(wg.boundingBox().sizevec().y()-2.5)<.01
assert b.evalParm('window_w')==oldb,'Instances are coupled'
check(a,'window_Null_and_instance_independence')
a.parm('preset_A').pressButton()
d=a.node('DOOR_CTRL');d.parm('width').set(2.0);d.parm('height').set(2.85)
d.parm('double').set(0);single=len(a.node('WINDOW_ASSETS/DOOR_MODEL').geometry().prims())
d.parm('double').set(1);double=len(a.node('WINDOW_ASSETS/DOOR_MODEL').geometry().prims())
assert double>single
check(a,'door_Null_width_height_single_double')
a.parm('door_w').set(1.65);a.parm('door_h').set(2.65)
bc=a.node('BALCONY_CTRL');bc.parm('width').set(3.1);bc.parm('height').set(1.2);bc.parm('depth').set(1.55)
balgeo=a.node('WINDOW_ASSETS/BALCONY_MODEL').geometry();size=balgeo.boundingBox().sizevec()
assert abs(size.x()-3.1)<.1 and size.z()>1.5 and size.y()>1.3
bc.parm('style').set(0);v=len(a.node('WINDOW_ASSETS/BALCONY_MODEL').geometry().prims())
bc.parm('style').set(1);q=len(a.node('WINDOW_ASSETS/BALCONY_MODEL').geometry().prims());assert v!=q
check(a,'balcony_Null_dimensions_and_railing_style')
a.parm('preset_A').pressButton()
a.parm('seed').set(91);r=check(a,'different_seed');assert r['pattern']!=ra['pattern']
a.parm('seed').set(17);assert check(a,'seed_repeatability')['pattern']==ra['pattern']
a.parm('balconies_2').set(0);a.parm('pillars_3').set(0);check(a,'per_floor_balcony_and_column_toggles')
b.parm('supports').set(0);assert check(b,'supports_disabled')['support_primitives']==0
b.parm('supports').set(1)
for i in range(1,7):
    b.parm(f'x_{i}').set(11.5);b.parm(f'z_{i}').set(9);b.parm(f'offsetx_{i}').set(0);b.parm(f'offsetz_{i}').set(0)
assert check(b,'aligned_floors_no_supports')['support_primitives']==0
b.parm('offsetx_3').set(1.5)
assert check(b,'offset_creates_supports')['support_primitives']>0
b.parm('offsetx_3').set(0)
assert check(b,'removing_offset_removes_supports')['support_primitives']==0
b.parm('floors').set(1);check(b,'single_floor')
b.parm('floors').set(7);check(b,'seven_floors')
report['passed']=True
(ROOT/'validation/parameter_checks.json').write_text(json.dumps(report,indent=2))
print('ALL_CHECKS_PASSED',flush=True)
