import os
from PIL import Image, UnidentifiedImageError
import cv2
from tqdm import tqdm

DATA_DIR = r"C:\Users\lolka\.vscode\joj\bone-fracture-detection\data\raw"
TARGET_SIZE = (224, 224)

def is_image_valid(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError):
        print(f" Файл повреждён или не изображение: {path}")
        return False

def preprocess_image(path):
    try:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f" Не удалось прочитать файл с помощью OpenCV: {path}")
            return
        img = cv2.resize(img, TARGET_SIZE)
        cv2.imwrite(path, img)
    except Exception as e:
        print(f" Ошибка при обработке {path}: {e}")

def process_dataset():
    for split in ["train","val","test"]:
        split_dir = os.path.join(DATA_DIR, split)
        if not os.path.exists(split_dir):
            print(f" Папка не найдена: {split_dir}")
            continue
        classes = [d for d in os.listdir(split_dir) if os.path.isdir(os.path.join(split_dir,d))]
        for cls in classes:
            cls_dir = os.path.join(split_dir, cls)
            files = [f for f in os.listdir(cls_dir) if f.lower().endswith(('.png','.jpg','.jpeg'))]
            for f in tqdm(files, desc=f"{cls} -> {split}", ncols=80):
                path = os.path.join(cls_dir, f)
                if is_image_valid(path):
                    preprocess_image(path)
                else:
                    continue

if __name__=="__main__":
    process_dataset()
    print(" Обработка завершена! Битые файлы пропущены, нормальные обработаны.")
