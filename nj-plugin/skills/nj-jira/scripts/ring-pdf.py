"""Ring + crop a PDF sentence as evidence. Needs poppler (pdftoppm) + Pillow.
usage: ring-pdf.py in.pdf PAGE X0 Y0 X1 Y1 out.png [CROP_Y0 CROP_Y1]
Coordinates are PDF points (72/in) on the page; render is 150 dpi; crop rows default to ring +-25pt."""
import subprocess, sys, tempfile, os
from PIL import Image, ImageDraw
pdf, page, x0, y0, x1, y1, out = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7]), sys.argv[7]
c0, c1 = (float(sys.argv[8]), float(sys.argv[9])) if len(sys.argv) > 9 else (y0 - 25, y1 + 25)
k = 150 / 72
with tempfile.TemporaryDirectory() as d:
    subprocess.run(['pdftoppm', '-r', '150', '-png', '-f', page, '-l', page, '-singlefile', pdf, os.path.join(d, 'p')], check=True)
    im = Image.open(os.path.join(d, 'p.png')).convert('RGB')
dr = ImageDraw.Draw(im)
for i in range(4): dr.rounded_rectangle((x0*k-i, y0*k-i, x1*k+i, y1*k+i), radius=6, outline=(225, 29, 72))
im.crop((0, max(0, int(c0*k)), im.width, min(im.height, int(c1*k)))).save(out)
