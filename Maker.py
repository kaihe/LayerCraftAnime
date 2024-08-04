import numpy as np
import itertools
from posixpath import basename
import random
from math import log
import re
import requests
from genericpath import exists
from tqdm import tqdm
from ast import copy_location
from collections import defaultdict
import os
import json
from dataclasses import dataclass
from sre_constants import IN
from typing import Dict, List
from common.tools import slugify
import logging
from PIL import Image, UnidentifiedImageError, ImageEnhance
import copy
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.CRITICAL, format='%(message)s')
logger = logging.getLogger('Maker')

def to_rgba(im_path):
    im = Image.open(im_path)
    if not im.mode == 'RGBA':
        im = im.convert('RGBA')
        
    return im

@dataclass
class ImageFile:
    url: str
    layer_id: int

"""
    item is a virtual concept, one item could be separated image files to be rendered on different layers
"""
@dataclass
class Item:
    it_id: int
    default_color_code: str
    all_image_files: Dict[str, List[ImageFile]]
    
    @property
    def image_files(self):
        # return item files of default color
        return self.all_image_files.get(self.default_color_code, [])


@dataclass
class Component:
    cp_id: int
    _cp_name: str
    items: List[Item]
    
    color_group_id: int
    default_color_code: str
    default_it: int
    layer_ids: list
    x: int
    y: int

    rp_x: int
    layer_l: int
    layer_r: int

    is_menu: int
    p_type: int

    def __post_init__(self):
        self._id_to_item = {
            item.it_id:item for item in self.items
        }

    @property
    def cp_name(self):
        folder = slugify(self._cp_name, allow_unicode=True)
        if folder == '':
            folder = str(self.cp_id)
        return folder
    
    def get_item_by_it(self, it_id):
        return self._id_to_item[it_id]

class Maker:
    def __init__(self, root) -> None:
        self.components = []
        self.width = None
        self.height = None
        self.base_url = None
        self.picrew_id = None
        self.root = None
        self.rules = [] # list of sets
        # front means lower rank means first to paint
        self.ordered_layers = [] # [(rank, lid, c)]
        self.comp_rank = defaultdict(list)
        self.lid_to_rank = {}
        self._build(root)
        # remove items without their file
        self._trim_items()

    def _trim_items(self):
        _components = []
        for c in self.components:
            _items = []
            for item in c.items:
                _im_files = []
                for im_file in item.image_files:
                    filename = im_file.url.split('/')[-1]
                    im_path = os.path.join(self.root, c.cp_name, filename)
                    if os.path.isfile(im_path):
                        _im_files.append(im_file)
                if len(_im_files)>0:
                    _items.append(
                        Item(item.it_id, item.default_color_code, item.all_image_files)
                    )
            if len(_items)>0:
                new_comp = copy.deepcopy(c)
                new_comp.items = _items
                _components.append(new_comp)
        self.components = _components                

    def set_verbose(self, show_verbos):
        if show_verbos:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.CRITICAL)

    def _build(self, root):
        json_path = os.path.join(root, 'cf.json')
        img_path = os.path.join(root, 'img.json')

        cf = json.load(open(json_path))
        img = json.load(open(img_path))

        self.base_url = img['baseUrl']
        self.picrew_id = os.path.basename(root)
        self.root = root

        it_id_data = img['lst']
        self.width = cf['w']
        self.height = cf['h']

        # check empty
        if any(len(cf[k])==0 for k in ['lyrList', 'pList']) or len(it_id_data)==0:
            logger.info(f'empty card: {self.root}')
            return

        color_groups = {}
        for color_group_id, color_list in cf['cpList'].items():
            color_code_map = {e['cId']:e['cd'] for e in color_list}
            color_groups[str(color_group_id)] = color_code_map

        # read component default color
        cp_default_color = dict() # int -> int 
        for cp_id, data in cf['zeroConf'].items():
            cp_default_color[int(cp_id)] = data['cId']

        for com in cf['pList']:
            cp_id = int(com['pId'])
            cp_name = com['pNm']
            layer_ids = com['lyrs']

            color_group_id = com['cpId']
            default_it = int(com['defItmId'])
            default_color = str(cp_default_color[cp_id])

            x = int(com['x'])
            y = int(com['y'])

            rp_x = com.get('rpX', -1)
            layer_l = com.get('lyrL', -1)
            layer_r = com.get('lyrR', -1)
            
            is_menu = com['isMenu']
            p_type = com['pType']

            items = []
            for item in com['items']:
                _all_image_files = defaultdict(list)
                it_id = item['itmId']
                
                img_data = it_id_data.get(str(it_id), {})
                
                # build Item object and corresponding ImageFile objects
                # image_files = []
                for layer_id, color_data in img_data.items():
                    for _color, data in color_data.items():
                        url = data['url']
                        _all_image_files[_color].append(ImageFile(url, int(layer_id)))
                    
                items.append(
                    Item(int(it_id), default_color, _all_image_files)
                )

            self.components.append(
                Component(cp_id, cp_name, items, color_group_id, default_color, default_it, layer_ids, x, y, rp_x, layer_l, layer_r, is_menu, p_type)
            )
    
        rule_list = cf['ruleList']
        for data in rule_list.values():
            cp_ids = data['list']
            self.rules.append(set(cp_ids))

        # lower value means first to paint, means background
        paint_order = {int(k):v for k, v in cf['lyrList'].items()} # int-> int
        _layer = defaultdict(list)
        for comp in self.components:
            for lid in comp.layer_ids:
                _layer[lid].append(comp)
        
        _layer = [(paint_order[lid], lid, _layer[lid]) for lid in _layer.keys()]
        _layer = sorted(_layer, key=lambda k:k[0])
        for _, lid, comps in _layer:
            assert len(comps)<=1, f'more than 1 comp in one layer {self.picrew_id}, lid: {lid}'
            

        self.ordered_layers = [(rank, lid, comps[0]) for rank, lid, comps in _layer]

        for _rank, _lid, comp in self.ordered_layers:
            # one comp could exist in multiple layers
            self.comp_rank[comp.cp_id].append(_rank)
            self.lid_to_rank[_lid] = _rank

    def get_rank(self, cp_ids, type='highest'):
        
        # higher rank mean on top
        if type == 'highest':
            func = max 
        elif type == 'lowest':
            func = min
        comp_ranks = [self.comp_rank[int(_cp_id)] for _cp_id in cp_ids]
        ranks = list(itertools.chain(*comp_ranks))
        rank = func(ranks)
        
        return rank

    def show_paint_order(self, anno={}):
        for rank, lid, c in self.ordered_layers:
            label = anno.get(c.cp_name, '')
            
            print(f'{rank :<10d}{lid :<15d}{c.cp_id :<15d}{c.cp_name}--->{label}')

    def download_images(self):       

        dl_info = []
        for comp in self.components:
            for item in comp.items:
                for im_file in item.image_files:
                    url = self.base_url+im_file.url
                    filename = im_file.url.split('/')[-1]
                    dl_info.append((comp.cp_name, filename, url))

        
        existings = set()
        for root, _, files in os.walk(self.root):
            for f in files:
                existings.add(f)

        dl_info = [r for r in dl_info if r[1] not in existings]
        
        # return
        for folder, file_name, url in tqdm(dl_info, desc=f' {self.root} '):
            dir = os.path.join(self.root, folder)
            os.makedirs(dir, exist_ok=True)

            try:
                r = requests.get(url, verify=False, timeout = 3)
                with open(os.path.join(dir, file_name), 'wb') as f:
                    f.write(r.content)
                r.close()
            except Exception as e:
                logger.info(e)


    def _is_combo_legal(self, combo):
        cp_ids = set([cp_id for cp_id, _ in combo])

        if all(len(rule.intersection(cp_ids))<2 for rule in self.rules):
            return True
        else:
            return False

    def _trim_combo(self, combo):
        cp_ids = set([cp_id for cp_id, _ in combo])
        for rule in self.rules:
            broken_ids = rule.intersection(cp_ids)
            if len(broken_ids)>1:
                to_del = random.sample(broken_ids, len(broken_ids)-1)
                combo = [(cp_id, it_id) for cp_id, it_id in combo if cp_id not in to_del]
                return combo

        # nothing change
        assert True, 'trim on good combo'
        return combo

    def gen_combo(self, comp_ids, type):
        '''
            comp_ids data types: 
                1. list of int ---> choose from original component items
                2. lisf of tuple (int, list) ---> choose item from the given value list
            type values:
                1. "random": random choose from each of then
                2. "linear": make sure at least each item is chosen once
                3. "cartesian": cartesian product of items, could be very big, truncate at 200
                4. "single_item": each item in each comp as a combo
            
            return: list of tuple (cp_id, it_id)
        '''
        assert type in ('random','linear','cartesian', 'single_item')
        if len(comp_ids) == 0:
            return []
        
        if isinstance(comp_ids[0], int):
            selected_comp = [c for c in self.components if c.cp_id in comp_ids and len(c.items)>0]
            candidates = [ (c.cp_id, [item.it_id for item in c.items]) for c in selected_comp ]
        else:
            candidates = comp_ids

        if type == 'random':
            combo = [(cp_id,random.choice(item_ids)) for (cp_id, item_ids) in candidates]
            combos = [combo]
        elif type == 'linear':
            _N = max([len(it_ids) for _, it_ids in candidates])

            combos = [] 
            for i in range(_N):
                combo = []
                for cp_id, item_ids in candidates:
                    _selected = i if i<len(item_ids) else random.randint(0, len(item_ids)-1)
                    combo.append((cp_id, item_ids[_selected]))
                combos.append(combo)
        elif type == "single_item":
            combos = [] 
            for cp_id, it_ids in candidates:
                _combos = [[(cp_id, it_id)] for it_id in it_ids]
                if len(_combos)>0:
                    combos.extend(_combos)
        elif type == 'cartesian':
            
            pool = []
            for cp_id, it_ids in candidates:
                pool.append([(cp_id, it_id) for it_id in it_ids])
            combos = itertools.product(*pool)
            combos = list(combos)
            if len(combos)>200:
                combos = random.sample(combos, 200)
                pass
        else:
            raise ValueError(f'unsupport {type}')


        # correct combo to follow the rules
        for i, combo in enumerate(combos):
            k = 0
            while not self._is_combo_legal(combo):
                combo = self._trim_combo(combo)
                k+=1
                assert k<100, 'max trim operations'
            combos[i] = combo
        
        return combos

    def render_combo(self, combo, diminish=[]):
        """
        combo: list of tuple (cp_id, it_id)
        diminish: list of cp_ids to make them transparent
        return: Image
        """
        groupby_cp_id = defaultdict(set)
        for cp_id, it_id in combo:
            cp_id = int(cp_id)
            groupby_cp_id[cp_id].add(it_id)

        canvas = Image.new('RGBA', (self.width, self.height))
        sucess = False
        for _, lid, c in self.ordered_layers:
            if not c.cp_id in groupby_cp_id:
                continue
            
            if c.p_type == 3:
                continue

            _it_ids = groupby_cp_id[c.cp_id]

            if c.cp_id in diminish:
                alpha_factor = 0.3
            else:
                alpha_factor = 1

            for _it_id in _it_ids:
                item = c.get_item_by_it(_it_id)

                offset = (c.x, c.y)
                if c.layer_r == lid:
                    offset = (c.rp_x, c.y)

                for im_file in item.image_files:
                    if im_file.layer_id == lid:
                        filename = im_file.url.split('/')[-1]
                        im_path = os.path.join(self.root, c.cp_name, filename)
                        if os.path.isfile(im_path):
                            item_im = to_rgba(im_path)
                            
                            #modify alpha channel
                            A = item_im.getchannel('A')
                            newA = A.point(lambda i: alpha_factor*i)
                            item_im.putalpha(newA)

                            #to reduce brightness by 50%, use factor 0.5
                            # enhancer = ImageEnhance.Brightness(item_im)
                            # item_im = enhancer.enhance(alpha_factor)

                            if not item_im.width == self.width or not item_im.height == self.height:
                                _item_im = Image.new('RGBA', (self.width, self.height))
                                _item_im.paste(item_im,  offset)
                                item_im = _item_im
                            canvas = Image.alpha_composite(canvas, item_im)
                            sucess = True
                        else:
                            logger.warning(f'missing file {im_file}')
        if sucess:                    
            return canvas
        else:
            return None



