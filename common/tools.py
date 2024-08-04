import cv2
import shutil
import os
import re
import unicodedata
from tqdm import tqdm
from PIL import Image
from collections import defaultdict
import numpy as np
import math
def is_blank(im):
    alpha = np.array(im.split()[-1]) 
    coords = cv2.findNonZero(alpha)
    x, y, w, h = cv2.boundingRect(coords)

    if w==0 or h==0:
        return True
    else:
        return False

def stack_images(ims):
    canvas = Image.new('RGBA', ims[0].size)
    for im in ims:
        canvas = Image.alpha_composite(canvas, im)
    return canvas

def grid_ims(ims, cols, to_rgb=False):
    nrows = math.ceil(len(ims)/cols)
    w, h = ims[0].size
    canvas = Image.new(ims[0].mode, (w*cols, h*nrows))
    for i, _im in enumerate(ims):
        canvas.paste(_im, box=(i%cols*w, i//cols*h))
    if to_rgb:
        _img = Image.new('RGB', (canvas.width, canvas.height), (255, 255, 255))
        _img.paste(canvas, (0,0), mask=canvas.split()[3])
        canvas = _img

    return canvas

def _group_file(cp_root):
    pid_grouped = defaultdict(list)
    for f in os.listdir(cp_root):
        pid = f.split('_')[0]
        pid_grouped[pid].append(os.path.join(cp_root, f))
    return pid_grouped

def limited_cv2_show(np_im, max_height=1000):
    if np_im.shape[0]>max_height:
        new_height = max_height
        new_width = int(np_im.shape[1]*max_height/np_im.shape[0])
        np_im = cv2.resize(np_im, (new_width, new_height), interpolation = cv2.INTER_AREA)
    cv2.imshow('im', np_im)
    cv2.waitKey(0)

def clear_folder(folder):
    for f in tqdm(os.listdir(folder), 'deleting'):
        f = os.path.join(folder,f)
        if os.path.isdir(f):
            shutil.rmtree(f)
        elif os.path.isfile(f):
            os.remove(f)

def slugify(value, allow_unicode=False):
    
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

if __name__=='__main__':
    s = '←눈'
    s = "shirt :)"
    print(slugify(s, allow_unicode=True))
    # os.makedirs(os.path.join('out\picrew',s))

    