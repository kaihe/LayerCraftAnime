from datetime import datetime
from tqdm import tqdm
import json, random
from openai import OpenAI 
import base64
import requests
import os
from Maker import Maker
from prompts.legacy_prompt import BODY_ANNO, ITEM_ANNO
from common.tools import grid_ims
from io import BytesIO
from config import FORMAL_NAMES
import hashlib
from openai.lib._parsing import type_to_response_format_param 

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
# MODEL = 'gpt-4o-2024-08-06'
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY_IMAGE_EDITING"))

def request_openai_json(messages=None, ans_format=None, batch=False, custom_id=''):
    if not batch:
        # make rquest directly if not batch and return the result
        if ans_format is not None:
            response = client.beta.chat.completions.parse(
                model=MODEL,
                messages = messages,
                response_format=ans_format,
            )
            return response.choices[0].message.parsed
        else:
            response = client.chat.completions.create(
                model=MODEL,
                messages = messages
            )
            print(response.usage)
            return response.choices[0].message.content
    else:
        # only make the request body for batch requests
        _request = {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "messages" : messages,
                "response_format" : type_to_response_format_param(ans_format)
            }
        }
        return _request


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
    print(f'job created for file: {os.path.basename(file_name).replace(".jsonl", "")}')

def check_batch_result(f_name):
    f_job_recoder = r'data\job_mapping\all_jobs.json'
    all_jobs = json.load(open(f_job_recoder))
    job_id = all_jobs[f_name]
    batch_job = client.batches.retrieve(job_id)
    print(batch_job)


request_dir = r'data\gpt4o_component_description_batch_request'
result_dir = r'data\gpt4o_component_description_batch_result'
def fetch_batch_result(request_file):
    f_job_recoder = r'data\job_mapping\all_jobs.json'
    all_jobs = json.load(open(f_job_recoder))
    job_id = all_jobs[f'{request_dir}\\{request_file}']

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