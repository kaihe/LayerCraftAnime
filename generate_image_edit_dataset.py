from Maker import Maker
import os, random, json, copy
from data.image_edit_proposal.config import config, variations, fine_grained_change
from common.tools import grid_ims
from PIL import Image

def gen_edition(pid, instruction, seed=None, schedule=None):
    if schedule is not None:
        assert len(instruction) == len(schedule)

    # pid = '1423370'
    if seed:
        random.seed(seed)

    root = os.path.join(r'D:\picrew\data', pid)
    maker = Maker(root)
    comp_id_map = {
        str(c.cp_id):c for c in maker.components
    }
    card_info = config[pid]['annotation']

    # auto remove closed eye from eye
    eye_key, eye_value = list(card_info['eye'].items())[0]
    ceye_key, ceye_value = list(card_info['closed_eye'].items())[0]
    if eye_key == ceye_key and eye_value == 'Any' and isinstance(ceye_value, list) and len(card_info['eye'])==1 and len(card_info['closed_eye'])==1:
        _values = [item.it_id for item in comp_id_map[eye_key].items]
        _values = [it_id for it_id in _values if it_id not in ceye_value]
        card_info['eye'] = {eye_key:_values}

    def _sample_cp_item(cp_items):
        result = []
        for k, v in cp_items.items():
            if k == "":
                continue
            if isinstance(v, list):
                result.append((k, random.choice(v)))
            elif v=='Any':
                result.append((k, random.choice(comp_id_map[k].items).it_id))
        return result

    cards = [{}]
    for i, _var in enumerate(instruction):
        _card = copy.deepcopy(cards[-1])
        
        to_pop = _var.get('remove',[]) + _var.get('update_with_chance',[])

        for name in to_pop:
            for cp_id in card_info[name]:
                if not cp_id == "" and cp_id in _card:
                    _card.pop(cp_id)

        for name in _var.get('update',[]):
            cp_items = card_info[name]
            to_update = _sample_cp_item(cp_items)
            for k, v in to_update:
                _card[k] = [v]



        for name in _var.get('update_with_chance',[]):
            if random.random()<0.7:
                continue
            cp_items = card_info[name]
            to_update = _sample_cp_item(cp_items)
            for k, v in to_update:
                _card[k] = [v]

        # update based on scheduled item_ids
        if schedule:
           for cp_id, it_id in schedule[i].items():
               _card[cp_id] = [it_id] 

        cards.append(_card)

    ims = []
    for card in cards[1:]:
        combos = maker.gen_combo(list(card.items()), type='random')
        im = maker.render_combo(combos[0])
        ims.append(im)

    return ims


def figure_grid_board_edition():
    from PIL import Image
    dir = r'data\image_edit_proposal\general_editions'
    out = r'data\image_edit_proposal\latex_figures'
    selected = [648, 1315158, 11431, 32253, 16378, 29419, 36849, 1423370]

    grouped_images = [[] for _ in range(5)]

    for f in os.listdir(dir):
        pid = f.split('_')[0]
        if not int(pid) in selected:
            continue

        im = Image.open(os.path.join(dir, f))
        
        height = im.height/2
        width = im.width/3

        i = 0
        for r in range(2):
            for c in range(3):
                sub_im = im.crop([width*c, height*r, width*(c+1), height*(r+1)])
                # sub_im.show()
                # sub_im.save(os.path.join(out, f'{pid}_{i}.png'))
                grouped_images[i].append(sub_im)
                i +=1 
                if i == 5:
                    break

    for i, ims in enumerate(grouped_images):
        im = grid_ims(ims, 1)
        im_rgb = Image.new("RGB", im.size, (255, 255, 255))
        im_rgb.paste(im, mask=im.split()[3]) # 3 is the alpha channel
        im_rgb.save(os.path.join(out, f'board_{i}.jpeg'))

def to_rgba(im):
    im_rgb = Image.new("RGB", im.size, (255, 255, 255))
    im_rgb.paste(im, mask=im.split()[3]) # 3 is the alpha channel
    return im_rgb

def figure_gradually_edition():
    
    out = r'data\image_edit_proposal\latex_figures'
    gpt4_out = r'data\image_edit_proposal\gpt4_inputs'
    pid = '11428'
    seed = None
    comp_name = 'hand'

    fine_grained_change = [
        { # basic config
            'update':['bangs', 'back_hair', 'sideburns','basebody','eye','eyebrow','ear','mouth','inner_cloth','hand']
        }
    ]

    schedules = {
        "bangs": [{"25360": 828965}, {"25360": 828318}, {"25360": 2325644}, {"25360": 828272}],
        "back_hair": [{"25363": 2329363}, {"25363": 125620}, {"25363": 826760}, {"25363": 292696}],
        "eye": [{"25301": 105855}, {"25301": 108130}, {"25301": 112378}, {"25301": 107678}],
        "hand": [{"26936": 112226}, {"26936": 157057}, {"26936": 185296}, {"26936": 2312016}],
    }

    for _ in range(3):
        fine_grained_change.append({'update':[comp_name, 'mouth', 'eyebrow']})

    ims = gen_edition(pid, fine_grained_change, seed=seed, schedule=schedules.get(comp_name, None))

    for i, im in enumerate(ims):
        to_rgba(im).save(os.path.join(out, f'gradually_{comp_name}_{i}.jpeg'))

    to_rgba(grid_ims(ims, len(ims))).save(os.path.join(gpt4_out, f'{pid}',f'gradually_{comp_name}.jpeg'))

if __name__=='__main__':
    # seed = 4
    # instruction = variations
    # gen_edition(pid='1423370', instruction=instruction, seed=seed)

    figure_gradually_edition()