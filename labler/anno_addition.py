from datetime import datetime
from tqdm import tqdm
import json, random
import os
from Maker import Maker
from prompts import make_addition_message
from common.tools import grid_ims,to_rgb
from config import FORMAL_NAMES
import hashlib
from labler.openai_func import encode_image, fetch_batch_result,do_batching, request_dir, result_dir,request_openai_json
from pydantic import BaseModel
import base64
from PIL import Image,ImageDraw, ImageFont
import io
import textwrap

item_annos = json.load(open(r'D:\valuable_anno_data\picrew\item_anno.json'))
comp_anno = json.load(open(r'D:\valuable_anno_data\picrew\anno.json'))

def gen_comp_im(pid, pool):
    if pool is None:
        pool = ['cloth', 'eye', 'front', 'dec', 'mouth','back', 'eyebrow','ear']

    # pid = '1116402'
    root = os.path.join(r'D:\picrew\data', pid)
    base_dict = item_annos[pid]['base']
    
    def sample_comp():
        # calculate weight by how many items in one component
        weights = []
        for _cp_name in pool:
            cp_dict = item_annos[pid].get(_cp_name, {})
            w = 0
            for cp_id, item_ids in cp_dict.items():
                w += len(item_ids)
            weights.append(w)

        # sample components by weight
        _cp_name = random.choices(pool, weights=weights, k=1)[0]
        return _cp_name

    while True:
        # get a valid component
        _cp_name = sample_comp()
        target_cp = item_annos[pid].get(_cp_name, [])

        if len(target_cp) > 0:
            break

    maker = Maker(root)
    for k,v in item_annos[pid].items(): 
        if k in pool:
            for cp_id, it_ids in v.items():
                if not cp_id in target_cp:
                    base_dict[int(cp_id)] = it_ids
    
    _target_cp = [(int(k),v) for k, v in target_cp.items()]
    target_combo = maker.gen_combo(_target_cp, type="random")[0]
    im_item = maker.render_combo(target_combo)

    base_combo = [(int(k), random.choice(v)) for k, v in base_dict.items()]
    base_combo.extend(target_combo)
    to_diminish = [t[0] for t in base_combo if not str(t[0]) in target_cp]
    im_all = maker.render_combo(base_combo, to_diminish)

    ims = [im_item, im_all]
    im_grid = grid_ims(ims, cols=len(ims), to_rgb=True)
    im_grid = im_grid.resize((512*len(ims), 512))

    im_all = to_rgb(im_all).resize((512,512))
    im_item = to_rgb(im_item).resize((512,512))
    # im.show()
    
    data = {
        'pid':pid,
        'component': FORMAL_NAMES[_cp_name],
        'cp_combo': target_combo,
        'all_combo': base_combo,
        'im_all': encode_image(im_all),
        'im_item': encode_image(im_item),
        'im_grid': encode_image(im_grid),
        'task_type': 'item addition'
    }
    return data


class Instruction(BaseModel):
    Instruction: str


def gpt_describe(pid, pool=None, show=False):
    data = gen_comp_im(pid, pool)
    messages = make_addition_message(data['component'], data['im_item'], data['im_all'])
    ans = request_openai_json(messages=messages)
    data['description'] = ans
    if show:
        im_grid_base64 = data['im_grid']
        image_data = base64.b64decode(im_grid_base64)
        # Convert the binary data to a file-like object
        image_file = io.BytesIO(image_data)
        # Open the file-like object with PIL to get the image
        image = Image.open(image_file)

        font = ImageFont.load_default()
        draw = ImageDraw.Draw(image)

        lines = ans.split('\n')
        text_to_draw = []
        chunk_size = 70
        for line in lines:
            chunks = textwrap.wrap(line, width=chunk_size)
            text_to_draw.extend(chunks)
                

        draw.text((50, 50), text='\n'.join(text_to_draw), font=font, fill=(255, 0, 0))
        print(ans)
        image.show()
    return data



def worker():
    comp_anno_file = r'D:\valuable_anno_data\picrew\anno.json'
    comp_anno = json.load(open(comp_anno_file))
    out_dir = r'data\gpt4o_component_description'
    today = datetime.today().strftime('%Y%m%d')

    N = 10
    pids = list(comp_anno.keys())
    for _ in tqdm(range(N)):
        pid = random.choice(pids)
        data = gpt_describe(pid)
        if data is None:
            continue

        with open(os.path.join(out_dir, f'{today}.jsonl'), 'a') as fout:
            fout.write(json.dumps(data, ensure_ascii=False)+'\n')

def worker_batch(N = 500):
    today = datetime.today().strftime('%Y%m%d')
    pids = list(comp_anno.keys())

    requests = []
    tasks = []
    name = ''
    for i in tqdm(range(N)):
        pid = random.choice(pids)
        data = gen_comp_im(pid)
        if data is None:
            continue

        task_name = hashlib.md5(data['im_grid'].encode('utf-8')).hexdigest()
        messages = make_addition_message(data['component'], data['im_item'], data['im_all'])
        _request = request_openai_json(prompt='', messages=messages, image_input='', batch=True, custom_id=task_name)

        data['task_id'] = task_name
        data.pop('im_item')
        data.pop('im_all')
        data.pop('im_grid')
        requests.append(_request)
        tasks.append(data)       

        name += task_name

    print(f'creating {len(tasks)} annotation jobs')

    name = hashlib.md5(name.encode('utf-8')).hexdigest()[-4:]
    with open(os.path.join(request_dir, f'{today}_{name}.jsonl'), 'w+') as fout:
        for _request in requests:
            fout.write(json.dumps(_request, ensure_ascii=False)+'\n')

    with open(os.path.join(request_dir, f'{today}_{name}_task.jsonl'), 'w+') as fout:
        data = {}
        for task in tasks:
            data[task['task_id']] = task
        fout.write(json.dumps(data, ensure_ascii=False)+'\n')

    do_batching(os.path.join(request_dir, f'{today}_{name}.jsonl'))

if __name__ == '__main__':
    # worker_batch(N=10)
    # fetch_batch_result('20240901_f3e6.jsonl')

    data = gpt_describe('100315', pool=['front'], show=True)
    # print(data['description'])

    