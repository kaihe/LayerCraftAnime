import os, json
from Maker import Maker
from common.tools import grid_ims
from PIL import ImageFont
from PIL import ImageDraw 

root = r'D:\picrew\data'
def test():
    f_path = r'data\gpt4o_component_description_batch_result\20240803_29c5.jsonl'
    for line in open(f_path).readlines():
        data = json.loads(line.strip())
        pid = data['pid']
        comp_combo = data['cp_combo']
        total_combo = data['all_combo']
        base_combo = [t for t in total_combo if t not in comp_combo]


        maker = Maker(os.path.join(root, pid))
        comp_im = maker.render_combo(comp_combo)
        total_im = maker.render_combo(total_combo)
        base_im = maker.render_combo(base_combo)

        draw = ImageDraw.Draw(comp_im)
        font = ImageFont.load_default()
        draw.text((0, 0), data['description'].encode('utf-8'),(0,0,0),font=font)

        ims = [base_im, comp_im, total_im]
        im = grid_ims(ims, cols=len(ims), to_rgb=True)
        im.show()
        # break

if __name__ == '__main__':
    test()