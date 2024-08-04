import json, os

if __name__=='__main__':
    from datasets import load_dataset
    ds = load_dataset("kaihe/AnimeMorphosis", split='train')
    im = ds[0]['image_src']
    im.show()
    print(ds[0]['instruction'])

    # metadata_path = r'C:\Users\kaihe\Desktop\anime_works\hugging_face_datasets\AnimeMorphosis\data\labels_test.jsonl'
    # with open(metadata_path, 'r') as f:
    #     for line in f.readlines():
            
    #         labels = json.loads(line.strip())
    #         print(labels)
    
    #     print(len(f.readlines()))