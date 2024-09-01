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
from labler.openai_func import encode_image, fetch_batch_result,do_batching, request_dir, result_dir,request_openai_json
from pydantic import BaseModel


item_annos = json.load(open(r'D:\valuable_anno_data\picrew\item_anno.json'))
comp_anno = json.load(open(r'D:\valuable_anno_data\picrew\anno.json'))

def gen_edit_sample(pid=None, aspect=None):
    # pid = '1116402'
    root = os.path.join(r'D:\picrew\data', pid)
    base_dict = item_annos[pid]['base']
    
    pool = {
        'cloth': ['cloth'],
        'facial': ['eye',  'mouth', 'eyebrow', 'ear'],
        'hair': ['front', 'dec', 'back']
    }
    # pool = ['front']
    _cp_name = random.choice(pool)
    target_cp = item_annos[pid].get(_cp_name, [])

    if len(target_cp) == 0:
        return None
    
    maker = Maker(root)
    for k,v in item_annos[pid].items(): 
        if k in ('eye','mouth','eyebrow','front','back', 'cloth'):
            for cp_id, it_ids in v.items():
                if not cp_id in target_cp:
                    base_dict[int(cp_id)] = it_ids
    
    _target_cp = [(int(k),v) for k, v in target_cp.items()]
    target_combo = maker.gen_combo(_target_cp, type="random")[0]
    im_item = maker.render_combo(target_combo)

    base_combo = [(int(k), random.choice(v)) for k, v in base_dict.items()]
    base_combo.extend(target_combo)
    to_diminish = [t[0] for t in base_combo if not str(t[0]) in target_cp]
    im_base_item = maker.render_combo(base_combo, to_diminish)

    ims = [im_item, im_base_item]
    im = grid_ims(ims, cols=len(ims), to_rgb=True)

    im = im.resize((256*len(ims), 256))
    # im.show()
    
    data = {
        'pid':pid,
        'component': FORMAL_NAMES[_cp_name],
        'cp_combo': target_combo,
        'all_combo': base_combo,
        'im_str': encode_image(im)
    }
    return data

class Keypoint(BaseModel):
    aspect: str
    detail: str

class Instructions(BaseModel):
    instructions: list[Keypoint]


def gpt_describe(pid):
    data = gen_comp_im(pid)
    prompt = ITEM_ANNO.format(cp_name = data['component'])
    ans = request_openai_json(prompt, ans_format=Instructions, image_input=data['im_str'])
    data['description'] = ans
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

        prompt = ITEM_ANNO.format(cp_name = data['component'])
        task_name = hashlib.md5(data['im_str'].encode('utf-8')).hexdigest()

        _request = request_openai_json(prompt, ans_format=Instructions, image_input=data['im_str'], batch=True, task_id=task_name)
        data['task_id'] = task_name

        data.pop('im_str')
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
    # fetch_batch_result(r'data\gpt4o_component_description_batch_request\20240804_3787.jsonl')

    data = gpt_describe('241678')
    print(data['description'])

    