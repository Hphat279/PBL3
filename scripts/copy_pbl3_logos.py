import shutil, os
BASE = os.path.dirname(__file__)
src1 = os.path.join(BASE, '..', 'static', 'assets', 'img', 'attachment-1.png')
src2 = os.path.join(BASE, '..', 'static', 'assets', 'img', 'attachment-2.png')

targets = [
    os.path.join(BASE, '..', 'static', 'dashboard', 'assets', 'img', 'logo.png'),
    os.path.join(BASE, '..', 'static', 'dashboard', 'assets', 'img', 'logo-small.png'),
    os.path.join(BASE, '..', 'static', 'assets', 'img', 'footer-logo.png'),
]

# copy header to logo.png and footer
shutil.copyfile(src1, targets[0])
# copy small to logo-small and footer-thumb
shutil.copyfile(src2, targets[1])
shutil.copyfile(src2, targets[2])
print('Copied to:', targets)
