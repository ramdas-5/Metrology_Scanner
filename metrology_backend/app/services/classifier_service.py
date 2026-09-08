"""
Loads the trained MobileNetV2-based label classifier (label_classifier.h5)
once at process start-up and exposes a simple `classify_image()` helper.

Model shape (as saved): input (224, 224, 3) -> MobileNetV2 backbone (frozen)
-> GlobalAveragePooling2D -> Dense(128, relu) -> Dropout -> Dense(2, softmax)

The two output classes are configurable via MODEL_CLASS_NAMES in .env; by
default they are treated as ["Non-Compliant Label", "Compliant Label"].
Swap this mapping to match whatever your model was actually trained on.
"""

import logging
import threading

import numpy as np
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

_model = None
_load_failed = False
_warmup_started = False
_warmup_lock = threading.Lock()


def _load_model():
    global _model, _load_failed
    if _model is None and not _load_failed:
        # Imported lazily so the rest of the API can start even if
        # tensorflow is briefly unavailable / still installing.
        try:
            import tensorflow as tf
            _model = tf.keras.models.load_model(settings.MODEL_PATH)
        except Exception as exc:
            # Model missing/corrupt or TF broken: permanently skip the
            # classifier instead of paying the load cost on every scan.
            logger.warning("Label classifier could not be loaded (%s); scans continue without it.", exc)
            _load_failed = True
            raise
    return _model


def warmup_async():
    """Load TensorFlow + the .h5 in a background thread shortly after startup
    so the first scan doesn't pay a 10-20s cold-start penalty."""
    global _warmup_started
    with _warmup_lock:
        if _warmup_started:
            return
        _warmup_started = True

    def _run():
        try:
            _load_model()
            logger.info("Label classifier warmed up and ready.")
        except Exception:
            pass  # already logged in _load_model

    threading.Thread(target=_run, daemon=True, name="classifier-warmup").start()


def _preprocess(image_path: str) -> np.ndarray:
    size = settings.MODEL_INPUT_SIZE
    img = Image.open(image_path).convert("RGB").resize((size, size))
    arr = np.array(img).astype("float32")
    arr = arr / 127.5 - 1.0  # MobileNetV2-style preprocessing (-1..1)
    return np.expand_dims(arr, axis=0)


def classify_image(image_path: str) -> dict:
    """
    Run the label classifier on an image.
    Returns {"label": <class name>, "confidence": <0-100 float>, "probabilities": {...}}
    """
    model = _load_model()
    batch = _preprocess(image_path)
    preds = model.predict(batch, verbose=0)[0]

    class_names = settings.model_class_name_list
    if len(class_names) != len(preds):
        class_names = [f"class_{i}" for i in range(len(preds))]

    best_idx = int(np.argmax(preds))
    probabilities = {class_names[i]: round(float(preds[i]) * 100, 2) for i in range(len(preds))}

    return {
        "label": class_names[best_idx],
        "confidence": round(float(preds[best_idx]) * 100, 2),
        "probabilities": probabilities,
    }
