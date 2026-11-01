"""Cook the saved assets and check their controls without changing the HIP."""

import json
import math
from pathlib import Path
import hou


ROOT = Path(__file__).resolve().parents[1]
hou.hipFile.load(str(ROOT / "coastal_houses.hipnc"), suppress_save_prompt=True)
results = []


def check(name, condition, detail=""):
    results.append({"check": name, "passed": bool(condition), "detail": detail})
    print(("PASS " if condition else "FAIL ") + name, detail, flush=True)


def size(node):
    return tuple(node.geometry().boundingBox().sizevec())


def reset(node, preset=0):
    node.parm("preset").set(preset)
    node.parm("apply_preset").pressButton()
    node.parm("supports").set(1)
    node.parm("balconies").set(1)
    node.parm("all_sides").set(1)


a = hou.node("/obj/MANAROLA/building")
b = hou.node("/obj/RIOMAGGIORE/building")
check("One HDA type for both buildings", a.type() == b.type())
check("Building HDA embedded", a.type().definition().libraryFilePath() == "Embedded")
check("Stack HDA embedded", a.node("stack").type().definition().libraryFilePath() == "Embedded")
check("Separate asset library included", (ROOT / "otls/coastal_buildings.hdanc").is_file())

for name, node, floors in [("Manarola", a, 4), ("Riomaggiore", b, 5)]:
    geo = node.geometry()
    check(name + " geometry", len(geo.prims()) > 1000, f"{len(geo.points())} points, {len(geo.prims())} polygons")
    check(name + " floor boxes", len(node.node("stack").geometry().prims()) == floors * 6)
    check(name + " facade layout", len(node.node("windows_points").geometry().points()) == floors * 10 - 1)
    check(name + " one entrance", len(node.node("doors_points").geometry().points()) == 1)
    check(name + " UVs", geo.findVertexAttrib("uv") is not None)
    paths = set(geo.primStringAttribValues("shop_materialpath"))
    check(name + " internal materials", all(hou.node(p) is not None and p.startswith(node.path()) for p in paths))
    check(name + " finite coordinates", all(math.isfinite(v) for p in geo.points() for v in p.position()))

for kind, axis in [("window", 0), ("door", 0), ("balcony", 0)]:
    model = a.node(kind + "_model")
    ctrl = model.node(kind.upper() + "_CTRL")
    check(kind + " Null control", ctrl.type().name() == "null" and all(ctrl.parm(p) for p in ["width", "height"]))
    for parm_name, dimension, value in [("width", axis, 1.6), ("height", 1, 1.3)]:
        parm = a.parm(kind + "_" + parm_name)
        old = parm.eval()
        before = size(model)
        parm.set(value)
        after = size(model)
        check(kind + " " + parm_name + " changes model", abs(before[dimension] - after[dimension]) > .01)
        parm.set(old)

before = len(a.node("window_model").geometry().prims())
a.parm("window_shutters").set(0)
check("Shutters toggle", len(a.node("window_model").geometry().prims()) < before)
a.parm("window_shutters").set(1)
a.parm("window_open_angle").set(0)
closed = size(a.node("window_model"))
a.parm("window_open_angle").set(155)
check("Shutter angle", size(a.node("window_model"))[0] > closed[0])
before = len(a.node("door_model").geometry().prims())
a.parm("door_double_door").set(0)
check("Single / double doors", len(a.node("door_model").geometry().prims()) < before)
a.parm("door_double_door").set(1)
before = size(a.node("balcony_model"))[2]
a.parm("balcony_depth").set(1.2)
check("Balcony depth", size(a.node("balcony_model"))[2] > before)
a.parm("balcony_depth").set(.82)
before = len(a.node("balcony_model").geometry().prims())
a.parm("balcony_rail_spacing").set(.28)
check("Balcony rail spacing", len(a.node("balcony_model").geometry().prims()) < before)
a.parm("balcony_rail_spacing").set(.16)

a.parm("floors").set(1)
check("One-floor case", len(a.node("stack").geometry().prims()) == 6 and len(a.node("copy_balconies").geometry().prims()) == 0)
a.parm("floors").set(8)
check("Eight-floor case", len(a.node("stack").geometry().prims()) == 48 and len(a.geometry().prims()) > 15000)
reset(a)
a.parm("offset_x").set(0)
a.parm("offset_z").set(0)
a.parm("setback").set(0)
check("No supports for aligned floors", len(a.node("overhang_support_points").geometry().points()) == 0)

for x, z in [(.55, .4), (-.55, -.4), (.55, -.4)]:
    a.parm("offset_x").set(x)
    a.parm("offset_z").set(z)
    supports = a.node("overhang_support_points").geometry().points()
    levels = a.node("floor_layout").geometry().points()
    valid = bool(supports)
    for p in supports:
        base = p.floatAttribValue("bottom")
        top = p.floatAttribValue("top")
        scale = p.attribValue("scale")
        pos = p.position()
        floor = p.intAttribValue("floor")
        surfaces = [0]
        for lower in levels[:floor]:
            q = lower.position()
            if abs(pos[0]-q[0]) < lower.floatAttribValue("width")/2 and abs(pos[2]-q[2]) < lower.floatAttribValue("depth")/2:
                surfaces.append(q[1] + lower.floatAttribValue("height")/2)
        valid &= abs(base-max(surfaces)) < 1e-4 and top > base >= 0
        valid &= abs(pos[1]-scale[1]/2-base) < 1e-4 and abs(pos[1]+scale[1]/2-top) < 1e-4
    check(f"Supports land on geometry ({x}, {z})", valid, f"{len(supports)} columns")

a.parm("supports").set(0)
check("Support toggle", len(a.node("copy_supports").geometry().prims()) == 0)
reset(a)
a.parm("balconies").set(0)
check("Balcony toggle", len(a.node("copy_balconies").geometry().prims()) == 0)
reset(a)
a.parm("all_sides").set(0)
check("Front facade only", len(a.node("windows_points").geometry().points()) == 11)
reset(a)
check("Horizontally instanced pilasters", len(a.node("pilaster_points").geometry().points()) > 16)
check("Floor borders", len(a.node("floor_borders").geometry().prims()) > 0)
before = len(a.node("roof_and_chimneys").geometry().prims())
a.parm("chimneys").set(0)
check("Chimney count", len(a.node("roof_and_chimneys").geometry().prims()) < before)
reset(a, 1)
check("Riomaggiore preset button", a.evalParm("floors") == 5 and a.evalParm("roof_style") == 0)
reset(a)
check("Manarola preset button", a.evalParm("floors") == 4 and a.evalParm("roof_style") == 1)

a.parm("width").set(6.2)
a.parm("depth").set(5.5)
a.parm("front_bays").set(4)
a.parm("side_bays").set(3)
a.parm("window_width").set(1.6)
a.parm("window_height").set(1.9)
a.parm("floor_height").set(3.0)
a.parm("setback").set(.3)
a.parm("floors").set(8)
check("Narrow footprint and dense bays cook", len(a.geometry().prims()) > 1000 and not a.errors())
box = a.node("window_model").geometry().boundingBox()
fits = True
for p in a.node("windows_points").geometry().points():
    base = p.intAttribValue("floor") * a.evalParm("floor_height")
    sy = p.attribValue("scale")[1]
    fits &= p.position()[1] + box.minvec()[1]*sy >= base+.19
    fits &= p.position()[1] + box.maxvec()[1]*sy <= base+a.evalParm("floor_height")-.19
check("Tall windows stay within each floor", fits)
reset(a)
a.parm("window_width").set(1.12)
a.parm("window_height").set(1.7)

container = hou.node("/obj").createNode("geo", "portability_check")
fresh = container.createNode("coastal::building::1.0", "fresh_building")
check("Fresh HDA instance cooks", len(fresh.geometry().prims()) > 1000)
for kind in ["window", "door", "balcony"]:
    model = fresh.node(kind + "_model")
    ctrl = model.node(kind.upper() + "_CTRL")
    before = size(model)[0]
    try:
        ctrl.parm("width").deleteAllKeyframes()
        ctrl.parm("width").set(ctrl.evalParm("width") + .2)
        editable = abs(size(model)[0] - before) > .01
    except hou.PermissionError:
        editable = False
    check(kind + " Null editable inside HDA", editable)
errors = []
for node in hou.node("/obj").allSubChildren():
    if isinstance(node, hou.SopNode):
        node.geometry()
        if node.errors():
            errors.append([node.path(), node.errors()])
check("All SOPs cook without errors", not errors, repr(errors))

report = {
    "houdini": hou.applicationVersionString(),
    "license": str(hou.licenseCategory()),
    "passed": sum(r["passed"] for r in results),
    "total": len(results),
    "checks": results,
}
(ROOT / "media/validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"{report['passed']}/{report['total']} checks passed", flush=True)
if report["passed"] != report["total"]:
    raise SystemExit(1)
