"""
scar_classifier.py  –  Load the trained model and classify a scar image.

Usage:
    python scar_classifier.py path/to/image.png
"""

import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image


MODEL_PATH = Path("scar_model.pth")

TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def load_model():
    checkpoint   = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    class_names  = checkpoint["class_names"]

    model = models.resnet18(weights=None)
    model.fc = torch.nn.Sequential(
        torch.nn.Dropout(0.3),
        torch.nn.Linear(model.fc.in_features, len(class_names)),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    return model, class_names


def classify(image_path: str) -> dict:
    model, class_names = load_model()

    img    = Image.open(image_path).convert("RGB")
    tensor = TRANSFORM(img).unsqueeze(0)        # add batch dimension: (1, 3, 224, 224)

    with torch.no_grad():
        probs = F.softmax(model(tensor), dim=1)[0]  # probabilities for each class

    predicted_idx   = probs.argmax().item()
    predicted_class = class_names[predicted_idx]
    confidence      = probs[predicted_idx].item() * 100

    all_probs = {name: round(probs[i].item() * 100, 1) for i, name in enumerate(class_names)}

    return {
        "class":       predicted_class,
        "confidence":  round(confidence, 1),
        "all_classes": all_probs,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scar_classifier.py <image_path>")
        sys.exit(1)

    result = classify(sys.argv[1])

    print(f"\nPredicted class : {result['class']}")
    print(f"Confidence      : {result['confidence']}%")
    print("\nAll probabilities:")
    for cls, prob in sorted(result["all_classes"].items(), key=lambda x: -x[1]):
        bar = "#" * int(prob / 5)
        print(f"  {cls:<20} {prob:5.1f}%  {bar}")
