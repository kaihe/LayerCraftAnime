from datetime import datetime
from tqdm import tqdm
import json, random
import os
from Maker import Maker
from prompt import ITEM_ANNO_PART1, ITEM_ANNO_PART2, ITEM_ANNO
from common.tools import grid_ims, to_rgb, crop_to_non_white
import hashlib
from labler.openai_func import encode_image, fetch_batch_result,do_batching, request_dir, result_dir,request_openai_json
from pydantic import BaseModel
import enum

item_annos = json.load(open(r'D:\valuable_anno_data\picrew\item_anno.json'))
comp_anno = json.load(open(r'D:\valuable_anno_data\picrew\anno.json'))

def gen_item_anno_samples(pid, cp_name=None):
    root = os.path.join(r'D:\picrew\data', pid)
    base_comps = []

    maker = Maker(root)
    for name, cp_dict in item_annos[pid].items(): 
        for cp_id, it_ids in cp_dict.items():
            base_comps.append((int(cp_id), it_ids))
    
    known_comps = [v[0] for v in base_comps]
    # known_comps = []

    if cp_name is None:
        unknown_comps = [cp for cp in maker.components if not cp.cp_id in known_comps]
    else:
        unknown_comps = [cp for cp in maker.components if cp.cp_name==cp_name]

    for comp in unknown_comps:
        for item in comp.items:
            target_combo = [(comp.cp_id, item.it_id)]
            im_item = maker.render_combo(target_combo)

            _combo = maker.gen_combo(base_comps, type='random')[0]
            all_combo = _combo+target_combo
            im_all = maker.render_combo(all_combo, diminish=[v[0] for v in _combo])

            if im_item is None:
                continue
            ims = [im_all, im_item]
            im_grid = grid_ims(ims, cols=len(ims), to_rgb=True)
            im_grid = im_grid.resize((256*len(ims), 256))

            # im_all = crop_to_non_white(to_rgb(im_all).resize((512,512)))
            # im_item = crop_to_non_white(to_rgb(im_item).resize((512,512)))
            im_all = to_rgb(im_all).resize((512,512))
            im_item = to_rgb(im_item).resize((512,512))
            # im.show()
    
            data = {
                'pid': pid,
                'cp_id': comp.cp_id,
                'it_id': item.it_id,
                'component': '',
                'cp_combo': target_combo,
                'all_combo': _combo+target_combo,
                'im_all': encode_image(im_all),
                'im_item': encode_image(im_item),
                'im_grid': encode_image(im_grid),
                'task_type': 'item classification'
            }
            yield data

valid_layer_names = ['accessories', 'arm', 'back-hair', 'background', 'bangs', 'beard', 'blush', 'body', 'brows', 'bubbles', 'cheeks', 'choker', 'clothes', 'decorations', 'details', 'dress', 'earrings', 'ears', 'effects', 'emotion', 'expression', 'eye-shape', 'eyelids', 'eyes', 'face', 'face-accessories', 'facial-features', 'facial-hair', 'facial-markings', 'features', 'footwear', 'foreground', 'frames', 'freckles', 'fringe', 'glare', 'glasses', 'hair', 'hands', 'head', 'headwear', 'highlight', 'highlights', 'horns', 'innerwear', 'items', 'jacket', 'jewelry', 'lips', 'makeup', 'markings', 'mask', 'miscellaneous', 'moles', 'mouth', 'muzzle', 'necklace', 'nose', 'outerwear', 'outfits', 'overlays', 'patterns', 'piercings', 'pupil', 'scarf', 'scars', 'scarves', 'shadow', 'shapes', 'shirt', 'signature', 'skin-tone', 'socks', 'tags', 'tail', 'tattoos', 'tops', 'underclothes', 'underwear', 'wings', 'wrinkles', 'text']

layer_names = {k:k for k in valid_layer_names}
ValidNames = enum.Enum('names', dict(layer_names))

def gpt_describe(pid='5090'):
    data = next(gen_item_anno_samples(pid))
    im_str = data['im_all']
    import base64, io
    from PIL import Image
    image_data = base64.b64decode(im_str)
    
    # Use BytesIO to convert the binary data to a file-like object
    image_file = io.BytesIO(image_data)
    
    # Open the file-like object with PIL to create a PIL image
    pil_image = Image.open(image_file)
    pil_image.show()

# class Keypoint(BaseModel):
#     aspect: str
#     detail: str

class Classification(BaseModel):
    LayerName: ValidNames
    Explaination: str


def worker_batch(pid = "4211"):
    today = datetime.today().strftime('%Y%m%d')
    pids = list(comp_anno.keys())

    requests = []
    tasks = []
    name = ''
    batch_size = 1500

    task_added = set()
    with tqdm(total=batch_size) as pbar:
        for data in gen_item_anno_samples(pid):
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": ITEM_ANNO_PART1.format(names=','.join(valid_layer_names))},
                    {
                        "type": "image_url", 
                        "image_url": {
                            "url": f"data:image/png;base64,{data['im_all']}",
                            "detail": "low"
                        }
                    },
                    {"type": "text", "text": ITEM_ANNO_PART2},
                    {
                        "type": "image_url", 
                        "image_url": {
                            "url": f"data:image/png;base64,{data['im_item']}",
                            "detail": "low"
                        }
                    }
                ]}
            ]
            # messages=[
            #     {"role": "system", "content": "You are a helpful assistant."},
            #     {"role": "user", "content": [
            #         {"type": "text", "text": ITEM_ANNO.format(names=','.join(valid_layer_names))},
            #         {"type": "image_url", "image_url": {
            #             "url": f"data:image/png;base64,{data['im_grid']}"}
            #         }
            #     ]}
            # ]

            task_name = hashlib.md5(data['im_item'].encode('utf-8')).hexdigest()
            if task_name in task_added:
                continue
            else:
                task_added.add(task_name)

            _request = request_openai_json(prompt="", messages=messages, ans_format=Classification, batch=True, custom_id=task_name)
            data['task_id'] = task_name

            data.pop('im_item')
            data.pop('im_all')
            data.pop('im_grid')
            requests.append(_request)
            tasks.append(data)       

            name += task_name

            pbar.update(1)

    print(f'creating {len(tasks)} item annotation jobs')

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
    # worker_batch(pid='5090')
    # fetch_batch_result('20240812_c435.jsonl')
    # gpt_describe()

    one_task = 5804
    tasks = 650000
    price = 0.075
    unit = 1000000

    cost = one_task*tasks/unit*price
    print(cost)


        