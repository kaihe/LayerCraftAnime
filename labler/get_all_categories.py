import os
from tqdm import tqdm
import pickle

from datetime import datetime
from tqdm import tqdm
import json, random
import os
from Maker import Maker
from prompt import CATEGORY_ANNO
from common.tools import grid_ims
import hashlib
from labler.openai_func import encode_image, fetch_batch_result,do_batching, request_dir, result_dir,request_openai_json
from pydantic import BaseModel
from collections import Counter

root = r'D:\picrew\data'

def load_names():
    all_names = Counter()

    for pid in tqdm(os.listdir(root)):
        names = [d for d in os.listdir(os.path.join(root, pid)) if os.path.isdir(os.path.join(root, pid, d))]
        all_names.update(names)

    with open(r'data\comp_raw_names.pickle', 'wb') as fout:
        pickle.dump(all_names, fout)

class Names(BaseModel):
    Merged: list[str]

def merge_names():
    names = pickle.load(open(r'data\comp_raw_names.pickle','rb'))
    names = ','.join([k for k, _ in names.most_common(2000)])

    prompt = CATEGORY_ANNO.format(names = names)

    merged = Counter()
    for _ in tqdm(range(10)):
        ans = request_openai_json(prompt, ans_format=Names)
        ans = [s.lower() for s in ans.Merged]
        merged.update(ans)

    with open(r'data\categories.json','w+') as fout:
        json.dump(merged, fout)
    # print(prompt)

def final_merge():
    fname = r'data\categories.json'
    data = json.load(open(fname))
    names = sorted(list(data.keys()))
    prompt = CATEGORY_ANNO.format(names = ','.join(names))
    ans = request_openai_json(prompt, ans_format=Names)
    ans = [s.lower() for s in ans.Merged]
    print(ans)

if __name__=='__main__':
    final_merge()