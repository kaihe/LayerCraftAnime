from datetime import datetime
from tqdm import tqdm
import json, random
import os
from Maker import Maker
from prompt import ITEM_ADDITION, ITEM_ADDITION_PART1, ITEM_ADDITION_PART2
from common.tools import grid_ims,to_rgb
from config import FORMAL_NAMES
import hashlib
from labler.openai_func import encode_image, fetch_batch_result,do_batching, request_dir, result_dir,request_openai_json
from pydantic import BaseModel
import base64
from PIL import Image
import io


item_annos = json.load(open(r'D:\valuable_anno_data\picrew\item_anno.json'))
comp_anno = json.load(open(r'D:\valuable_anno_data\picrew\anno.json'))

def gen_comp_im(pid=None):
    # pid = '1116402'
    root = os.path.join(r'D:\picrew\data', pid)
    base_dict = item_annos[pid]['base']

    pool = ['cloth', 'eye', 'front', 'dec', 'mouth','back', 'eyebrow','ear']
    # pool = ['front']
    _cp_name = random.choice(pool)
    target_cp = item_annos[pid].get(_cp_name, [])

    if len(target_cp) == 0:
        return None
    
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


def gpt_describe(pid, show=False):
    data = gen_comp_im(pid)
    prompt = ITEM_ADDITION.format(cp_name = data['component'])
    ans = request_openai_json(prompt, ans_format=Instructions, image_input=data['im_grid'])
    data['description'] = ans
    if show:
        im_grid_base64 = data['im_grid']
        image_data = base64.b64decode(im_grid_base64)
        # Convert the binary data to a file-like object
        image_file = io.BytesIO(image_data)
        # Open the file-like object with PIL to get the image
        image = Image.open(image_file)
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
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": [
                {"type": "text", "text": ITEM_ADDITION_PART1.format(cp_name = data['component'])},
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/png;base64,{data['im_item']}",
                        "detail": "low"
                    }
                },
                {"type": "text", "text": ITEM_ADDITION_PART2.format(cp_name = data['component'])},
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/png;base64,{data['im_all']}",
                        "detail": "low"
                    }
                }
            ]}
        ]

        _request = request_openai_json(prompt='', messages=messages, ans_format=Instruction, image_input='', batch=True, custom_id=task_name)

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
    fetch_batch_result('20240901_f3e6.jsonl')

    # data = gpt_describe('241678', show=True)
    # print(data['description'])

    