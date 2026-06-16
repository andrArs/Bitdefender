"""
augment_data.py
---------------
Splits original images into train/val FIRST, then augments only the train set.
This prevents data leakage (augmented versions of the same image in both sets).

Output structure:
    dataset_augmented/
        train/
            dehiscence/   <- originals + 6 augmented versions each
            infected/
            ...
        val/
            dehiscence/   <- originals only, no augmentation
            infected/
            ...

Run:
    python augment_data.py
"""

import os
import random
from PIL import Image
import torchvision.transforms as T


INPUT_ROOT     = "scars_images"
OUTPUT_ROOT    = "dataset_augmented"
NUM_AUG        = 6      # augmented copies per training image
VAL_SPLIT      = 0.2    # 20% of originals go to val
RANDOM_SEED    = 42

random.seed(RANDOM_SEED)

# Augmentation pipeline (applied only to train images)
augmentations = T.Compose([
    T.RandomRotation(degrees=15),
    T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1, hue=0.02),
    T.RandomResizedCrop(size=(224, 224), scale=(0.85, 1.0)),
    T.RandomHorizontalFlip(p=0.5),
    T.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),
])

# Simple resize for val images (no augmentation, just standardize size)
resize = T.Resize((224, 224))


def save_image(img: Image.Image, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


for class_name in sorted(os.listdir(INPUT_ROOT)):
    class_in = os.path.join(INPUT_ROOT, class_name)
    if not os.path.isdir(class_in):
        continue

    # Collect all images in this class
    all_images = [
        f for f in os.listdir(class_in)
        if f.lower().endswith((".jpg", ".png", ".jpeg"))
    ]
    random.shuffle(all_images)

    # Split originals into train and val
    n_val   = max(1, int(len(all_images) * VAL_SPLIT))  # at least 1 val image
    val_images   = all_images[:n_val]
    train_images = all_images[n_val:]

    print(f"\n[{class_name}]  total={len(all_images)}  train={len(train_images)}  val={n_val}")

    # ── Val: copy originals resized, no augmentation ─────────────────────────
    for img_name in val_images:
        img = Image.open(os.path.join(class_in, img_name)).convert("RGB")
        img = resize(img)
        out_path = os.path.join(OUTPUT_ROOT, "val", class_name, img_name)
        save_image(img, out_path)

    # ── Train: copy originals + generate NUM_AUG augmented versions each ─────
    for img_name in train_images:
        img = Image.open(os.path.join(class_in, img_name)).convert("RGB")

        # Save the original (resized)
        resized = resize(img)
        out_path = os.path.join(OUTPUT_ROOT, "train", class_name, img_name)
        save_image(resized, out_path)

        # Save NUM_AUG augmented copies
        stem = img_name.rsplit(".", 1)[0]
        for i in range(NUM_AUG):
            aug_img  = augmentations(img)
            aug_name = f"{stem}_aug{i}.jpg"
            out_path = os.path.join(OUTPUT_ROOT, "train", class_name, aug_name)
            save_image(aug_img, out_path)

    train_count = len(train_images) * (1 + NUM_AUG)
    print(f"           -> train total: {train_count} | val total: {n_val}")

print("\n\nFinal summary:")
for split in ["train", "val"]:
    split_dir = os.path.join(OUTPUT_ROOT, split)
    if not os.path.exists(split_dir):
        continue
    print(f"  {split}/")
    for cls in sorted(os.listdir(split_dir)):
        count = len(os.listdir(os.path.join(split_dir, cls)))
        print(f"    {cls:<20} {count} images")

print("\nDone! Dataset is in:", OUTPUT_ROOT)
