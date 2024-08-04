from huggingface_hub import HfApi
api = HfApi()

api.upload_folder(
    folder_path=r"C:\Users\kaihe\Desktop\anime_works\hugging_face_datasets\AnimeMorphosis",
    repo_id="kaihe/AnimeMorphosis",
    repo_type="dataset",
)