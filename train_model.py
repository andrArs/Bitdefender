"""
train_model.py
--------------
Trains a ResNet18 classifier on the augmented scar dataset.

Expects dataset_augmented/ to have this structure (created by augment_data.py):
    dataset_augmented/
        train/   <- originals + augmented copies
        val/     <- originals only (no augmentation, no leakage)

Training has two phases:
  Phase 1 - backbone frozen, only the FC head is trained
  Phase 2 - full network unfrozen, fine-tuned with a smaller learning rate

Anti-overfit measures:
  - Dropout(0.3) before the final FC layer
  - Weight decay (L2 regularization) in the optimizer
  - Early stopping based on validation loss

Run:
    python train_model.py
"""

from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from torchvision.models import ResNet18_Weights
import matplotlib.pyplot as plt

from utils import EarlyStopping


# ── Config ───────────────────────────────────────────────────────────────────

DATA_DIR   = Path("dataset_augmented")
MODEL_PATH = Path("scar_model.pth")

BATCH_SIZE   = 16
EPOCHS_P1    = 15       # max epochs for phase 1 (early stopping can cut it short)
EPOCHS_P2    = 20       # max epochs for phase 2
LR_HEAD      = 1e-3
LR_FINETUNE  = 1e-4
PATIENCE     = 5        # early stopping patience (epochs without improvement)
WEIGHT_DECAY = 1e-4     # L2 regularization — penalizes large weights (reduces overfit)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ── Transforms ───────────────────────────────────────────────────────────────
# Augmentation was already done on disk, so we only normalize here.
# Val images get the same preprocessing but no augmentation.

TRAIN_TRANSFORMS = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),          # mild extra variation during training
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

VAL_TRANSFORMS = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


# ── Data loading ─────────────────────────────────────────────────────────────

def build_loaders():
    """Load train and val sets from the pre-split dataset folders."""
    train_ds = datasets.ImageFolder(DATA_DIR / "train", transform=TRAIN_TRANSFORMS)
    val_ds   = datasets.ImageFolder(DATA_DIR / "val",   transform=VAL_TRANSFORMS)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False)

    return train_loader, val_loader, train_ds.classes


# ── Model ────────────────────────────────────────────────────────────────────

def build_model(num_classes: int) -> nn.Module:
    """
    Pretrained ResNet18 with a custom head:
      original FC (512 -> 1000)  replaced by:
      Dropout(0.3) + Linear(512 -> num_classes)

    Dropout randomly zeros 30% of neurons during training,
    forcing the network not to rely on any single feature — reduces overfit.
    """
    model = models.resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)

    for param in model.parameters():
        param.requires_grad = False     # freeze backbone for phase 1

    in_features = model.fc.in_features  # 512
    model.fc = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, num_classes),
    )

    return model.to(DEVICE)


# ── Training helpers ─────────────────────────────────────────────────────────

def run_epoch(model, loader, criterion, optimizer, training: bool):
    """One full pass over the dataset. Returns (avg_loss, accuracy)."""
    model.train(training)

    total_loss, correct, total = 0.0, 0, 0

    with torch.set_grad_enabled(training):
        for images, labels in loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)

            outputs = model(images)
            loss    = criterion(outputs, labels)

            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            total_loss += loss.item()
            correct    += (outputs.argmax(dim=1) == labels).sum().item()
            total      += labels.size(0)

    return total_loss / len(loader), correct / total


def train_phase(model, train_loader, val_loader, criterion,
                optimizer, scheduler, max_epochs: int, phase_name: str):
    """
    Train for up to max_epochs, with early stopping on val_loss.
    Saves the best model to MODEL_PATH.
    Returns (best_val_acc, train_losses, val_losses).
    """
    early_stopping = EarlyStopping(patience=PATIENCE, min_delta=0.001)
    best_val_acc   = 0.0
    train_losses, val_losses = [], []

    for epoch in range(1, max_epochs + 1):
        tr_loss, tr_acc = run_epoch(model, train_loader, criterion, optimizer, training=True)
        va_loss, va_acc = run_epoch(model, val_loader,   criterion, optimizer, training=False)
        scheduler.step()

        train_losses.append(tr_loss)
        val_losses.append(va_loss)

        saved = ""
        if va_acc > best_val_acc:
            best_val_acc = va_acc
            torch.save(model.state_dict(), MODEL_PATH)
            saved = "  <-- saved"

        print(f"  [{phase_name}] Epoch {epoch:02d}/{max_epochs} | "
              f"loss={tr_loss:.4f} acc={tr_acc:.3f} | "
              f"val_loss={va_loss:.4f} val_acc={va_acc:.3f}{saved}")

        if early_stopping(va_loss):
            print(f"  [{phase_name}] Early stopping at epoch {epoch}.")
            break

    return best_val_acc, train_losses, val_losses


# ── Evaluation ───────────────────────────────────────────────────────────────

def evaluate_per_class(model, val_loader, class_names):
    """Print per-class accuracy on the validation set."""
    model.eval()
    n  = len(class_names)
    correct = [0] * n
    total   = [0] * n

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            preds = model(images).argmax(dim=1)
            for cls in range(n):
                mask         = labels == cls
                total[cls]  += mask.sum().item()
                correct[cls]+= (preds[mask] == cls).sum().item()

    print("\nPer-class accuracy on validation set:")
    for cls, name in enumerate(class_names):
        acc = (correct[cls] / total[cls] * 100) if total[cls] > 0 else 0.0
        bar = "#" * int(acc / 5)
        print(f"  {name:<20} {acc:5.1f}%  {bar}")


def plot_losses(p1_train, p1_val, p2_train, p2_val):
    """Save a loss curve plot to training_curve.png."""
    all_train = p1_train + p2_train
    all_val   = p1_val   + p2_val
    split_at  = len(p1_train)   # where phase 2 starts

    plt.figure(figsize=(10, 4))
    plt.plot(all_train, label="Train loss")
    plt.plot(all_val,   label="Val loss")
    plt.axvline(x=split_at, color="gray", linestyle="--", label="Phase 2 start")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig("training_curve.png")
    print("Loss curve saved to training_curve.png")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Device: {DEVICE}")

    train_loader, val_loader, class_names = build_loaders()
    print(f"Classes: {class_names}")
    print(f"Train: {len(train_loader.dataset)} images | Val: {len(val_loader.dataset)} images\n")

    model     = build_model(num_classes=len(class_names))
    criterion = nn.CrossEntropyLoss()

    # ── Phase 1: head only ────────────────────────────────────────────────────
    print("=" * 60)
    print("Phase 1: FC head only (backbone frozen)")
    print("=" * 60)

    # Only pass FC parameters — backbone is frozen anyway, but being explicit
    optimizer_p1 = torch.optim.Adam(model.fc.parameters(), lr=LR_HEAD,
                                    weight_decay=WEIGHT_DECAY)
    scheduler_p1 = torch.optim.lr_scheduler.StepLR(optimizer_p1, step_size=5, gamma=0.5)

    best_p1, p1_train_losses, p1_val_losses = train_phase(
        model, train_loader, val_loader, criterion,
        optimizer_p1, scheduler_p1, EPOCHS_P1, "P1"
    )
    print(f"\nPhase 1 done. Best val acc: {best_p1:.4f}")

    model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))

    # ── Phase 2: fine-tune full network ───────────────────────────────────────
    print()
    print("=" * 60)
    print("Phase 2: fine-tuning full network (backbone unfrozen)")
    print("=" * 60)

    for param in model.parameters():
        param.requires_grad = True

    optimizer_p2 = torch.optim.Adam([
        {"params": model.fc.parameters(),
         "lr": LR_HEAD * 0.1, "weight_decay": WEIGHT_DECAY},
        {"params": [p for n, p in model.named_parameters() if "fc" not in n],
         "lr": LR_FINETUNE,   "weight_decay": WEIGHT_DECAY},
    ])
    scheduler_p2 = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer_p2, T_max=EPOCHS_P2)

    best_p2, p2_train_losses, p2_val_losses = train_phase(
        model, train_loader, val_loader, criterion,
        optimizer_p2, scheduler_p2, EPOCHS_P2, "P2"
    )
    print(f"\nPhase 2 done. Best val acc: {best_p2:.4f}")

    # ── Results ───────────────────────────────────────────────────────────────
    model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    evaluate_per_class(model, val_loader, class_names)
    plot_losses(p1_train_losses, p1_val_losses, p2_train_losses, p2_val_losses)

    # Save weights + class names together (needed by the classifier later)
    torch.save({
        "model_state_dict": model.state_dict(),
        "class_names":      class_names,
    }, MODEL_PATH)

    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
