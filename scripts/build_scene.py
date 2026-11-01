"""Build the HIP and its embedded assets. Run with Houdini's hython."""

from pathlib import Path
import math
import sys
import hou


ROOT = Path(__file__).resolve().parents[1]
VEX = ROOT / "vex"
COMMON = (VEX / "mesh.vfl").read_text()
BLUE = hou.Color((.26, .46, .60))
GREEN = hou.Color((.32, .53, .40))
GOLD = hou.Color((.65, .49, .24))


def number(name, label, value, low, high, integer=False):
    cls = hou.IntParmTemplate if integer else hou.FloatParmTemplate
    return cls(name, label, 1, default_value=(value,), min=low, max=high,
               min_is_strict=True, max_is_strict=True)


def color(name, label, value):
    return hou.FloatParmTemplate(name, label, 3, default_value=value,
                                naming_scheme=hou.parmNamingScheme.RGBA,
                                look=hou.parmLook.ColorSquare)


def parameters(node, folders):
    group = hou.ParmTemplateGroup()
    for label, items in folders:
        if label:
            group.append(hou.FolderParmTemplate(label.lower().replace(" ", "_"), label, items))
        else:
            for item in items:
                group.append(item)
    node.setParmTemplateGroup(group)


def wrangle(parent, name, source, mesh=False, run_over="detail"):
    node = parent.createNode("attribwrangle", name)
    node.parm("class").set(run_over)
    node.parm("snippet").set((COMMON if mesh else "") + "\n" + source)
    node.setColor(BLUE)
    return node


def source(name):
    return (VEX / (name + ".vfl")).read_text()


def output(parent, input_node, name="OUT"):
    node = parent.createNode("null", name)
    node.setInput(0, input_node)
    node.setDisplayFlag(True)
    node.setRenderFlag(True)
    node.setColor(GREEN)
    return node


def copy(parent, name, model, points):
    node = parent.createNode("copytopoints", name)
    node.setInput(0, model)
    node.setInput(1, points)
    # Keep the model's origin: doors and balconies are anchored at their base.
    node.parm("pivot").set("origin")
    return node


def link(node, names, prefix):
    for name in names:
        parm = node.parm(name)
        parm.setExpression('ch("' + prefix + name + '")')


def stack_parameters():
    return [
        number("floors", "Floors", 4, 1, 8, True),
        number("width", "Width", 8.4, 6.2, 14),
        number("depth", "Depth", 6.4, 5.5, 12),
        number("floor_height", "Floor Height", 3.2, 3.0, 4.5),
        number("offset_x", "X Offset per Floor", 0, -.75, .75),
        number("offset_z", "Z Offset per Floor", .24, -.75, .75),
        number("offset_start", "First Offset Floor (0-based)", 2, 1, 7, True),
        number("setback", "Setback per Floor", .12, 0, .30),
        number("setback_start", "First Setback Floor (0-based)", 3, 1, 7, True),
    ]


def make_stack(parent):
    node = parent.createNode("subnet", "stack")
    parameters(node, [(None, stack_parameters())])
    points = wrangle(node, "floor_centers", source("floors"))
    unit = wrangle(node, "unit_floor", 'box({0,0,0},{1,1,1},{1,1,1},"wall");', True)
    copied = copy(node, "stack_boxes", unit, points)
    output(node, points, "OUT_FLOOR_POINTS").setDisplayFlag(False)
    output(node, copied, "OUT_BOXES")
    node.layoutChildren()
    asset = node.createDigitalAsset(
        name="coastal::box_stack::1.0", description="Coastal Box Stack",
        save_as_embedded=True, min_num_inputs=0, max_num_inputs=0)
    asset.type().definition().setParmTemplateGroup(asset.parmTemplateGroup())
    asset.type().definition().updateFromNode(asset)
    asset.type().definition().addSection("Help", "Stack floor boxes. Offsets begin at the selected floor; setbacks shrink upper footprints.")
    asset.type().definition().copyToHDAFile(str(ROOT / "otls/coastal_buildings.hdanc"))
    return asset


def make_component(parent, kind, controls):
    node = parent.createNode("subnet", kind + "_model")
    ctrl = node.createNode("null", kind.upper() + "_CTRL")
    parameters(ctrl, [(None, controls)])
    ctrl.setColor(GOLD)
    for parm in controls:
        ctrl.parm(parm.name()).setExpression('ch("../../' + kind + "_" + parm.name() + '")')
    code = source("flowers") + "\n" + source(kind) if kind == "window" else source(kind)
    geo = wrangle(node, "model", code, True)
    output(node, geo)
    node.layoutChildren()
    ctrl.setPosition(hou.Vector2(-3, 1))
    return node


PRESETS = {
    "Manarola": {
        "floors": 4, "width": 8.4, "depth": 6.4, "floor_height": 3.2,
        "offset_x": 0.0, "offset_z": .24, "offset_start": 2,
        "setback": .12, "setback_start": 3,
        "front_bays": 3, "side_bays": 2, "balcony_every": 2,
        "wall_color": (.80, .67, .46), "shutter_color": (.075, .19, .14),
        "roof_style": 1, "roof_rise": .85, "chimneys": 2,
        "window_open_angle": 155, "door_double_door": 1,
    },
    "Riomaggiore": {
        "floors": 5, "width": 8.0, "depth": 6.0, "floor_height": 3.2,
        "offset_x": .34, "offset_z": .18, "offset_start": 2,
        "setback": 0.0, "setback_start": 4,
        "front_bays": 3, "side_bays": 2, "balcony_every": 3,
        "wall_color": (.58, .22, .15), "shutter_color": (.055, .14, .10),
        "roof_style": 0, "roof_rise": .85, "chimneys": 1,
        "window_open_angle": 125, "door_double_door": 0,
    },
}


def apply_preset(node, name):
    for key, value in PRESETS[name].items():
        if isinstance(value, tuple):
            node.parmTuple(key).set(value)
        else:
            node.parm(key).set(value)


def materials(parent):
    matnet = parent.createNode("matnet", "materials")
    specs = {"plaster": (.82, 0), "stone": (.68, 0), "wood": (.47, 0),
             "metal": (.28, .65), "glass": (.12, .15), "tile": (.56, 0),
             "flower": (.72, 0), "foliage": (.78, 0), "soil": (1, 0)}
    for name, (roughness, metallic) in specs.items():
        shader = matnet.createNode("principledshader::2.0", name)
        shader.parmTuple("basecolor").set((1, 1, 1))
        shader.parm("basecolor_usePointColor").set(1)
        shader.parm("rough").set(roughness)
        shader.parm("metallic").set(metallic)
        if name == "glass":
            shader.parm("reflect").set(.8)
    matnet.layoutChildren()
    return matnet


def make_building(parent):
    node = parent.createNode("subnet", "building")
    preset = hou.MenuParmTemplate("preset", "Building Preset", ("0", "1"), ("Manarola", "Riomaggiore"))
    button = hou.ButtonParmTemplate("apply_preset", "Apply Preset")
    button.setScriptCallback("hou.pwd().hdaModule().apply_preset(hou.pwd())")
    button.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    window_controls = [
        number("width", "Width", 1.12, .7, 1.6),
        number("height", "Height", 1.7, 1.2, 1.9),
        hou.ToggleParmTemplate("shutters", "Shutters", True),
        number("open_angle", "Shutter Angle", 155, 0, 170),
        number("slats", "Shutter Slats", 12, 4, 20, True),
        hou.ToggleParmTemplate("flower_box", "Window Flowers", True),
        number("flower_count", "Flower Count", 9, 3, 15, True),
    ]
    door_controls = [
        number("width", "Width", 1.45, .8, 1.8),
        number("height", "Height", 2.55, 1.8, 2.7),
        hou.ToggleParmTemplate("double_door", "Double Door", True),
    ]
    balcony_controls = [
        number("width", "Width", 1.95, 1.5, 2.5),
        number("height", "Railing Height", .92, .65, 1.25),
        number("depth", "Depth", .82, .45, 1.4),
        number("rail_spacing", "Rail Spacing", .16, .10, .30),
    ]
    component_folders = []
    for kind, controls in [("window", window_controls), ("door", door_controls), ("balcony", balcony_controls)]:
        items = []
        for template in controls:
            item = template.clone()
            item.setName(kind + "_" + item.name())
            items.append(item)
        component_folders.append((kind.title(), items))
    parameters(node, [
        ("Layout", [preset, button] + stack_parameters() + [
            number("front_bays", "Front / Back Bays", 3, 2, 4, True),
            number("side_bays", "Side Bays", 2, 1, 3, True),
            hou.ToggleParmTemplate("all_sides", "Details on All Sides", True),
            hou.ToggleParmTemplate("balconies", "Balconies", True),
            number("balcony_every", "Balcony Every N Bays", 2, 1, 4, True),
        ]),
        *component_folders,
        ("Structure", [
            hou.ToggleParmTemplate("supports", "Overhang Supports", True),
            number("support_width", "Support Width", .16, .10, .32),
            hou.MenuParmTemplate("roof_style", "Roof", ("0", "1"), ("Terrace", "Tiled Roof"), default_value=1),
            number("roof_rise", "Roof Rise", .85, .30, 1.6),
            number("chimneys", "Chimneys", 2, 0, 3, True),
        ]),
        ("Colors", [
            color("wall_color", "Plaster", (.80,.67,.46)),
            color("trim_color", "Stone", (.77,.72,.60)),
            color("shutter_color", "Shutters", (.075,.19,.14)),
        ]),
    ])

    stack = make_stack(node)
    link(stack, [p.name() for p in stack_parameters()], "../")
    floor_points = node.createNode("object_merge", "floor_layout")
    floor_points.parm("objpath1").set("../stack/OUT_FLOOR_POINTS")
    floor_points.parm("xformtype").set(0)

    models = [make_component(node, "window", window_controls),
              make_component(node, "door", door_controls),
              make_component(node, "balcony", balcony_controls)]
    copies = []
    for kind, model, index in zip(("windows", "doors", "balconies"), models, range(3)):
        points = wrangle(node, kind + "_points", source("facade_points"))
        points.addSpareParmTuple(hou.IntParmTemplate("kind", "Kind", 1, default_value=(index,)))
        points.setInput(1, floor_points)
        copies.append(copy(node, "copy_" + kind, model, points))

    pilaster = wrangle(node, "pilaster_model", '''
vector stone=chv("../trim_color");
box({0,0,.04},{.22,1,.16},stone,"stone");
box({0,-.46,.08},{.32,.08,.24},stone,"stone");
box({0,.46,.08},{.32,.08,.24},stone,"stone");
''', True)
    pillar_points = wrangle(node, "pilaster_points", source("facade_points"))
    pillar_points.addSpareParmTuple(hou.IntParmTemplate("kind", "Kind", 1, default_value=(3,)))
    pillar_points.setInput(1, floor_points)
    copies.append(copy(node, "copy_pilasters", pilaster, pillar_points))
    borders = wrangle(node, "floor_borders", source("borders"), True)
    borders.setInput(1, floor_points)
    support_points = wrangle(node, "overhang_support_points", source("supports"))
    support_points.setInput(1, floor_points)
    support_model = wrangle(node, "support_model", 'box({0,0,0},{1,1,1},chv("../trim_color")*.82,"stone");', True)
    supports = copy(node, "copy_supports", support_model, support_points)
    roof = wrangle(node, "roof_and_chimneys", source("roof"), True)
    roof.setInput(1, floor_points)
    merge = node.createNode("merge", "assemble_building")
    for i, part in enumerate([stack, *copies, borders, supports, roof]):
        merge.setInput(i, part)
    materials(node)
    bind = wrangle(node, "assign_materials", '''
if (s@material=="wall") {
    v@Cd=chv("../wall_color");
    s@material="plaster";
}
s@shop_materialpath=opfullpath("../materials/"+s@material);
''', run_over="primitive")
    bind.setInput(0, merge)
    normals = node.createNode("normal", "corner_normals")
    normals.setInput(0, bind)
    output(node, normals, "OUT_BUILDING")
    node.layoutChildren()
    for title, children in [
        ("Floor layout", [stack, floor_points]),
        ("Facade kit — dive inside for controls", models),
        ("Overhangs", [support_points, support_model, supports]),
    ]:
        box = node.createNetworkBox()
        box.setComment(title)
        for child in children:
            box.addItem(child)
        box.fitAroundContents()
    asset = node.createDigitalAsset(
        name="coastal::building::1.0", description="Coastal House",
        save_as_embedded=True, min_num_inputs=0, max_num_inputs=0)
    definition = asset.type().definition()
    definition.setParmTemplateGroup(asset.parmTemplateGroup())
    definition.updateFromNode(asset)
    module = "PRESETS = " + repr(PRESETS) + '''

def apply_preset(node):
    name = ("Manarola", "Riomaggiore")[node.evalParm("preset")]
    for key, value in PRESETS[name].items():
        if isinstance(value, tuple):
            node.parmTuple(key).set(value)
        else:
            node.parm(key).set(value)
'''
    definition.addSection("PythonModule", module)
    definition.addSection("EditableNodes", "window_model/WINDOW_CTRL door_model/DOOR_CTRL balcony_model/BALCONY_CTRL")
    definition.addSection("Help", '''Coastal House

Use Apply Preset to load either example. Layout controls the floor boxes and
facade bays. The Window, Door, and Balcony tabs drive their yellow Null controls
inside the model subnets. Geometry is copied along all four facades.

Offsets start at a zero-based floor index. Support columns appear only when an
upper corner is outside the previous footprint, and stop at the next floor
underneath or at ground level. Long columns are thicker. Chimneys follow the top
floor, including its offsets and setbacks. Materials and geometry are embedded.
''')
    definition.copyToHDAFile(str(ROOT / "otls/coastal_buildings.hdanc"))
    return asset


def point_camera(camera, position, target):
    dx, dy, dz = (position[i] - target[i] for i in range(3))
    camera.parmTuple("t").set(position)
    camera.parmTuple("r").set((
        -math.degrees(math.atan2(dy, math.hypot(dx, dz))),
        math.degrees(math.atan2(dx, dz)), 0))


def make_setting():
    parent = hou.node("/obj").createNode("geo", "COURTYARD")
    geo = wrangle(parent, "paving_and_furniture", '''
box({0,-.28,0},{28,.5,16},{.34,.36,.33},"stone");
for (int x=0; x<28; x++)
for (int z=0; z<16; z++) {
    vector c=set((x-13.5),-.025,(z-7.5));
    float shade=fit01(rand(x*17+z*231),.88,1.06);
    box(c,{.98,.08,.98},set(.49,.47,.40)*shade,"stone");
}
for (int side=-1; side<=1; side+=2) {
    float x=side*11.9;
    box(set(x,.34,4.6),{1.2,.72,1.2},{.53,.46,.34},"stone");
    box(set(x,.72,4.6),{1.25,.12,1.25},{.65,.58,.46},"stone");
    box(set(x,.78,4.6),{1.03,.03,1.03},{.11,.085,.045},"stone");
    box(set(x,1.42,4.6),{.14,1.4,.14},{.20,.12,.065},"wood");
}
for (int i=0; i<5; i++)
    box(set((i-2)*.16,.55,5.65),{.13,.09,2.4},{.34,.19,.09},"wood");
for (int side=-1; side<=1; side+=2)
    box(set(0,.25,5.65+side*.9),{.72,.5,.08},{.07,.10,.10},"metal");
''', True)
    leaves = parent.createNode("sphere", "leaf_cluster")
    leaves.parm("type").set(1)
    if leaves.parm("freq"):
        leaves.parm("freq").set(2)
    points = wrangle(parent, "tree_points", '''
for (int side=-1; side<=1; side+=2)
for (int i=0; i<5; i++) {
    vector pos=set(side*11.9+sin(i*2.4)*.35,2.05+(i%2)*.45,4.6+cos(i*2.4)*.35);
    int pt=addpoint(0,pos);
    setpointattrib(0,"pscale",pt,.65);
    setpointattrib(0,"Cd",pt,set(.12,.25,.10)*fit01(rand(i+15),.7,1.2));
}
''')
    leaf_color = wrangle(parent, "leaf_color", 'v@Cd=set(.12,.25,.10);', run_over="primitive")
    leaf_color.setInput(0, leaves)
    foliage = copy(parent, "tree_canopies", leaf_color, points)
    merge = parent.createNode("merge", "merge")
    merge.setInput(0, geo)
    merge.setInput(1, foliage)
    normals = parent.createNode("normal")
    normals.setInput(0, merge)
    output(parent, normals)
    shader = hou.node("/mat").createNode("principledshader::2.0", "courtyard")
    shader.parmTuple("basecolor").set((1, 1, 1))
    shader.parm("rough").set(.8)
    parent.parm("shop_materialpath").set(shader.path())
    parent.layoutChildren()


def make_coast():
    coast_code = source("coast")
    specs = [("BEACH", "beach", .94, 0), ("SEA", "sea", .19, .15),
             ("SURF", "foam", .48, 0), ("SKY", "sky", 1, 0)]
    for name, model, roughness, metallic in specs:
        parent = hou.node("/obj").createNode("geo", name)
        geo = wrangle(parent, model, coast_code + "\n" + source(model))
        normals = parent.createNode("normal", "surface_normals")
        normals.parm("cuspangle").set(180)
        normals.setInput(0, geo)
        output(parent, normals)
        shader = hou.node("/mat").createNode("principledshader::2.0", model)
        shader.parmTuple("basecolor").set((1, 1, 1))
        shader.parm("rough").set(roughness)
        shader.parm("metallic").set(metallic)
        if model == "sea":
            shader.parm("ior").set(1.333)
            shader.parm("reflect").set(.65)
        if model == "sky":
            shader.parmTuple("emitcolor").set((.20, .43, .65))
            shader.parm("emitcolor_usePointColor").set(0)
            shader.parm("emitint").set(.65)
            shader.parm("emitillum").set(0)
            shader.parm("reflect").set(0)
        parent.parm("shop_materialpath").set(shader.path())
        parent.layoutChildren()


def make_lighting():
    obj = hou.node("/obj")
    camera = obj.createNode("cam", "presentation_camera")
    point_camera(camera, (32, 18, 50), (0, 7.8, 0))
    camera.parm("projection").set("perspective")
    camera.parm("focal").set(58)
    camera.parm("far").set(2500)
    camera.parm("orthowidth").set(35)
    camera.parmTuple("res").set((960, 720))
    sun = obj.createNode("hlight", "afternoon_sun")
    sun.parm("light_type").set(7)
    point_camera(sun, (-15, 28, 18), (0, 0, 0))
    sun.parm("light_intensity").set(1.0)
    sun.parmTuple("light_color").set((1, .89, .73))
    fill = obj.createNode("hlight", "sky_fill")
    fill.parm("light_type").set(2)
    point_camera(fill, (18, 20, 4), (0, 5, 0))
    fill.parm("light_intensity").set(.55)
    fill.parmTuple("light_color").set((.70, .82, 1))
    if fill.parm("areasize1"):
        fill.parmTuple("areasize").set((18, 18))
    env = obj.createNode("envlight", "sky")
    env.parm("light_intensity").set(.35)
    env.parmTuple("light_color").set((.76, .85, 1))
    rop = hou.node("/out").createNode("ifd", "beauty")
    rop.parm("camera").set(camera.path())
    rop.parm("vm_picture").set("$HIP/media/coastal_houses.png")
    rop.parm("vm_renderengine").set("pbrraytrace")
    rop.parmTuple("vm_samples").set((6, 6))
    rop.parm("vm_maxraysamples").set(4)
    rop.parm("vm_minraysamples").set(1)
    rop.parm("vm_diffuselimit").set(1)
    rop.parm("vm_reflectlimit").set(1)
    rop.parm("vm_refractlimit").set(0)
    rop.parm("vm_alfprogress").set(1)
    gl = hou.node("/out").createNode("opengl", "preview")
    preview_camera = obj.copyItems((camera,))[0]
    preview_camera.setName("preview_camera")
    if sys.platform == "darwin":
        preview_camera.parm("orthowidth").set(70)
        preview_camera.parm("aperture").set(camera.evalParm("aperture") * 2)
        preview_camera.parm("winx").set(.25)
        preview_camera.parm("winy").set(.25)
    gl.parm("camera").set(preview_camera.path())
    gl.parm("picture").set("$HIP/render/preview.$F4.png")
    gl.parm("tres").set(0)
    gl.parmTuple("res").set((960, 720))
    detail_camera = obj.createNode("cam", "facade_camera")
    point_camera(detail_camera, (-3.3, 8.9, 11.5), (-5.5, 7.7, 3.45))
    detail_camera.parm("focal").set(70)
    detail_camera.parmTuple("res").set((720, 540))
    detail = hou.node("/out").copyItems((rop,))[0]
    detail.setName("window_detail")
    detail.parm("camera").set(detail_camera.path())
    detail.parm("vm_picture").set("$HIP/media/window_flowers.png")
    detail.parmTuple("vm_samples").set((4, 4))
    hou.node("/out").layoutChildren()


def main():
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.setFps(24)
    hou.playbar.setFrameRange(1, 240)
    hou.playbar.setPlaybackRange(1, 240)
    obj = hou.node("/obj")
    left = obj.createNode("geo", "MANAROLA")
    a = make_building(left)
    apply_preset(a, "Manarola")
    left.parm("tx").set(-5.5)
    output(left, a, "OUT")
    right = obj.createNode("geo", "RIOMAGGIORE")
    b = right.createNode("coastal::building::1.0", "building")
    apply_preset(b, "Riomaggiore")
    b.parm("preset").set(1)
    right.parm("tx").set(5.2)
    output(right, b, "OUT")
    make_setting()
    make_coast()
    make_lighting()
    for parent in [left, right, obj, hou.node("/mat")]:
        parent.layoutChildren()
    a.setSelected(True, clear_all_selected=True)
    for asset in [a, b]:
        geometry = asset.geometry()
        if geometry is None:
            raise RuntimeError(asset.path() + ": " + str(asset.errors()))
        print(asset.path(), len(geometry.points()), len(geometry.prims()), flush=True)
        if not geometry.prims():
            raise RuntimeError(asset.path() + " has no geometry")
        for child in asset.allSubChildren():
            if child.errors():
                raise RuntimeError(child.path() + ": " + str(child.errors()))
    # Keep the HIP independent of the separately exported asset library.
    library = str(ROOT / "otls/coastal_buildings.hdanc")
    if library in hou.hda.loadedFiles():
        hou.hda.uninstallFile(library)
    for definition in hou.hda.definitionsInFile("Embedded"):
        definition.setIsPreferred(True)
    hou.hipFile.save(str(ROOT / "coastal_houses.hipnc"))
    print("Saved", hou.hipFile.path(), flush=True)


if __name__ == "__main__":
    main()
