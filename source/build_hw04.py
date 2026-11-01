"""Run in Houdini's Python Shell to build the editable HW04 project.

import runpy; _ = runpy.run_path('/absolute/path/to/source/build_hw04.py', run_name='__main__')
The resulting HIP embeds all Python code and its custom HDA definition.
"""
import json
import pathlib
import traceback
import hou

DEST=pathlib.Path(__file__).resolve().parent.parent if '__file__' in globals() else pathlib.Path('/Users/xuan/Documents/Codex/2026-10-14/https-github-com-cis-5660-fall/outputs/hw04-buildings')
SOURCE=DEST/'source'
MODULE=(SOURCE/'terrace_layout.py').read_text()+'\n'+(SOURCE/'building_module.py').read_text()


def set_if(node, values):
    for key,value in values.items():
        p=node.parmTuple(key) if isinstance(value,(list,tuple)) else node.parm(key)
        if p is not None:p.set(value)


def control(parent, name, specifications):
    n=parent.createNode('null',name)
    pg=hou.ParmTemplateGroup()
    for kind,key,label,value,lo,hi in specifications:
        cls=hou.IntParmTemplate if kind=='int' else hou.FloatParmTemplate
        pg.append(cls(key,label,1,default_value=(value,),min=lo,max=hi))
    n.setParmTemplateGroup(pg);n.setColor(hou.Color(.9,.65,.2))
    n.setComment('Edit these parameters to reshape this component. Width and height are in metres.')
    n.setGenericFlag(hou.nodeFlag.DisplayComment,True)
    return n


def expr_tuple(n,key,values):
    for p,v in zip(n.parmTuple(key),values):
        if isinstance(v,str):p.setExpression(v,hou.exprLanguage.Hscript)
        else:p.set(v)


def native_box(parent,name,size,center,material,part):
    n=parent.createNode('box',name)
    expr_tuple(n,'size',size);expr_tuple(n,'t',center)
    tag=parent.createNode('attribwrangle',name+'_material');tag.setInput(0,n)
    tag.parm('class').set(1)
    rgb={'wood': (0.48, 0.3, 0.16), 'wood_light': (0.62, 0.43, 0.25), 'concrete': (0.72, 0.71, 0.65), 'metal': (0.095, 0.12, 0.125), 'glass': (0.16, 0.25, 0.27), 'deck': (0.4, 0.28, 0.17)}[material]
    tag.parm('snippet').set('s@shop_materialpath="/mat/HW04_%s"; s@part="%s"; v@Cd=set(%s);'%(material,part,','.join(map(str,rgb))))
    return tag


def merge(parent,name,nodes):
    n=parent.createNode('merge',name)
    for i,s in enumerate(nodes):n.setInput(i,s)
    return n


def named_piece(parent,name,source,piece):
    n=parent.createNode('attribwrangle',name);n.setInput(0,source);n.parm('class').set(1)
    n.parm('snippet').set('s@name="%s";'%piece)
    return n


def module_network(asset,kind):
    sub=asset.createNode('subnet',kind.upper()+'_MODEL')
    # Spare controls live on real Null nodes, separate from the modeling chains.
    specs={'window':[('float','width','Width',3.65,.5,5),('float','height','Height',2.65,.6,3.8),('int','panes','Vertical Panes',3,1,6)],
           'door':[('float','width','Width',3.65,.7,5),('float','height','Height',2.65,1.8,3.8),('int','double','Double Door',1,0,1)],
           'balcony':[('float','width','Width',3.6,1,5),('float','height','Railing Height',1.05,.7,1.4),('float','depth','Depth',1.2,.5,2.5),('float','spacing','Baluster Spacing',.22,.10,.45)]}[kind]
    ctrl=control(asset,'CTRL_'+kind.upper(),specs)
    # Object-merge is not needed: the control Null only supplies channel references.
    for _,key,_,_,_,_ in specs:
        parm=ctrl.parm(key);parm.setExpression('ch("../%s_%s")'%(kind,key),hou.exprLanguage.Hscript)
    w='ch("../CTRL_%s/width")'%kind.upper()
    h='ch("../CTRL_%s/height")'%kind.upper()
    # Expressions inside the model subnet reach the controls one level further up.
    W='ch("../../CTRL_%s/width")'%kind.upper()
    H='ch("../../CTRL_%s/height")'%kind.upper()
    nodes=[]
    def box(name,size,pos,mat='metal',part=None):
        n=native_box(sub,name,size,pos,mat,part or kind+'_'+name);nodes.append(n);return n
    if kind in ['window','door']:
        box('glass',(W+'-.10',H+'-.10',.035),(0,H+'/2',-.035),'glass')
        for sign,label in [(-1,'left'),(1,'right')]:
            box(label+'_jamb',(.055,H,.11),('%s*(%s)/2'%(sign,W),H+'/2',.025))
        box('head',(W+'+.055',.065,.11),(0,H,.025))
        box('threshold',(W+'+.055',.065,.14),(0,.015,.025))
        if kind=='window':
            box('crossbar',(W,.035,.09),(0,H+'*.38',.045))
            mullion=native_box(sub,'vertical_mullion',(.035,H,.09),(0,0,0),'metal','window_mullion')
            pts=sub.createNode('python','pane_positions')
            pts.parm('python').set('''import hou
n=hou.pwd();g=n.geometry();g.clear();c=n.parent().parent().node('CTRL_WINDOW')
w=c.evalParm('width');h=c.evalParm('height');count=c.evalParm('panes')
for i in range(1,count):
 p=g.createPoint();p.setPosition((-w/2+w*i/count,h/2,.035))
''')
            cp=sub.createNode('copytopoints::2.0','copy_mullions');cp.setInput(0,mullion);cp.setInput(1,pts);nodes.append(cp)
            box('sill',(W+'+.16',.07,.24),(0,-.04,.05),'concrete')
        else:
            D='ch("../../CTRL_DOOR/double")'
            box('meeting_stile',(.045,H,.10),('if(%s,0,-%s*.18)'%(D,W),H+'/2',.055))
            for sign,label in [(-1,'left'),(1,'right')]:
                size=tuple('if(%s,%s,.0001)'%(D,v) for v in (.022,.35,.055)) if sign<0 else (.022,.35,.055)
                x='if(%s,.09,-%s*.18+.09)'%(D,W) if sign>0 else '-.09'
                box(label+'_handle',size,(x,'min(1.1,%s*.48)'%H,.13))
            box('transom',(W,.04,.09),(0,H+'*.78',.045))
    else:
        D='ch("../../CTRL_BALCONY/depth")'
        box('slab',(W,.12,D),(0,-.07,D+'/2'),'concrete')
        box('deck',(W+'-.08',.035,D+'-.08'),(0,.01,D+'/2'),'deck')
        box('front_toprail',(W,.045,.045),(0,H,D))
        box('front_bottomrail',(W,.035,.035),(0,.12,D))
        for sign,label in [(-1,'left'),(1,'right')]:
            box(label+'_toprail',(.045,.045,D),('%s*(%s)/2'%(sign,W),H,D+'/2'))
            box(label+'_bottomrail',(.035,.035,D),('%s*(%s)/2'%(sign,W),.12,D+'/2'))
        bal=native_box(sub,'baluster',(.023,H,.023),(0,0,0),'metal','balcony_baluster')
        pts=sub.createNode('python','railing_positions')
        pts.parm('python').set('''import hou,math
n=hou.pwd();g=n.geometry();g.clear();c=n.parent().parent().node('CTRL_BALCONY')
w=c.evalParm('width');h=c.evalParm('height');d=c.evalParm('depth');s=c.evalParm('spacing')
coords=[]
for i in range(math.ceil(w/s)+1):coords.append((-w/2+w*i/math.ceil(w/s),h/2,d))
for sign in [-1,1]:
 for i in range(math.ceil(d/s)):coords.append((sign*w/2,h/2,d*i/math.ceil(d/s)))
for pos in coords:
 p=g.createPoint();p.setPosition(pos)
''')
        cp=sub.createNode('copytopoints::2.0','copy_balusters');cp.setInput(0,bal);cp.setInput(1,pts);nodes.append(cp)
    assembled=merge(sub,'assemble_'+kind,nodes)
    named=named_piece(sub,'set_piece_name',assembled,kind)
    out=sub.createNode('null','OUT_'+kind.upper());out.setInput(0,named);out.setDisplayFlag(True);out.setRenderFlag(True)
    sub.layoutChildren();sub.setColor(hou.Color(.6,.4,.23))
    return sub


def asset_parameters():
    pg=hou.ParmTemplateGroup()
    main=hou.FolderParmTemplate('massing','Building')
    for name,label,preset in [('preset_a','Dortheavej Variant','dortheavej'),('preset_b','Stepped Variant','sneglehusene')]:
        p=hou.ButtonParmTemplate(name,label)
        p.setScriptCallback("hou.phm().apply_preset(kwargs, '%s')"%preset)
        p.setScriptCallbackLanguage(hou.scriptLanguage.Python);main.addParmTemplate(p)
    multi=hou.FolderParmTemplate('floors','Floors',folder_type=hou.folderType.MultiparmBlock,default_value=4)
    for name,label,val,lo,hi in [('width#','Width',26.4,10,40),('depth#','Depth',10.8,6,20),('height#','Height',3.2,2.7,4.2),('offsetx#','X Offset',0,-8,8),('offsetz#','Z Offset',0,-8,8)]:
        multi.addParmTemplate(hou.FloatParmTemplate(name,label,1,default_value=(val,),min=lo,max=hi))
    main.addParmTemplate(multi)
    for name,label,val,lo,hi in [('baywidth','Target Bay Width',4.4,3,6),('recess','Alternating Recess',1.25,0,2),('setback','Setback per Floor',.16,0,1.5),('slab','Slab Thickness',.20,.12,.35)]:
        main.addParmTemplate(hou.FloatParmTemplate(name,label,1,default_value=(val,),min=lo,max=hi))
    main.addParmTemplate(hou.IntParmTemplate('seed','Facade Variation Seed',1,default_value=(83,),min=0,max=1000))
    pg.append(main)
    components=hou.FolderParmTemplate('components','Components')
    for kind,specs in [('window',[('width',3.65,.5,5),('height',2.65,.6,3.8),('panes',3,1,6)]),
                       ('door',[('width',3.65,.7,5),('height',2.65,1.8,3.8),('double',1,0,1)]),
                       ('balcony',[('width',3.6,1,5),('height',1.05,.7,1.4),('depth',1.2,.5,2.5),('spacing',.22,.1,.45)])]:
        folder=hou.FolderParmTemplate(kind+'_settings',kind.title())
        for key,value,lo,hi in specs:
            cls=hou.IntParmTemplate if key in ['panes','double'] else hou.FloatParmTemplate
            folder.addParmTemplate(cls(kind+'_'+key,key.replace('_',' ').title(),1,default_value=(value,),min=lo,max=hi))
        components.addParmTemplate(folder)
    pg.append(components)
    details=hou.FolderParmTemplate('details','Details')
    for name,label in [('terraces','Automatic Terraces and Access'),('balconies','Balconies'),('supports','Overhang Supports'),('borders','Floor Borders'),('pillars','Repeated Facade Uprights'),('site','Site and Terrace Furniture')]:
        details.addParmTemplate(hou.ToggleParmTemplate(name,label,default_value=True))
    pg.append(details)
    return pg


def materials():
    colors={'wood': (0.48, 0.3, 0.16), 'wood_light': (0.62, 0.43, 0.25), 'concrete': (0.72, 0.71, 0.65), 'metal': (0.095, 0.12, 0.125), 'glass': (0.16, 0.25, 0.27), 'interior': (0.3, 0.29, 0.26), 'deck': (0.4, 0.28, 0.17), 'roof': (0.13, 0.15, 0.15), 'ground': (0.48, 0.49, 0.45), 'leaf': (0.19, 0.28, 0.12), 'fabric': (0.64, 0.61, 0.54)}
    mat=hou.node('/mat')
    for key,col in colors.items():
        n=mat.createNode('principledshader::2.0','HW04_'+key)
        set_if(n,{'basecolor':(1.,1.,1.),'basecolor_usePointColor':1,'rough':.62,'base':1.,'reflect':.25,'ior':1.5})
        if key=='glass':set_if(n,{'rough':.08,'reflect':1.,'transparency':.45,'transcolor':(.8,.9,.9)})
        if key=='metal':set_if(n,{'metallic':.7,'rough':.28})
        if key=='leaf':set_if(n,{'rough':.9,'reflect':.1})
        if key=='fabric':set_if(n,{'rough':.88,'reflect':.12})
        if key in ['wood','wood_light','concrete','metal','deck']:set_if(n,{'roundedEdge_enable':1,'roundedEdge_radius':.008})
    glob=mat.createNode('global','HW04_shading_position')
    for name,lo,hi in [('wood_light',(.39,.25,.13),(.60,.43,.26)),('wood',(.25,.14,.07),(.42,.26,.13)),('deck',(.25,.16,.09),(.43,.29,.17))]:
        noise=mat.createNode('unifiednoise::3.0','HW04_'+name+'_grain')
        noise.setParms({'signature':'v3','freqx':65.,'freqy':.5,'freqz':65.,'fractal':'fbm','oct':3,'rough':.45,'cc_dorng':1})
        noise.parmTuple('cc_rnglo').set(lo);noise.parmTuple('cc_rnghi').set(hi)
        noise.setInput(list(noise.inputNames()).index('pos'),glob,list(glob.outputNames()).index('P'))
        shader=hou.node('/mat/HW04_'+name);shader.setInput(list(shader.inputNames()).index('basecolor'),noise,0)
        shader.parm('basecolor_usePointColor').set(0);shader.parm('rough').set(.65)
        shader.parmTuple('basecolor').set(tuple((a+b)/2 for a,b in zip(lo,hi)))
    mat.layoutChildren()


def build():
    DEST.mkdir(exist_ok=True,parents=True);(DEST/'images').mkdir(exist_ok=True)
    hou.setUpdateMode(hou.updateMode.Manual)
    # Work in a new scene. The existing lab file is never overwritten.
    hou.hipFile.clear(suppress_save_prompt=True)
    materials()
    geo=hou.node('/obj').createNode('geo','TERRACE_WEAVE')
    for n in geo.children():n.destroy()
    a=geo.createNode('subnet','BUILDING_GENERATOR')
    # Attach the module early so Python SOPs can reference it during their first cook.
    a=a.createDigitalAsset(name='ronan83::terrace_weave::1.0',hda_file_name='Embedded',
                           description='HW04 | Terrace Weave',min_num_inputs=0,max_num_inputs=0)
    a.allowEditingOfContents();definition=a.type().definition()
    (DEST/'build-status.txt').write_text('setting clean definition')
    definition.setParmTemplateGroup(asset_parameters());(DEST/'build-status.txt').write_text('definition ready');definition.addSection('PythonModule',MODULE)
    module=a.hdaModule();module.apply_preset({'node':a},'dortheavej')
    def stage(name,key,input_node=None):
        n=a.createNode('python',name)
        n.parm('python').set("hou.pwd().parent().hdaModule().cook('%s', hou.pwd())"%key)
        if input_node:n.setInput(0,input_node)
        return n
    positions=stage('01_floor_layout','layout')
    unit=a.createNode('box','02_unit_floor_box')
    mass=a.createNode('copytopoints::2.0','03_stack_floor_boxes');mass.setInput(0,unit);mass.setInput(1,positions)
    body=stage('04_slabs_timber_and_borders','structure',mass)
    window=module_network(a,'window');door=module_network(a,'door');balcony=module_network(a,'balcony')
    library=merge(a,'05_window_door_library',[window,door])
    points=stage('06_facade_and_access_rules','facade',mass)
    facade=a.createNode('copytopoints::2.0','07_copy_facade_components');facade.setInput(0,library);facade.setInput(1,points)
    set_if(facade,{'useidattrib':1,'idattrib':'name','pack':0})
    bp=stage('08_balcony_placement','balconies',mass)
    balconies=a.createNode('copytopoints::2.0','09_copy_balconies');balconies.setInput(0,balcony);balconies.setInput(1,bp)
    terrace=stage('10_terrace_footprint_difference','terraces',mass)
    support=stage('11_adaptive_overhang_supports','supports',mass)
    plaza=stage('12_forecourt','site',mass)
    merged=merge(a,'13_assemble_building',[body,facade,balconies,terrace,support,plaza])
    normal=a.createNode('normal','14_surface_normals');normal.setInput(0,merged)
    colors=a.createNode('attribwrangle','15_viewport_point_colors');colors.setInput(0,normal);colors.parm('class').set(2)
    colors.parm('snippet').set('int ps[]=pointprims(0,@ptnum);\nif(len(ps)>0){\nstring mat=prim(0,"shop_materialpath",ps[0]);\nif(mat=="/mat/HW04_wood")v@Cd=set(0.63,0.38,0.17);\nif(mat=="/mat/HW04_wood_light")v@Cd=set(0.85,0.60,0.30);\nif(mat=="/mat/HW04_concrete")v@Cd=set(0.72,0.71,0.65);\nif(mat=="/mat/HW04_metal")v@Cd=set(0.095,0.12,0.125);\nif(mat=="/mat/HW04_glass")v@Cd=set(0.16,0.25,0.27);\nif(mat=="/mat/HW04_interior")v@Cd=set(0.3,0.29,0.26);\nif(mat=="/mat/HW04_deck")v@Cd=set(0.4,0.28,0.17);\nif(mat=="/mat/HW04_roof")v@Cd=set(0.13,0.15,0.15);\nif(mat=="/mat/HW04_ground")v@Cd=set(0.48,0.49,0.45);\nif(mat=="/mat/HW04_leaf")v@Cd=set(0.19,0.28,0.12);\nif(mat=="/mat/HW04_fabric")v@Cd=set(0.64,0.61,0.54);\n}\nsetattribtypeinfo(0,"point","Cd","color");')
    color_display=a.createNode('attribdelete','16_point_color_display');color_display.setInput(0,colors)
    color_display.parm('primdel').set('Cd');color_display.parm('vtxdel').set('Cd')
    out=a.createNode('null','OUT_BUILDING');out.setInput(0,color_display);out.setDisplayFlag(True);out.setRenderFlag(True)
    for n in [positions,unit,mass,body]:n.setColor(hou.Color(.35,.52,.63))
    for n in [terrace,support]:n.setColor(hou.Color(.36,.65,.40))
    terrace.setComment('Custom extension: lower footprint minus upper footprint. Railings omit wall contacts; access doors follow usable terraces.')
    terrace.setGenericFlag(hou.nodeFlag.DisplayComment,True)
    a.layoutChildren();a.setDisplayFlag(True);a.setRenderFlag(True)
    definition.setIcon('SOP_box')
    definition.addSection('Help','''Terrace Weave — CIS 5660 HW04\n\nTwo architectural references: BIG Dortheavej Residences and Sneglehusene Housing.\nBuilding: editable floor dimensions, offsets, alternating recess and global setback.\nComponents: native Box SOP modeling, control Nulls, Copy to Points.\nCustom extension: exposed roof areas become terraces, safety rails avoid wall contacts, and facade doors follow terrace access.\nThe HDA PythonModule contains all layout code. No external Python source or texture is needed.\n''')
    definition.updateFromNode(a)
    a.setSelected(True,clear_all_selected=True)
    # Camera and a neutral architectural daylight setup.
    cam=hou.node('/obj').createNode('cam','HERO_CAMERA')
    cam.parmTuple('t').set((31,21,44));cam.parmTuple('r').set((-14.5,35.2,0));cam.parm('focal').set(50)
    cam.parm('projection').set('ortho');cam.parm('orthowidth').set(41)
    cam.parmTuple('res').set((1280,720))
    sun=hou.node('/obj').createNode('hlight','SUN');set_if(sun,{'light_type':'distant','light_intensity':1.05,'light_color':(1.,.90,.76)})
    sun.parmTuple('r').set((-32,-38,0))
    sky=hou.node('/obj').createNode('envlight','SKY');set_if(sky,{'light_intensity':.36,'light_color':(.78,.86,1.)})
    ground=hou.node('/obj').createNode('geo','STUDIO_GROUND')
    for n in ground.children():n.destroy()
    gb=native_box(ground,'ground',(200,.15,200),(0,-.31,0),'concrete','studio_ground')
    gb.parm('snippet').set('s@shop_materialpath="/mat/HW04_ground";v@Cd=set(.55,.57,.53);')
    gb.setDisplayFlag(True);gb.setRenderFlag(True)
    rop=hou.node('/out').createNode('karma','HW04_RENDER')
    set_if(rop,{'camera':cam.path(),'picture':'$HIP/images/hero.png','samplesperpixel':128,'pathtracedsamples':128,'denoiser':'oidn','denoise_usealbedo':1,'denoise_useN':1,
                'soho_foreground':1,'override_camerares':1})
    if rop.parmTuple('res_override'):rop.parmTuple('res_override').set((1280,720))
    hou.setUpdateMode(hou.updateMode.AutoUpdate);out.cook(force=True)
    errors={n.path():n.errors() for n in a.allSubChildren() if n.errors()}
    report={'errors':errors,'bounds':str(out.geometry().boundingBox()),'primitives':len(out.geometry().prims()),
            'terrace_area':terrace.geometry().attribValue('terrace_area'),
            'railing_segments':terrace.geometry().attribValue('railing_segments'),
            'custom_hda_embedded':[d.nodeTypeName() for d in hou.hda.definitionsInFile('Embedded')]}
    (DEST/'build-report.json').write_text(json.dumps(report,indent=2))
    if errors:raise RuntimeError(errors)
    hou.node('/obj').layoutChildren()
    for pane in hou.ui.paneTabs():
        if isinstance(pane,hou.NetworkEditor):pane.setPwd(geo);pane.homeToSelection()
        if isinstance(pane,hou.SceneViewer):
            pane.setPwd(geo);vp=pane.curViewport();vp.setCamera(cam);vp.setDefaultCamera(vp.defaultCamera().stash())
            vp.frameBoundingBox(out.geometry().boundingBox());vp.defaultCamera().setClipPlanes((.05,1000.))
            st=vp.settings();st.showMaterials(False);st.showGeometryColor(True);st.setDisplayTextures(False);st.setLighting(hou.viewportLighting.Off)
            st.setDefaultMaterialDiffuse(hou.Color(1,1,1));st.setDefaultMaterialAmbient(hou.Color(0,0,0));st.setDefaultMaterialSpecular(hou.Color(0,0,0));st.setDefaultMaterialEmission(hou.Color(0,0,0))
            pane.setUsingOCIO(False)
            for visualizer in hou.viewportVisualizers.visualizers():
                try:
                    if visualizer.type().name()=='vis_color':visualizer.setIsActive(False,vp)
                except:pass
    hou.hipFile.save(str(DEST/'hw04.hipnc'))
    print('HW04 BUILD COMPLETE',report)


if __name__=='__main__':
    try:build()
    except Exception:
        hou.setUpdateMode(hou.updateMode.AutoUpdate)
        DEST.mkdir(exist_ok=True,parents=True)
        (DEST/'build-error.txt').write_text(traceback.format_exc())
        print(traceback.format_exc())
