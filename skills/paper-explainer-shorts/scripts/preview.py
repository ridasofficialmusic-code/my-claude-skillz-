"""QA contact sheet: renders one still per voice line (mid-line) plus the thumbnails.
Usage: python3 preview.py script.json WORK_DIR  -> WORK_DIR/preview_sheet.png (needs WORK_DIR/timing.json from tts.py)
"""
import json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render

spec_path, work = sys.argv[1], sys.argv[2]
spec = json.load(open(spec_path)); timing = json.load(open(os.path.join(work, "timing.json")))
tl = render.Timeline(spec, timing)
times = [0.0] + [round((l["start"] + l["end"]) / 2, 2) for l in timing["lines"]] + [spec.get("duration", 60.0) - 0.5]
tw, th, cols = 216, 384, 8; rows = -(-len(times) // cols)
sheet = Image.new("RGB", (tw * cols, (th + 0) * rows), "white")
for i, t in enumerate(times):
    sheet.paste(render.frame(tl, t).resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
sheet.save(os.path.join(work, "preview_sheet.png"))
render.render_thumbs(spec_path, work)
print("times:", times)
