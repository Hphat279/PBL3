from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'img')
os.makedirs(OUT_DIR, exist_ok=True)

# Colors
BG = (15, 98, 167)  # blue background similar to original
CROSS = (33, 150, 243)
TEXT = (33, 150, 243)
WHITE = (255,255,255)

# Helper to draw a medical cross
def draw_cross(draw, x, y, size, color):
    w = size
    bw = w//3
    # center rect
    draw.rectangle([x+bw, y, x+2*bw, y+w], fill=color)
    draw.rectangle([x, y+bw, x+w, y+2*bw], fill=color)

# First image (wide header) - 485x139
w,h = 485,139
img = Image.new('RGB', (w,h), BG)
d = ImageDraw.Draw(img)
# draw cross at left
cross_size = 60
draw_cross(d, 40, (h-cross_size)//2, cross_size, CROSS)
# text PBL3
try:
    font = ImageFont.truetype('arial.ttf', 48)
except:
    font = ImageFont.load_default()
text = 'PBL3'
try:
    bbox = d.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
except AttributeError:
    tw, th = font.getsize(text)
d.text((120, (h-th)//2), text, font=font, fill=TEXT)
img.save(os.path.join(OUT_DIR, 'attachment-1.png'))

# Second image (small logo) - 143x41
w2,h2 = 143,41
img2 = Image.new('RGB', (w2,h2), (255,255,255))
d2 = ImageDraw.Draw(img2)
draw_cross(d2, 6, (h2-24)//2, 24, CROSS)
try:
    font2 = ImageFont.truetype('arial.ttf', 20)
except:
    font2 = ImageFont.load_default()
text2 = 'PBL3'
try:
    bbox2 = d2.textbbox((0,0), text2, font=font2)
    th2 = bbox2[3]-bbox2[1]
except AttributeError:
    _, th2 = font2.getsize(text2)
d2.text((40, (h2-th2)//2), text2, font=font2, fill=CROSS)
img2.save(os.path.join(OUT_DIR, 'attachment-2.png'))

print('Generated:', os.path.join(OUT_DIR, 'attachment-1.png'), os.path.join(OUT_DIR, 'attachment-2.png'))
