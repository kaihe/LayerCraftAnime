from Maker import Maker
import os, json
import random

item_annos = json.load(open(r'D:\valuable_anno_data\picrew\item_anno.json'))
comp_annos = json.load(open(r'D:\valuable_anno_data\picrew\anno.json'))

def get_body_anno():
    # get the missing body component and the corresponding item_ids
    pid = '241678'
    comp_names = comp_annos[pid].keys()
    print(comp_names)

    root = os.path.join(r'D:\picrew\data', pid)
    maker = Maker(root)

    comps = [cp for cp in maker.components if cp.cp_name == 'kuchi']
    combo = maker.gen_combo([c.cp_id for c in comps], type='random')[0]
    im = maker.render_combo(combo)
    # im.show()

    cp = comps[0]
    print(f"\"{cp.cp_id}\":[{','.join([str(it.it_id) for it in cp.items])}]")

def get_cp_id(pid, cp_name):
    root = os.path.join(r'D:\picrew\data', pid)
    maker = Maker(root)
    comp = [c for c in maker.components if c.cp_name == cp_name]
    print(comp[0].cp_id)

if __name__ =='__main__':
    get_cp_id('5090', '左手')