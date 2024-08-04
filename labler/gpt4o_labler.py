from datetime import datetime
from tqdm import tqdm
import json, random
from openai import OpenAI 
import base64
import requests
import os
from Maker import Maker
from prompt import BODY_ANNO, ITEM_ANNO
from common.tools import grid_ims
from io import BytesIO
from config import FORMAL_NAMES
import hashlib

# Function to encode the image
def encode_image(image_input):
    if isinstance(image_input, str):
        with open(image_input, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    else:
        buffered = BytesIO()
        image_input.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

## Set the API key and model name
MODEL="gpt-4o-mini"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY_IMAGE_EDITING"))

def request_openai(prompt, image_input=None, batch=False, task_id=''):
    if image_input is not None:
        # Getting the base64 string
        if not isinstance(image_input, str):
            base64_image = encode_image(image_input)
        else:
            base64_image = image_input

        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"}
                }
            ]}
        ]
    else:
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt}
            ]}
        ]

    if not batch:
        response = client.chat.completions.create(
            model=MODEL,
            messages = messages,
            temperature=0.0,
        )
        return response.choices[0].message.content
    else:
        _request = {
            "custom_id": task_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "messages" : messages,
                "temperature" : 0.0
            }
        }
        return _request


def get_body_comp(pid=None):
    pid = '53713'
    root = os.path.join(r'D:\picrew\data', pid)
    maker = Maker(root)
    prompt = str.format(BODY_ANNO, input = ','.join([cp.cp_name for cp in maker.components]))
    anno = request_openai(prompt)
    print(anno)

item_annos = json.load(open(r'D:\valuable_anno_data\picrew\item_anno.json'))

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
        if k in ('eye','mouth','eyebrow','front','back'):
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

def get_comp_description(pid):
    data = gen_comp_im(pid)
    prompt = ITEM_ANNO.format(cp_name = data['component'])
    ans = request_openai(prompt, image_input=data['im_str'])
    data['description'] = ans
    return data

def worker_description_gen():
    comp_anno_file = r'D:\valuable_anno_data\picrew\anno.json'
    comp_anno = json.load(open(comp_anno_file))
    out_dir = r'data\gpt4o_component_description'
    today = datetime.today().strftime('%Y%m%d')

    N = 10
    pids = list(comp_anno.keys())
    for _ in tqdm(range(N)):
        pid = random.choice(pids)
        data = get_comp_description(pid)
        if data is None:
            continue

        with open(os.path.join(out_dir, f'{today}.jsonl'), 'a') as fout:
            fout.write(json.dumps(data, ensure_ascii=False)+'\n')


request_dir = r'data\gpt4o_component_description_batch_request'
result_dir = r'data\gpt4o_component_description_batch_result'
def worker_description_batch_request(N = 500):
    comp_anno_file = r'D:\valuable_anno_data\picrew\anno.json'
    comp_anno = json.load(open(comp_anno_file))
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

        _request = request_openai(prompt, image_input=data['im_str'], batch=True, task_id=task_name)
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
    

def do_batching(file_name):
    # file_name = r'data\gpt4o_component_description_batch_request\20240803_c63f.jsonl'
    batch_file = client.files.create(
        file=open(file_name, "rb"),
        purpose="batch"
    )

    print('finish upload!!!')
    batch_job = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    f_job_recoder = r'data\job_mapping\all_jobs.json'
    all_jobs = json.load(open(f_job_recoder))
    all_jobs[file_name] = batch_job.id

    with open(f_job_recoder, 'w+') as fout:
        json.dump(all_jobs,fout, ensure_ascii=False)
    print(f'job created for file: {file_name}')

def check_batch_result(f_name):
    f_job_recoder = r'data\job_mapping\all_jobs.json'
    all_jobs = json.load(open(f_job_recoder))
    job_id = all_jobs[f_name]
    batch_job = client.batches.retrieve(job_id)
    print(batch_job)

def fetch_batch_result(request_file):
    f_job_recoder = r'data\job_mapping\all_jobs.json'
    all_jobs = json.load(open(f_job_recoder))
    job_id = all_jobs[request_file]

    batch_job = client.batches.retrieve(job_id)

    if not batch_job.status == 'completed':
        print('not completed!')
        return 
    result_file_id = batch_job.output_file_id
    batch_return_content = client.files.content(result_file_id).content
    
    tasks = json.load(open(os.path.join(request_dir, os.path.basename(request_file)).replace('.jsonl','_task.jsonl')))
    results = []
    for _body in batch_return_content.decode('utf8').split('\n'):
        if len(_body)==0:
            continue
        result_body = json.loads(_body)
        task = tasks[result_body['custom_id']]
        task['description'] = result_body['response']['body']['choices'][0]['message']['content']
        results.append(task)

    result_file = os.path.join(result_dir, os.path.basename(request_file))
    with open(result_file, 'w+') as fout:
        for task in results:
            fout.write(json.dumps(task, ensure_ascii=False)+'\n')


if __name__ == '__main__':
    # worker_description_batch_request(N=2000)
    # fetch_batch_result(r'data\gpt4o_component_description_batch_request\20240803_c6e4.jsonl')

    data = get_comp_description('241756')
    print(data['description'])
    