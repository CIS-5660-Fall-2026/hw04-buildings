"""Render a truthful, silent parameter demonstration without controlling the desktop.

Each caption is read from the actual HDA state used for that frame. This is an
automated rendered demonstration, not a recording of mouse interaction.
"""
from pathlib import Path
import hou,json,subprocess
from hou_helpers import *
ROOT=Path(__file__).resolve().parents[1]
frames=ROOT/'video/frames';frames.mkdir(parents=True,exist_ok=True)
hou.hipFile.load(str(ROOT/'hw04_residences.hipnc'),suppress_save_prompt=True,ignore_load_warnings=True)
a=hou.node('/obj/BUILDING_A/BUILDING_GENERATOR');b=hou.node('/obj/BUILDING_B/BUILDING_GENERATOR')
oa=a.parent();ob=b.parent();cam=hou.node('/obj/BEAUTY_CAMERA');rop=hou.node('/out/PREVIEW')
rop.parm('res1').set(1120);rop.parm('res2').set(840)
cam.parm('resx').set(1120);cam.parm('resy').set(840)
for k,v in [('ambocclusion',1),('ambquality',1),('aamode',2)]:rop.parm(k).set(v)

hudmat=node(hou.node('/mat'),'principledshader::2.0','HUD_WHITE',values={'basecolor':(.95,.95,.95),'basecolor_usePointColor':0})
if hudmat.parm('emitint'):hudmat.parm('emitint').set(1)
if hudmat.parmTuple('emitcolor'):hudmat.parmTuple('emitcolor').set((1,1,1))
bgmat=node(hou.node('/mat'),'principledshader::2.0','HUD_BG',values={'basecolor':(.016,.025,.032),'basecolor_usePointColor':0})
hud=node(hou.node('/obj'),'geo','DEMO_CAPTIONS');hud.setInput(0,cam)
parts=[]
back=dbox(hud,'banner',(1,1,.005),(0,0,-.16))
ex(back,'sizex','ch("/obj/BEAUTY_CAMERA/orthowidth")')
ex(back,'sizey','ch("/obj/BEAUTY_CAMERA/orthowidth")*.085')
ex(back,'ty','ch("/obj/BEAUTY_CAMERA/orthowidth")*(.375-.0425)')
parts.append(shade(hud,'banner_mat',back,'HUD_BG','banner'))
texts=[]
for i in range(3):
    font=node(hud,'font','caption_'+str(i),values={'text':'','halign':0});texts.append(font)
    tr=node(hud,'xform','place_'+str(i),(font,))
    ex(tr,'scale','ch("/obj/BEAUTY_CAMERA/orthowidth")*'+('.021' if i==0 else '.016'))
    ex(tr,'tx','ch("/obj/BEAUTY_CAMERA/orthowidth")*(-.5+.025)')
    ex(tr,'ty','ch("/obj/BEAUTY_CAMERA/orthowidth")*'+str(.375-.025-i*.024))
    tr.parm('tz').set(-.10)
    parts.append(shade(hud,'label_mat_'+str(i),tr,'HUD_WHITE','labels'))
finish(hud,node(hud,'merge','labels',parts))
assetobj=node(hou.node('/obj'),'geo','ASSET_CLOSEUP');assetmerge=node(assetobj,'object_merge','asset',values={'xformtype':0})
finish(assetobj,assetmerge);assetobj.setDisplayFlag(False)
shots=[]
def configure(mode):
    assetobj.setDisplayFlag(mode.startswith('asset'))
    hou.node('/obj/SITE').setDisplayFlag(not mode.startswith('asset'))
    oa.setDisplayFlag(mode in ['building','pair']);ob.setDisplayFlag(mode=='pair')
    if mode=='pair':
        oa.parm('tx').set(-12);ob.parm('tx').set(12);cam.parm('orthowidth').set(56);aim(cam,(28,28,52),(0,10.5,0))
    elif mode=='building':
        oa.parm('tx').set(0);cam.parm('orthowidth').set(32);aim(cam,(25,20,37),(0,7.0,0))
    else:
        cam.parm('orthowidth').set(7.5);aim(cam,(4,2.6,6),(0,-.1,.2))
def render(title,line1,line2,duration=2):
    for n,s in zip(texts,[title,line1,line2]):n.parm('text').set(s)
    p=frames/f'{len(shots):03d}.png';rop.parm('picture').set(p.as_posix());rop.render()
    shots.append({'frame':p.name,'duration':duration,'title':title,'parameters':[line1,line2]})
    print('FRAME',len(shots),title,flush=True)
def asset(kind):
    configure('asset');assetmerge.parm('objpath1').set(a.path()+'/WINDOW_ASSETS/'+kind)
def gp(name):return a.evalParm(name)

configure('pair');render('NORTH / RESIDENCES — CIS 5660 HW04','One embedded HDA | A: 4 floors | B: 6 floors','Original parameterized assets / swept borders / automatic supports',3)
configure('building');a.parm('preset_A').pressButton()
for floors in [2,3,4]:
    a.parm('floors').set(floors);render('01 / FLOOR STACK',f'Floors = {gp("floors")} | per-floor dimensions remain editable','Feedback + Match Size + procedural facade placement',1.6)
a.parm('preset_A').pressButton()
asset('WINDOW_0')
for w,h,m in [(2.15,2.25,1),(2.9,2.5,3),(1.7,1.9,0)]:
    a.parm('window_w').set(w);a.parm('window_h').set(h);a.parm('window_divs').set(m)
    render('02 / WINDOW_CTRL',f'Width = {gp("window_w"):.2f} | Height = {gp("window_h"):.2f} | Mullions = {gp("window_divs")}','Null channels drive frame, glazing and mullion geometry',2)
a.parm('preset_A').pressButton();asset('DOOR_MODEL')
for w,h,double in [(1.65,2.65,1),(1.25,2.45,0),(2.0,2.85,1)]:
    a.parm('door_w').set(w);a.parm('door_h').set(h);a.parm('door_double').set(double)
    render('03 / DOOR_CTRL',f'Width = {gp("door_w"):.2f} | Height = {gp("door_h"):.2f} | Double = {gp("door_double")}','The door model and its Boolean cutter share these dimensions',2)
a.parm('door_w').set(1.65);a.parm('door_h').set(2.65);asset('BALCONY_MODEL')
for w,h,d,style in [(2.7,1.05,1.2,0),(3.3,1.2,1.65,0),(3.3,1.2,1.65,1)]:
    for k,v in [('balcony_w',w),('balcony_h',h),('balcony_d',d),('rail_style',style)]:a.parm(k).set(v)
    render('04 / BALCONY_CTRL',f'Width = {w:.2f} | Height = {h:.2f} | Depth = {d:.2f}',f'Railing = {"horizontal" if gp("rail_style") else "vertical"} | deck + posts + rails',2)
a.parm('preset_A').pressButton();a.parm('balcony_h').set(1.05);configure('building')
for n in [0,1]:
    a.parm('pillars_2').set(n);a.parm('balconies_2').set(n)
    render('05 / FLOOR DETAILS',f'Floor 2: Columns = {n} | Balconies = {n}','Borders are swept along each floor outline',2)
# Controlled support test: identical footprints first, then an upper-floor shift.
a.parm('floors').set(3)
for i in range(1,4):
    for k,v in [('x',12),('z',9),('y',3.6),('offsetx',0),('offsetz',0)]:a.parm(f'{k}_{i}').set(v)
for x in [0,.7,1.4,2.1]:
    a.parm('offsetx_3').set(x)
    g=a.geometry();sg=g.findPrimGroup('supports');count=len(sg.prims()) if sg else 0
    render('06 / AUTOMATIC OVERHANG SUPPORTS',f'Floor 3 X offset = {gp("offsetx_3"):.2f} m | Support faces = {count}','Boolean region / resampled outline / Ray connection / Sweep',1.5)
for enabled in [0,1]:
    a.parm('supports').set(enabled);render('07 / SUPPORT TOGGLE',f'Floor 3 X offset = 2.10 m | Supports enabled = {enabled}','Visible brackets connect the projecting floor to the floor below',2)
a.parm('offsetx_3').set(0)
render('08 / REMOVE THE OVERHANG','Floor 3 X offset = 0.00 m | footprints aligned','Supports disappear when the overhang is removed',2)
a.parm('preset_A').pressButton();a.parm('seed').set(91)
render('09 / REPEATABLE VARIATION',f'Window seed = {gp("seed")} | Floors = {gp("floors")}','The layout remains procedural when the pattern seed changes',2)
a.parm('preset_A').pressButton();configure('pair')
render('NORTH / RESIDENCES — TWO PRESETS, ONE TOOL','A / Terraces     +     B / Shift','Houdini 21.0.512 Apprentice | HDA and Labs definition embedded',3)
(ROOT/'video/demo_manifest.json').write_text(json.dumps(shots,indent=2))
concat=[]
for shot in shots:
    concat += ["file '"+(frames/shot['frame']).as_posix()+"'",'duration '+str(shot['duration'])]
concat += ["file '"+(frames/shots[-1]['frame']).as_posix()+"'"]
(ROOT/'video/frames.txt').write_text('\n'.join(concat)+'\n')
ffmpeg=Path(hou.expandString('$HFS'))/'bin/hffmpeg.exe'
cmd=[str(ffmpeg),'-y','-f','concat','-safe','0','-i',str(ROOT/'video/frames.txt'),'-vf','fps=24,format=yuv420p','-c:v','libopenh264','-b:v','3500k','-an','-movflags','+faststart',str(ROOT/'video/tool_demo.mp4')]
subprocess.run(cmd,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
print('VIDEO_DONE',flush=True)
