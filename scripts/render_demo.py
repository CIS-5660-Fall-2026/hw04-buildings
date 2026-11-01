"""Render the parameter animation and write its frame-by-frame values."""

import argparse
import json
import sys
from pathlib import Path
import hou


ROOT = Path(__file__).resolve().parents[1]


def keys(parm, values, step=False):
    parm.deleteAllKeyframes()
    for frame, value in values:
        key = hou.Keyframe(value)
        key.setFrame(frame)
        key.setExpression("constant()" if step else "linear()", hou.exprLanguage.Hscript)
        parm.setKeyframe(key)


def chapter(frame):
    if frame <= 12:
        return "Two houses, one tool", "Manarola and Riomaggiore presets"
    if frame <= 44:
        return "01 / Stack floors", "Change the height without rebuilding the facade"
    if frame <= 76:
        return "02 / Offset floors", "Supports follow the exposed corners"
    if frame <= 108:
        return "03 / Doors and shutters", "Open the shutters; switch between one and two door leaves"
    if frame <= 140:
        return "04 / Resize the facade kit", "Window dimensions, balcony depth, and railing spacing"
    if frame <= 164:
        return "05 / Roof details", "Switch roof style and change the chimney count"
    if frame <= 228:
        return "06 / Window flowers", "Close-up: turn the flower box on and change the flower count"
    return "Coastal Houses", "Two variations of the same procedural building asset"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("frames", type=Path)
    parser.add_argument("--setup-only", action="store_true", help="Save the animation without rendering frames")
    args = parser.parse_args()
    args.frames.mkdir(parents=True, exist_ok=True)
    hou.hipFile.load(str(ROOT / "coastal_houses.hipnc"), suppress_save_prompt=True)
    hou.setFps(25)
    hou.playbar.setFrameRange(1, 240)
    hou.playbar.setPlaybackRange(1, 240)
    a = hou.node("/obj/MANAROLA/building")
    tracks = {
        "floors": ([(1,4),(13,2),(21,3),(29,4),(37,5),(45,4),(240,4)], True),
        "offset_x": ([(1,0),(44,0),(45,-.50),(76,.65),(77,0),(240,0)], False),
        "offset_z": ([(1,.24),(44,.24),(45,-.40),(76,.60),(77,.24),(240,.24)], False),
        "offset_start": ([(1,2),(45,1),(77,2),(240,2)], True),
        "setback": ([(1,.12),(44,.12),(45,0),(76,0),(77,.12),(240,.12)], False),
        "window_open_angle": ([(1,155),(76,155),(77,0),(86,0),(108,170),(109,155),(240,155)], False),
        "door_double_door": ([(1,1),(96,0),(109,1),(240,1)], True),
        "window_width": ([(1,1.12),(108,1.12),(109,.80),(140,1.5),(141,1.12),(240,1.12)], False),
        "window_height": ([(1,1.7),(108,1.7),(109,1.3),(140,1.9),(141,1.7),(240,1.7)], False),
        "balcony_depth": ([(1,.82),(108,.82),(109,.45),(140,1.35),(141,.82),(240,.82)], False),
        "balcony_rail_spacing": ([(1,.16),(108,.16),(109,.10),(140,.30),(141,.16),(240,.16)], False),
        "roof_style": ([(1,1),(141,0),(153,1),(240,1)], True),
        "chimneys": ([(1,2),(141,0),(149,1),(157,3),(165,2),(240,2)], True),
        "window_flower_box": ([(1,1),(165,0),(173,1),(240,1)], True),
        "window_flower_count": ([(1,9),(165,3),(181,6),(197,9),(240,9)], True),
    }
    for name, (values, step) in tracks.items():
        keys(a.parm(name), values, step)

    camera = hou.node("/obj/presentation_camera")
    camera.parmTuple("res").set((960, 720))
    close_camera = hou.node("/obj/facade_camera")
    demo_camera = hou.node("/obj").copyItems((camera,))[0]
    demo_camera.setName("demo_camera")
    camera_parms = ["tx", "ty", "tz", "rx", "ry", "rz", "focal"]
    for name in camera_parms:
        wide = camera.evalParm(name)
        close = close_camera.evalParm(name)
        keys(demo_camera.parm(name), [(1,wide),(165,close),(229,wide),(240,wide)], True)
    preview_camera = hou.node("/obj/preview_camera")
    for name in camera_parms:
        preview_camera.parm(name).setExpression('ch("../demo_camera/' + name + '")')
    if sys.platform == "darwin":
        # H22's offscreen viewport reads one quadrant on this Retina display.
        preview_camera.parm("orthowidth").set(camera.evalParm("orthowidth") * 2)
        preview_camera.parm("aperture").set(camera.evalParm("aperture") * 2)
        preview_camera.parm("winx").set(.25)
        preview_camera.parm("winy").set(.25)
    rop = hou.node("/out/preview")
    hou.node("/out/beauty").parm("camera").set(demo_camera.path())
    rop.parm("camera").set(preview_camera.path())
    rop.parm("tres").set(0)
    rop.parm("picture").set(str(args.frames.resolve() / "demo.$F4.png"))
    rop.parm("aamode").set("aa4")
    rop.parm("hqlighting").set(1)
    rop.parm("shadowquality").set("point")
    rop.parm("ambocclusion").set(1)
    rop.parm("ambquality").set(1)

    manifest = []
    for frame in range(1, 241):
        hou.setFrame(frame)
        title, subtitle = chapter(frame)
        manifest.append({"frame": frame, "title": title, "subtitle": subtitle,
                         "parameters": {name: a.evalParm(name) for name in tracks}})
    (args.frames / "values.json").write_text(json.dumps(manifest, indent=2) + "\n")
    hou.setFrame(1)
    # The render output stays relative when the demo HIP is moved.
    rop.parm("picture").set("$HIP/render/demo.$F4.png")
    hou.hipFile.save(str(ROOT / "coastal_demo.hipnc"))
    if args.setup_only:
        print("Saved 240 frames at 25 fps (9.6 seconds)", flush=True)
        return
    rop.parm("picture").set(str(args.frames.resolve() / "demo.$F4.png"))
    print("Rendering 240 frames", flush=True)
    rop.render(frame_range=(1, 240))
    print("Done", flush=True)


if __name__ == "__main__":
    main()
