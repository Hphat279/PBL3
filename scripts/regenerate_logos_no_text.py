from PIL import Image, ImageDraw
import os
BASE = os.path.dirname(__file__)
out_dir = os.path.join(BASE, '..', 'static', 'assets', 'img')
dash_dir = os.path.join(BASE, '..', 'static', 'dashboard', 'assets', 'img')

os.makedirs(out_dir, exist_ok=True)
os.makedirs(dash_dir, exist_ok=True)

# Colors
BG = (15, 98, 167)
CROSS = (33, 150, 243)
WHITE = (255,255,255)

def draw_cross(draw, x, y, size, color):
    w = size
    bw = max(4, w//3)
    draw.rectangle([x+bw, y, x+2*bw, y+w], fill=color)
    draw.rectangle([x, y+bw, x+w, y+2*bw], fill=color)

# 1) Regenerate login-banner.png (large banner) without text
w,h = 1024,768
img = Image.new('RGB', (w,h), WHITE)
d = ImageDraw.Draw(img)
# draw big cross on left
cs = int(min(w,h)*0.25)
draw_cross(d, 30, (h-cs)//2, cs, CROSS)
img.save(os.path.join(out_dir, 'login-banner.png'))

# 2) Regenerate small logo (logo-small.png) with only cross, transparent bg if PNG
w2,h2 = 40,40
img2 = Image.new('RGBA', (w2,h2), (0,0,0,0))
d2 = ImageDraw.Draw(img2)
cs2 = 28
draw_cross(d2, 6, (h2-cs2)//2, cs2, CROSS)
img2.convert('RGB').save(os.path.join(dash_dir, 'logo-small.png'))
img2.convert('RGB').save(os.path.join(out_dir, 'attachment-2.png'))

# Also overwrite static/assets/img/footer-logo.png with just cross
img3 = Image.new('RGB', (200,80), WHITE)
d3 = ImageDraw.Draw(img3)
cs3 = 48
draw_cross(d3, 10, (80-cs3)//2, cs3, CROSS)
img3.save(os.path.join(out_dir, 'footer-logo.png'))

print('Wrote:', os.path.join(out_dir, 'login-banner.png'), os.path.join(dash_dir, 'logo-small.png'))
