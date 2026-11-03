"""Extend the submitted Lab 06 SOP network into HW04's modular residence HDA.
Run with Houdini 21 hython. No GUI input or microphone access is used.
"""
from pathlib import Path
import hou,json,sys
from hou_helpers import *
ROOT=Path(__file__).resolve().parents[1]
for d in ['renders','validation','video']: (ROOT/d).mkdir(exist_ok=True)
hou.hipFile.load(str(ROOT/'source/lab06_base.hipnc'),suppress_save_prompt=True,ignore_load_warnings=True)
hou.setFrame(1)
obj=hou.node('/obj/OFFICE');obj.setName('BUILDING_A')
h=obj.node('OFFICE_GENERATOR')
h.type().definition().copyToHDAFile('Embedded',new_name='cis5660::hw04_residences::1.0',new_menu_name='HW04 | NORTH Residences')
hou.hda.installFile('Embedded')
h=h.changeNodeType('cis5660::hw04_residences::1.0',keep_name=True,keep_parms=True,keep_network_contents=True)
h.setName('BUILDING_GENERATOR');h.allowEditingOfContents()
for nb in h.networkBoxes():nb.destroy()
pg=h.parmTemplateGroup()
for name in ['intro']:pg.remove(name)
pg.insertBefore('seed',hou.LabelParmTemplate('intro','NORTH / RESIDENCES — HW04',column_labels=('One HDA / two architectural presets / metres',)))
general=hou.FolderParmTemplate('detail_controls','Doors / Windows / Balconies')
templates=[fparm('window_w','Window width',2.15,1.2,3.2),fparm('window_h','Window height',2.25,1.5,2.6),iparm('window_divs','Window mullions',1,0,4),
 fparm('door_w','Door width',1.65,1.1,2.5),fparm('door_h','Door height',2.65,2.2,2.9),hou.ToggleParmTemplate('door_double','Double door',default_value=True),
 fparm('balcony_w','Balcony width',2.7,2.0,3.8),fparm('balcony_h','Balcony railing height',1.05,.8,1.3),fparm('balcony_d','Balcony depth',1.2,.65,1.8),
 fparm('rail_spacing','Railing spacing',.22,.12,.4),hou.MenuParmTemplate('rail_style','Railing style',('vertical','horizontal'),('Vertical bars','Horizontal rails')),
 iparm('balcony_every','Balcony every N bays',2,1,4),hou.ToggleParmTemplate('supports','Automatic supports',default_value=True),
 fparm('support_spacing','Support spacing',2.5,1.5,4),fparm('support_width','Support section',.12,.07,.22),fparm('support_min','Minimum overhang',.18,.08,.4)]
for t in templates:general.addParmTemplate(t)
pg.insertBefore('floors',general)
floor=pg.find('floors')
floor.addParmTemplate(fparm('offsetx_#','X offset (absolute)',0,-3,3))
floor.addParmTemplate(fparm('offsetz_#','Z offset (absolute)',0,-3,3))
floor.addParmTemplate(hou.ToggleParmTemplate('balconies_#','Balconies',default_value=True))
pg.replace('floors',floor);h.setParmTemplateGroup(pg)

def control(name,entries):
    c=node(h,'null',name,comment='Part 2 | Edit the parameters here or on the HDA. These channels drive the asset geometry.')
    g=hou.ParmTemplateGroup()
    for local,label,rootname in entries:
        src=h.parm(rootname).parmTemplate();src.setName(local);src.setLabel(label);g.append(src)
    c.setParmTemplateGroup(g)
    for local,label,rootname in entries:ex(c,local,ref(c,h,rootname))
    c.setColor(hou.Color((.9,.57,.15)))
    return c
wctrl=control('WINDOW_CTRL',[('width','Width','window_w'),('height','Height','window_h'),('mullions','Vertical mullions','window_divs')])
dctrl=control('DOOR_CTRL',[('width','Width','door_w'),('height','Height','door_h'),('double','Double door','door_double')])
bctrl=control('BALCONY_CTRL',[('width','Width','balcony_w'),('height','Railing height','balcony_h'),('depth','Projection depth','balcony_d'),('spacing','Railing spacing','rail_spacing'),('style','Railing style','rail_style')])

assets=h.node('WINDOW_ASSETS')
for n in assets.children():n.destroy()
def make_window(index):
    s=node(assets,'subnet',f'WINDOW_{index}')
    bind={'W':(wctrl,'width'),'H':(wctrl,'height')}
    parts=[]
    for nm,sz,pos in [('left',(.09,'{H}',.20),('-{W}/2+.045',0,.02)),('right',(.09,'{H}',.20),('{W}/2-.045',0,.02)),
       ('head',('{W}',.09,.20),(0,'{H}/2-.045',.02)),('sill',('{W}+.08',.10,.26),(0,'-{H}/2+.04',.06)),
       ('transom',('{W}-.1',.055,.15),(0,'{H}*.25',.04))]:parts.append(dbox(s,nm,sz,pos,bind))
    seed=node(s,'null','empty')
    pts=wr(s,'mullion_positions',seed,'','detail')
    pts.parm('snippet').set(f'int n=int({ref(pts,wctrl,"mullions")}); float w={ref(pts,wctrl,"width")}; for(int i=1;i<=n;i++) addpoint(0,set((float(i)/(n+1)-.5)*(w-.15),0,.04));')
    bar=dbox(s,'mullion',(.055,'{H}-.14',.15),bindings=bind)
    parts.append(node(s,'copytopoints','copy_mullions',(bar,pts),{'transform':0}))
    frames=shade(s,'frame_material',node(s,'merge','frames',parts),'charcoal','frames')
    pane=shade(s,'glass_material',dbox(s,'glass',('{W}-.13','{H}-.13',.055),(0,0,-.025),bind),'glass' if index==0 else 'glass_light','glazing')
    finish(s,asset_id(s,node(s,'merge','model',(frames,pane)),index));return s
win0=make_window(0);win1=make_window(1)
door=node(assets,'subnet','DOOR_MODEL');db={'W':(dctrl,'width'),'H':(dctrl,'height')}
dp=[]
for nm,sz,pos in [('left',(.1,'{H}',.22),('-{W}/2+.05',0,.02)),('right',(.1,'{H}',.22),('{W}/2-.05',0,.02)),
 ('head',('{W}',.10,.22),(0,'{H}/2-.05',.02)),('threshold',('{W}',.06,.24),(0,'-{H}/2+.03',.02))]:dp.append(dbox(door,nm,sz,pos,db))
center=dbox(door,'double_stile',(.06,'{H}',.17),(0,0,.05),db)
empty=node(door,'null','single_door')
sw=node(door,'switch','single_or_double',(empty,center));ex(sw,'input',ref(sw,dctrl,'double'));dp.append(sw)
handle=dbox(door,'handle',(.04,.55,.11),('{W}*.10',-.05,.16),db)
ex(handle,'tx',f'if({ref(handle,dctrl,"double")},{ref(handle,dctrl,"width")}*.10,{ref(handle,dctrl,"width")}*.32)');dp.append(handle)
frame=shade(door,'door_metal',node(door,'merge','frames',dp),'charcoal','frames')
pane=shade(door,'door_glass',dbox(door,'pane',('{W}-.14','{H}-.14',.06),(0,0,-.025),db),'glass','glazing')
finish(door,node(door,'merge','door',(frame,pane)))

bal=node(assets,'subnet','BALCONY_MODEL');bb={'W':(bctrl,'width'),'H':(bctrl,'height'),'D':(bctrl,'depth'),'DH':(dctrl,'height')}
deck=shade(bal,'deck_material',dbox(bal,'deck',('{W}',.16,'{D}'),(0,'-{DH}/2-.08','{D}/2+.08'),bb),'concrete','balcony_deck')
rails=[]
for nm,sz,pos in [('front',('{W}',.065,.065),(0,'-{DH}/2+{H}','{D}+.06')),
 ('left',(.065,.065,'{D}'),('-{W}/2+.03','-{DH}/2+{H}','{D}/2+.08')),
 ('right',(.065,.065,'{D}'),('{W}/2-.03','-{DH}/2+{H}','{D}/2+.08'))]:rails.append(dbox(bal,nm,sz,pos,bb))
for side in [-1,1]:
    for end in [0,1]:
        rails.append(dbox(bal,f'corner_post_{side}_{end}',(.065,'{H}',.065),(f'{side}*({{W}}/2-.03)','-{DH}/2+{H}/2','{D}+.06' if end else '.08'),bb))
pts=wr(bal,'railing_points',node(bal,'null','empty'),'','detail')
pts.parm('snippet').set(f'''float w={ref(pts,bctrl,'width')},d={ref(pts,bctrl,'depth')},step={ref(pts,bctrl,'spacing')};
float y=-{ref(pts,dctrl,'height')}/2+{ref(pts,bctrl,'height')}/2;
int nx=max(2,int(ceil(w/step))),nz=max(2,int(ceil(d/step)));
for(int i=0;i<=nx;i++)addpoint(0,set(-w/2+w*i/nx,y,d+.06));
for(int s=-1;s<=1;s+=2)for(int j=0;j<nz;j++)addpoint(0,set(s*(w/2-.03),y,.08+d*j/nz));''')
bar=dbox(bal,'baluster',(.035,'{H}',.035),bindings=bb)
vertical=node(bal,'copytopoints','vertical_rails',(bar,pts),{'transform':0})
horizontal=[]
for j in range(1,4):
    for nm,sz,pos in [('front',('{W}',.035,.035),(0,f'-{{DH}}/2+{{H}}*{j}/4','{D}+.06')),
      ('left',(.035,.035,'{D}'),('-{W}/2+.03',f'-{{DH}}/2+{{H}}*{j}/4','{D}/2+.08')),
      ('right',(.035,.035,'{D}'),('{W}/2-.03',f'-{{DH}}/2+{{H}}*{j}/4','{D}/2+.08'))]:horizontal.append(dbox(bal,nm+str(j),sz,pos,bb))
hs=node(bal,'merge','horizontal_rails',horizontal)
style=node(bal,'switch','RAILING_STYLE',(vertical,hs));ex(style,'input',ref(style,bctrl,'style'));rails.append(style)
rail=shade(bal,'rail_material',node(bal,'merge','rails',rails),'charcoal','balcony_rails')
finish(bal,node(bal,'merge','balcony',(deck,rail)))

# Compile/Invoke retains the tutorial's reusable Bounds preparation.
cb=node(assets,'compile_begin','prepare_begin',(win0,),{'name':'asset','blockpath':'../prepare_end'})
bounds=node(assets,'bound','bounds',(cb,),{'minsizez':.9})
shrink=node(assets,'xform','cut_inside_frame',(bounds,),{'s':(.90,.94,1)})
cp=node(assets,'attribcopy','copy_ID',(shrink,cb),{'attribname':'ID'})
grp=node(assets,'groupcreate','Bounds_group',(cp,),{'groupname':'Bounds'})
ce=node(assets,'compile_end','prepare_end',(node(assets,'merge','model_and_cutter',(cb,grp)),))
def invoke_asset(src,name):return node(assets,'invoke',name,(src,),{'blockpath':'../prepare_end','inputs':1,'name0':'asset','inputpath0':src.path()})
# Absolute paths would prevent a second HDA instance; use relative Invoke paths.
inv1=invoke_asset(win1,'prepare_window_1');inv1.parm('inputpath0').set('../WINDOW_1')
door2=asset_id(assets,door,2);door2.setName('door_ID_2')
inv2=invoke_asset(door2,'prepare_door');inv2.parm('inputpath0').set('../door_ID_2')
baldoor=node(assets,'merge','door_and_balcony',(inv2,bal))
balid=asset_id(assets,baldoor,3);balid.setName('balcony_ID_3')
finish(assets,node(assets,'merge','collection',(ce,inv1,inv2,balid)))

# Per-floor absolute X/Z offsets; all placement references the translated floor.
meta=h.node('FLOOR_METADATA');begin=h.node('PREVIOUS_FLOORS');align=h.node('STACK_BY_TOP');floorbox=h.node('floor_box')
for axis in ['x','z']:ex(floorbox,'t'+axis,f'ch(strcat("../offset{axis}_",detail("../FLOOR_METADATA","iteration",0)+1))')
h.node('WINDOWS_FOR_CHAIN').parm('group').set('@ID>=2')
proxy=node(h,'xform','reserve_balcony_width',(h.node('packed_ID_proxies'),))
ex(proxy,'sx',f'(max({ref(proxy,wctrl,"width")},{ref(proxy,bctrl,"width")})+.1)/({ref(proxy,wctrl,"width")}*.90+.072)')
h.node('proxy_axis_Z').setInput(0,proxy)
h.parm('spacing').set(.55)
entry=h.node('ground_floor_entrance')
entry.parm('snippet').set('''int fi=detail(1,"iteration",0); int n=npoints(0);
float base=bbox(2,D_YMIN); // replaced below with VEX getbbox_min
'''.replace('float base=bbox(2,D_YMIN); // replaced below with VEX getbbox_min','float base=getbbox_min(2).y;')+f'''
int every=chi("../balcony_every"); int enabled=chi(sprintf("../balconies_%d",fi+1));
int entrance=-1;float best=1e9;vector centre=getbbox_center(2);
for(int p=0;p<n;p++){{
 vector P=point(0,"P",p),N=point(0,"N",p);int rank=0;
 for(int q=0;q<n;q++){{vector Q=point(0,"P",q),M=point(0,"N",q);if(dot(N,M)>.99 && (abs(N.z)>.5 ? Q.x<P.x-.01 : Q.z<P.z-.01))rank++;}}
 setpointattrib(0,"bay",p,rank);
 if(fi>0 && enabled && (N.z>.5 || N.x>.5) && (rank+fi)%every==0){{
  setpointattrib(0,"ID",p,3);P.y=base+{ref(entry,dctrl,'height')}/2+.12;setpointattrib(0,"P",p,P);
 }}
 if(fi==0 && N.z>.5 && abs(P.x-centre.x)<best){{entrance=p;best=abs(P.x-centre.x);}}
}}
if(entrance>=0){{vector P=point(0,"P",entrance);P.y=base+{ref(entry,dctrl,'height')}/2;setpointattrib(0,"ID",entrance,2);setpointattrib(0,"P",entrance,P);}}
''')
entry.setInput(2,align)

# Contour-derived floor borders, swept around closed polygons (tutorial 35:22).
bands=h.node('FLOOR_EDGE_BANDS')
for n in bands.children():n.destroy()
outline=node(bands,'object_merge','floor_outline',values={'objpath1':'../../BOTTOM_FACE','xformtype':0})
# Object Merge relative paths remain instance-local.
outline.parm('objpath1').set('../../BOTTOM_FACE')
path=node(bands,'polypath','closed_outline',(outline,))
profile=node(bands,'grid','border_profile',values={'rows':2,'cols':2,'sizex':.25,'sizey':.18})
profile.parm('orient').set(0) if profile.parm('orient') else None
sweep=node(bands,'sweep','SWEEP_BORDER',(path,profile),{'endcaptype':1})
# The profile is centered; lift the bottom border so its highest edge stays below the next floor.
bottomtrim=node(bands,'xform','bottom_border',(sweep,),{'ty':.13})
toptrim=node(bands,'xform','top_border',(sweep,));ex(toptrim,'ty','ch("../../floor_box/sizey")-.13')
finish(bands,shade(bands,'border_finish',node(bands,'merge','both_borders',(bottomtrim,toptrim)),'limestone','borders'))

# Roof components follow the final floor's offsets as well as dimensions.
def expression_or_value(p):
    try:return p.expression()
    except hou.OperationFailed:return str(p.eval())
roof=h.node('ROOF')
for n in roof.children():
    if n.type().name().startswith('box'):
        for axis in ['x','z']:
            p=n.parm('t'+axis);old=expression_or_value(p)
            ex(n,'t'+axis,'('+old+')+ch(strcat("../../offset'+axis+'_",ch("../../floors")))')
entrynet=h.node('ENTRANCE_CANOPY')
for nm in ['canopy','sign_panel','place_letters']:
    n=entrynet.node(nm)
    for axis in ['x','z']:
        p=n.parm('t'+axis);old=expression_or_value(p)
        ex(n,'t'+axis,'('+old+')+ch("../../offset'+axis+'_1")')
entrynet.node('OFFICE_LETTERS').parm('text').set('N O R T H  /  R E S I D E N C E S')

# Support network and final assembly are built below.
support=node(h,'subnet','AUTOMATIC_SUPPORTS',comment='Part 4 / 40:41 | Boolean overhang mask → resampled outline → Ray to previous floor → Sweep')
prev=node(support,'box','PREVIOUS_STRUCTURAL_FLOOR')
for axis in 'xyz':
    ex(prev,'size'+axis,f'max(.01,detail("../../PREVIOUS_FLOORS","prev_max{axis}",0)-detail("../../PREVIOUS_FLOORS","prev_min{axis}",0))')
    ex(prev,'t'+axis,f'(detail("../../PREVIOUS_FLOORS","prev_max{axis}",0)+detail("../../PREVIOUS_FLOORS","prev_min{axis}",0))/2')
current=node(support,'object_merge','current_underside',values={'objpath1':'../../BOTTOM_FACE','xformtype':0})
cutvolume=node(support,'xform','extend_previous_volume',(prev,))
ex(cutvolume,'sy','1+.4/ch("../PREVIOUS_STRUCTURAL_FLOOR/sizey")')
overhang=node(support,'boolean','OVERHANG_REGION',(current,cutvolume),{'asurface':1,'bsurface':0,'booleanop':2,'subtractchoices':0})
edges=node(support,'convertline','underside_edges',(current,))
path=node(support,'polypath','join_outline',(edges,),{'connectends':1,'closeloops':1})
sample=node(support,'resample','support_spacing',(path,))
ex(sample,'length',ref(sample,h,'support_spacing'))
points=node(support,'add','outline_points',(sample,),{'keep':1})
metain=node(support,'object_merge','loop_metadata',values={'objpath1':'../../FLOOR_METADATA','xformtype':0})
candidate=wr(support,'unsupported_candidates',points,'','point',(prev,overhang,metain))
candidate.parm('snippet').set(f'''vector lo=getbbox_min(1),hi=getbbox_max(1);
vector clo=getbbox_min(0),chi=getbbox_max(0);
int fi=detail(3,"iteration",0);
vector anchor=set(clamp(@P.x,lo.x,hi.x),@P.y,clamp(@P.z,lo.z,hi.z));
float span=distance(@P,anchor);
if(fi==0 || min(chi.x,hi.x)-max(clo.x,lo.x)<.25 || min(chi.z,hi.z)-max(clo.z,lo.z)<.25 ||
 span<{ref(candidate,h,'support_min')} || nprimitives(2)==0 || xyzdist(2,@P)>.02){{removepoint(0,@ptnum);return;}}
v@top=@P;v@top.y-=.015;
float drop=min((hi.y-lo.y)*.7,max(.45,span*.8));
@P.y-=drop;anchor.y=@P.y;
v@N=normalize(anchor-@P);v@ray_origin=@P;
f@span=span;i@support_floor=fi;
''')
ray=node(support,'ray','RAY_TO_PREVIOUS_WALL',(candidate,prev),{'method':1,'dirmethod':2,'dirattrib':'N','putdist':1,'newgrp':1,'maxraydistcheck':1,'maxraydist':8})
segments=wr(support,'connect_support_endpoints',ray,'''int count=npoints(0);
for(int i=0;i<count;i++) {
 vector anchor=point(0,"P",i),origin=point(0,"ray_origin",i),top=point(0,"top",i);
 if(distance(anchor,origin)>.02 && distance(anchor,top)<9) {
  int a=addpoint(0,anchor),b=addpoint(0,top);int prim=addprim(0,"polyline",a,b);
  float span=point(0,"span",i);int fi=point(0,"support_floor",i);
  setprimattrib(0,"support_span",prim,span);
  setprimattrib(0,"support_floor",prim,fi);
 }
}
for(int i=count-1;i>=0;i--)removepoint(0,i);
''','detail')
swept=node(support,'sweep','SWEEP_STEEL_SUPPORTS',(segments,),{'surfaceshape':2,'endcaptype':1})
ex(swept,'width',ref(swept,h,'support_width'))
steel=shade(support,'support_material',swept,'bronze','supports')
off=node(support,'null','NO_SUPPORTS')
enabled=node(support,'switch','SUPPORT_ENABLE',(off,steel));ex(enabled,'input',ref(enabled,h,'supports'))
finish(support,enabled)
h.node('complete_floor').setNextInput(support)

# Record only the current structural box, not decorations, for the next iteration.
store=wr(h,'STORE_PREVIOUS_FOOTPRINT',h.node('accumulate_floors'),'''vector lo=getbbox_min(1),hi=getbbox_max(1);
setdetailattrib(0,"prev_minx",lo.x);setdetailattrib(0,"prev_maxx",hi.x);
setdetailattrib(0,"prev_miny",lo.y);setdetailattrib(0,"prev_maxy",hi.y);
setdetailattrib(0,"prev_minz",lo.z);setdetailattrib(0,"prev_maxz",hi.z);
''','detail',(align,))
h.node('STACK_FLOORS').setInput(0,store)

PRESETS={
 'A':{'seed':17,'window_w':2.15,'window_h':2.25,'window_divs':1,'balcony_w':2.7,'balcony_d':1.2,'rail_style':0,'balcony_every':2,
      'floors':[(16,3.8,11,0,0),(16,3.6,11,0,0),(14.5,3.6,10,-.4,-.15),(12.5,3.6,8.7,-.5,-.25)]},
 'B':{'seed':42,'window_w':2.35,'window_h':2.4,'window_divs':2,'balcony_w':2.8,'balcony_d':1.1,'rail_style':1,'balcony_every':2,
      'floors':[(11.5,3.8,9,0,0),(11.5,3.6,9,0,0),(13,3.6,10.5,1.0,.65),(12.2,3.6,9.5,.5,0),(12.8,3.6,10,-.65,.55),(10.5,3.6,8.5,-.4,.3)]}
}
def apply_preset(n,key):
    data=PRESETS[key]
    for k,v in data.items():
        if k!='floors':n.parm(k).set(v)
    n.parm('floors').set(len(data['floors']))
    for i,(w,height,d,ox,oz) in enumerate(data['floors'],1):
        for key,val in [('x',w),('y',height),('z',d),('offsetx',ox),('offsetz',oz),('pillars',1),('balconies',i>1)]:n.parm(f'{key}_{i}').set(val)
apply_preset(h,'A')
(ROOT/'presets.json').write_text(json.dumps(PRESETS,indent=2))

# Reusable preset buttons live on the asset and operate on the selected instance.
module='PRESETS = '+repr(PRESETS)+'\n'+'''def apply_preset(node,key):
    data=PRESETS[key]
    for k,v in data.items():
        if k!='floors':node.parm(k).set(v)
    node.parm('floors').set(len(data['floors']))
    for i,vals in enumerate(data['floors'],1):
        for k,v in zip(['x','y','z','offsetx','offsetz'],vals):node.parm(k+'_'+str(i)).set(v)
        node.parm('pillars_'+str(i)).set(1)
        node.parm('balconies_'+str(i)).set(i>1)
'''
pg=h.parmTemplateGroup()
for key in ['A','B']:
    button=hou.ButtonParmTemplate('preset_'+key,'Load '+key+(' — Terraces' if key=='A' else ' — Shift'))
    button.setScriptCallback('kwargs["node"].hdaModule().apply_preset(kwargs["node"],"'+key+'")')
    button.setScriptCallbackLanguage(hou.scriptLanguage.Python);pg.insertBefore('seed',button)
h.setParmTemplateGroup(pg)
for n in [wctrl,dctrl,bctrl]:n.setSelected(False)

# Material palette is deliberately shared by both buildings.
for name,color,rough,metal in [('limestone',(.60,.565,.49),.65,0),('charcoal',(.035,.05,.058),.45,.15),
 ('glass',(.055,.16,.21),.20,.35),('glass_light',(.11,.25,.29),.25,.25),('bronze',(.38,.20,.075),.38,.4),
 ('concrete',(.32,.35,.34),.8,0),('ground',(.13,.18,.20),.85,0)]:
    mat=hou.node('/mat/'+name);mat.parmTuple('basecolor').set(color);mat.parm('rough').set(rough);mat.parm('metallic').set(metal)

# Lay out editable chapters in non-overlapping network boxes.
categories=[('01 | Controls',[wctrl,dctrl,bctrl]),('02 | Assets + compiled preparation',[assets]),
 ('03 | Feedback stack',[begin,meta,floorbox,align,store,h.node('STACK_FLOORS'),h.node('accumulate_floors'),h.node('floor_index')]),
 ('04 | Floor borders',[bands]),('05 | Automatic supports',[support]),('06 | Roof + entrance',[roof,entrynet])]
used=set()
for label,members in categories:
    nb=h.createNetworkBox();nb.setComment(label)
    for n in members:nb.addItem(n);used.add(n.path())
rest=[n for n in h.children() if n.path() not in used]
nb=h.createNetworkBox();nb.setComment('07 | Facade placement / wall cuts / columns / assembly')
for n in rest:nb.addItem(n)
cursor=0
for nb in sorted(h.networkBoxes(),key=lambda b:b.comment()):
    h.layoutChildren(items=[x for x in nb.items() if isinstance(x,hou.Node)]);nb.fitAroundContents()
    nb.setPosition(hou.Vector2(cursor,-nb.size().y()));cursor+=nb.size().x()+3
h.type().definition().setParmTemplateGroup(h.parmTemplateGroup())
h.type().definition().updateFromNode(h)
h.type().definition().addSection('PythonModule',module)
h.type().definition().setComment('HW04: Null-controlled original door/window/balcony models, swept borders, conditional Ray/Sweep supports, X/Z offsets and two presets. Reference studies: ODA 251 1st and 2222 Jackson.')

print('COOK_A',flush=True)
try:
    ga=h.geometry();print('A_GEOMETRY',len(ga.prims()),ga.boundingBox(),flush=True)
except Exception:
    print('COOK_ERRORS',[(n.path(),n.errors()) for n in h.allSubChildren() if n.errors()][-3:],flush=True)
    hou.hipFile.save(str(ROOT/'hw04_debug.hipnc'));raise
obj.parm('tx').set(-12)
objB=node(hou.node('/obj'),'geo','BUILDING_B')
for n in objB.children():n.destroy()
b=node(objB,h.type().name(),'BUILDING_GENERATOR')
apply_preset(b,'B');b.setDisplayFlag(True);b.setRenderFlag(True)
objB.parm('tx').set(12)
print('COOK_B',flush=True)
gb=b.geometry();print('B_GEOMETRY',len(gb.prims()),gb.boundingBox(),flush=True)
errors=[{'node':n.path(),'errors':n.errors()} for x in [h,b] for n in x.allSubChildren() if n.errors()]
(ROOT/'validation/build_diagnostics.json').write_text(json.dumps(errors,indent=2))
if errors:print('ERRORS',errors,flush=True)

cam=hou.node('/obj/BEAUTY_CAMERA');cam.parm('orthowidth').set(54);aim(cam,(28,28,52),(0,8.8,0))
cam.parmTuple('res').set((1280,900)) if cam.parmTuple('res') else None
cam.parm('resx').set(1280);cam.parm('resy').set(900)
rop=hou.node('/out/PREVIEW');rop.parm('picture').set('$HIP/renders/residences_pair.png')
rop.parm('res1').set(1280);rop.parm('res2').set(900)
rop.parm('gamma').set(2.2)
hou.node('/obj/SUN').parm('light_intensity').set(1.6)
hou.node('/obj/FILL').parm('light_intensity').set(.7)
beauty=hou.node('/out/BEAUTY_RENDER');beauty.parm('vm_picture').set('$HIP/renders/residences_beauty.png')
for k,v in {'res_overridex':1100,'res_overridey':760,'vm_samplesx':3,'vm_samplesy':3,'vm_maxraysamples':3,'vm_diffuselimit':0,'vm_gamma':1.0}.items():beauty.parm(k).set(v)
for n in [obj,objB]:n.setDisplayFlag(True)
h.setSelected(True,clear_all_selected=True)
hou.node('/obj').layoutChildren()
hou.hipFile.save(str(ROOT/'hw04_residences.hipnc'))
print('SAVED',ROOT/'hw04_residences.hipnc',flush=True)
if '--render' in sys.argv:
    rop.render();print('PREVIEW_DONE',flush=True)
if '--beauty' in sys.argv:
    beauty.render();print('BEAUTY_DONE',flush=True)
