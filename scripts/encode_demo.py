"""Add the evaluated control values to the rendered demo and encode an MP4."""

import argparse
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg


def font(size):
    for path in ["/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def controls(frame, p):
    if 13 <= frame <= 44:
        return f"Floors: {p['floors']}    |    Floor height: 3.20    |    Front bays: 3"
    if 45 <= frame <= 76:
        return f"Offset X: {p['offset_x']:+.2f}    |    Offset Z: {p['offset_z']:+.2f}    |    Supports: on"
    if 77 <= frame <= 108:
        door = "double" if p["door_double_door"] else "single"
        return f"Shutter angle: {p['window_open_angle']:.0f} degrees    |    Door: {door}"
    if 109 <= frame <= 140:
        return (f"Window: {p['window_width']:.2f} x {p['window_height']:.2f}    |    "
                f"Balcony depth: {p['balcony_depth']:.2f}    |    Rails: {p['balcony_rail_spacing']:.2f}")
    if 141 <= frame <= 164:
        roof = "tiled" if p["roof_style"] else "terrace"
        return f"Roof: {roof}    |    Chimneys: {p['chimneys']}"
    if 165 <= frame <= 228:
        enabled = "on" if p["window_flower_box"] else "off"
        return f"Window flowers: {enabled}    |    Flower count: {p['window_flower_count']}"
    return "Left: Manarola, 4 floors    |    Right: Riomaggiore, 5 floors    |    Same HDA"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("frames", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.frames / "values.json").read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
           "-s", "960x864", "-pix_fmt", "rgb24", "-r", "25", "-i", "-", "-an",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(args.output)]
    encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    heading, small, label = font(23), font(15), font(18)
    try:
        for item in manifest:
            frame = item["frame"]
            render = Image.open(args.frames / f"demo.{frame:04d}.png").convert("RGB")
            assert render.size == (960, 720), render.size
            canvas = Image.new("RGB", (960, 864), "#182629")
            canvas.paste(render, (0, 72))
            draw = ImageDraw.Draw(canvas)
            draw.text((24, 11), item["title"], font=heading, fill="#f2ebdc")
            draw.text((24, 41), item["subtitle"], font=small, fill="#bbc7c5")
            draw.rectangle((0, 69, 959, 71), fill="#b97853")
            draw.text((24, 808), controls(frame, item["parameters"]), font=label, fill="#f2ebdc")
            draw.text((24, 838), "Parameter animation rendered from the Houdini asset", font=small, fill="#9db0ad")
            draw.rectangle((0, 861, int(959*frame/240), 863), fill="#b97853")
            encoder.stdin.write(canvas.tobytes())
    finally:
        encoder.stdin.close()
    if encoder.wait():
        raise RuntimeError("Video encoding failed")
    print(args.output)


if __name__ == "__main__":
    main()
