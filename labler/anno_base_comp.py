from datetime import datetime
from tqdm import tqdm
import json, random
import os
from Maker import Maker
from prompt import BODY_ANNO, ITEM_ANNO
from common.tools import grid_ims
from io import BytesIO
from config import FORMAL_NAMES
import hashlib
from labler.openai_func import encode_image, request_openai

def get_body_comp(pid=None):
    pid = '53713'
    root = os.path.join(r'D:\picrew\data', pid)
    maker = Maker(root)
    prompt = str.format(BODY_ANNO, input = ','.join([cp.cp_name for cp in maker.components]))
    anno = request_openai(prompt)
    print(anno)