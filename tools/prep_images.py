"""Prepare case-study images in one go.

Run from anywhere:  python C:/Users/shanmugam/portfolio/tools/prep_images.py

For every file in images/work/<project>/ it:
  - fixes doubled extensions (name.png.png -> name.png)
  - converts PNG/JPEG to a compressed JPG (quality 86), shrinking anything wider than 1600 px
  - extends the canvas to 16:10 when the shape is off (fills with the image's corner colour, never crops)
  - checks the name matches a placeholder in index.html
and prints one short line per file, plus what is still missing.
"""
import os, re, sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing: run  python -m pip install --user pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "images", "work")
html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()


def expected(project):
    """File names the site asks for in this project's case study (without extension)."""
    i = html.find(f"  {project}:{{")
    if i < 0:
        return set()
    j = html.find("\n  }", i)
    nxt = re.search(r"\n  [a-z]+:\{", html[i + 5:])
    end = i + 5 + nxt.start() if nxt else len(html)
    return {os.path.splitext(n)[0] for n in re.findall(r'"([a-z0-9-]+\.png)"', html[i:end])}


for project in sorted(os.listdir(WORK)):
    folder = os.path.join(WORK, project)
    if not os.path.isdir(folder):
        continue
    want = expected(project)
    done = set()
    print(f"\n{project.upper()}")
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        base, ext = os.path.splitext(name)
        while os.path.splitext(base)[1].lower() in (".png", ".jpg", ".jpeg"):  # name.png.png
            base = os.path.splitext(base)[0]
        base = base.lower().strip().replace(" ", "-")
        ext = ext.lower()
        if ext == ".mp4":
            mb = os.path.getsize(path) / 1e6
            out = os.path.join(folder, base + ".mp4")
            if path != out:
                os.replace(path, out)
            done.add(base)
            print(f"  ok    {base}.mp4  ({mb:.1f} MB{', consider compressing' if mb > 8 else ''})")
            continue
        if ext not in (".png", ".jpg", ".jpeg", ".webp"):
            print(f"  skip  {name}  (not an image)")
            continue
        im = Image.open(path)
        w, h = im.size
        note = []
        if abs(w / h - 1.6) > 0.01:
            # extend the canvas (never crop): fill the new edges with the image's own corner colour
            fill = im.convert("RGB").getpixel((2, 2))
            nw, nh = (round(h * 1.6), h) if w / h < 1.6 else (w, round(w / 1.6))
            canvas = Image.new("RGB", (nw, nh), fill)
            canvas.paste(im.convert("RGB"), ((nw - w) // 2, (nh - h) // 2))
            im, (w, h) = canvas, canvas.size
            ext = ".changed"
        if w > 1600:
            im = im.resize((1600, round(1600 * h / w)), Image.LANCZOS)
        out = os.path.join(folder, base + ".jpg")
        already = ext in (".jpg", ".jpeg") and w <= 1600 and path == out
        if not already:
            im.convert("RGB").save(out, quality=86, optimize=True, progressive=True, subsampling=0)
            if os.path.abspath(path) != os.path.abspath(out):
                os.remove(path)
        if base not in want:
            note.append("name not used on the site, check spelling")
        done.add(base)
        kb = os.path.getsize(out) // 1024
        print(f"  {'warn' if note else 'ok  '}  {base}.jpg  {kb} KB" + ("  <- " + "; ".join(note) if note else ""))
    missing = sorted(want - done)
    print(f"  still missing ({len(missing)}): {', '.join(missing) if missing else 'none'}")
