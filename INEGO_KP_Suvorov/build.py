from base64 import b64encode
from io import BytesIO
import json
from pathlib import Path
import subprocess

from PIL import Image

root = Path(__file__).resolve().parent
work = root / "source"
build = root / "build"
build.mkdir(exist_ok=True)
deliverable = build / "KP_INEGO_Suvorov.html"
font_dir = work / "fonts"
faces = [
    ("Inter", 400, "Inter-Regular"),
    ("Inter", 500, "Inter-Medium"),
    ("Inter", 600, "Inter-SemiBold"),
    ("Inter Display", 600, "InterDisplay-SemiBold"),
    ("Inter Display", 700, "InterDisplay-Bold"),
]
license_text = (font_dir / "LICENSE.txt").read_text(encoding="utf-8")
rules = ["/*\n" + license_text + "\n*/"]
for family, weight, file in faces:
    buffer = b64encode((font_dir / f"{file}.woff2").read_bytes()).decode("ascii")
    rules.append(f'@font-face {{ font-family: "{family}"; font-weight: {weight}; font-style: normal; '
                 f'font-display: swap; src: url(data:font/woff2;base64,{buffer}) format("woff2"); }}')

slots = {
    "WEB:core": "p7-0",
    "WEB:filter": "p7-2",
    "WEB:scene": "p7-0",
    "WEB:render": "p7-0",
    "WEB:facade": "p7-1",
    "UE5:core": "p3-0",
    "UE5:filter": "p3-0",
    "UE5:cityFilter": "p3-1",
    "UE5:cityMap": "p8-0",
    "UE5:cityMap:styled": "p8-0",
    "UE5:cityMap:satellite": "p3-1",
    "UE5:facades": "p3-2",
    "UE5:masterplan": "p3-4",
    "UE5:maf": "p3-4",
    "UE5:overview": "p3-1",
    "UE5:surround": "p3-1",
    "UE5:light": "p3-2",
    "UE5:interiors": "p5-1",
    "UE5:interiors:project": "p5-1",
    "UE5:interiors:reference": "p7-3",
    "UE5:interiors:inego": "p3-3",
    "UE5:interiors:whiteBox": "white-box",
    "UE5:commonAreas": "p3-3",
    "UE5:commonAreas:project": "p5-4",
    "UE5:commonAreas:reference": "p3-3",
    "UE5:commonAreas:whiteBox": "common-areas-white-box",
    "UE5:parking": "p5-2",
    "UE5:parking:inego": "p5-2",
}
image_paths = {
    "white-box": work / "reference-visuals" / "white-box.png",
    "common-areas-white-box": work / "reference-visuals" / "common-areas-white-box.png",
}
captions = {
    "white-box": "Иллюстрация отделки White box",
    "common-areas-white-box": "Иллюстрация МОП в отделке White box",
}
images = {}
for name in sorted(set(slots.values())):
    with Image.open(image_paths.get(name, work / "reference-visuals" / f"{name}.jpg")) as picture:
        picture.thumbnail((960, 640), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        picture.save(buffer, "WEBP", quality=80, method=6)
    images[name] = "data:image/webp;base64," + b64encode(buffer.getvalue()).decode("ascii")

document = (work / "calculator.html").read_text(encoding="utf-8")
document = document.replace("/* EMBEDDED_FONTS */", "\n".join(rules))
document = document.replace(
    "/* EMBEDDED_VISUALS */ {}",
    json.dumps({"images": images, "slots": slots, "captions": captions}, separators=(",", ":")),
)
offer_file = work / "offer.json"
editor_seed = json.loads(offer_file.read_text(encoding="utf-8"))["state"]
seed_json = json.dumps(editor_seed, separators=(",", ":")).replace("<", "\\u003c")
app_start = '<script id="app-script">'
if app_start not in document:
    raise ValueError("Missing app script")
document = document.replace(app_start, '<script>globalThis.inegoEditorSeed = ' + seed_json + ';</script>\n' + app_start, 1)
deliverable.write_text(document, encoding="utf-8")
subprocess.run(["node", str(root / "build_exports.cjs"), str(deliverable), str(offer_file)], check=True)
