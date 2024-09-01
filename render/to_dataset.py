import os, json
from Maker import Maker
from tqdm import tqdm
import hashlib

root = r'D:\picrew\data'
result_dir=r'data\gpt4o_component_description_batch_result'

def render_image(pid, comp_combo, total_combo):
    base_combo = [t for t in total_combo if t not in comp_combo]

    maker = Maker(os.path.join(root, pid))
    # comp_im = maker.render_combo(comp_combo)
    total_im = maker.render_combo(total_combo)
    base_im = maker.render_combo(base_combo)

    return base_im, total_im

dataset_dir = r'C:\Users\kaihe\Desktop\anime_works\hugging_face_datasets\AnimeMorphosis\data'

def write_im(im):
    name = hashlib.md5(im.tobytes()).hexdigest()[-8:]
    im.save(os.path.join(dataset_dir,'images', f'{name}.png'))
    return f'{name}.png'

def to_dataset(file_name):
    split = 0.8
    samples = []
    with open(os.path.join(result_dir, file_name)) as fin:
        for line in tqdm(fin.readlines()):
            data = json.loads(line.strip())
            base_im, result_im = render_image(data['pid'], data['cp_combo'], data['all_combo'])

            base_name = write_im(base_im)
            result_name = write_im(result_im)

            samples.append(json.dumps({
                'src':base_name,
                'tgt':result_name,
                'desc':data['description']
            }, ensure_ascii=False))

    train_samples = samples[:int(len(samples)*split)]
    test_samples = samples[int(len(samples)*split):]

    with open(os.path.join(dataset_dir, 'labels_train.jsonl'), 'a+') as fout:
        for sample in train_samples:
            fout.write(sample+'\n')


    with open(os.path.join(dataset_dir, 'labels_test.jsonl'), 'a+') as fout:
        for sample in test_samples:
            fout.write(sample+'\n')


if __name__=='__main__':
    to_dataset('20240804_3787.jsonl')
