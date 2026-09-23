"""
Ad-hoc benchmark: run the configured OCR engine + declaration parser over the
uploaded label images and print a compact per-image report, so OCR accuracy
changes can be compared before/after editing ocr_service.py.

Usage (from metrology_backend, with the venv active):

    python scripts/bench_ocr.py [image_path ...]
    python scripts/bench_ocr.py           # all images in app/uploads
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import ocr_service  # noqa: E402


def main():
    args = sys.argv[1:]
    if args:
        paths = [a for a in args if os.path.exists(a)]
    else:
        paths = sorted(glob.glob(os.path.join("app", "uploads", "*.*")))
    paths = [p for p in paths if p.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]

    if not paths:
        print("No images found.")
        return 1

    keys = ["mrp", "net_quantity", "manufacturer", "mfg_date", "consumer_care", "country_of_origin", "unit_sale_price"]
    total_fields = 0
    found_fields = 0
    total_chars = 0

    for path in paths:
        ocr = ocr_service.run_ocr_engine(path)
        fields = ocr_service.parse_declarations(ocr["text"])
        text = ocr["text"]
        found = {k: fields.get(k) for k in keys if fields.get(k)}
        n_found = len(found)
        total_fields += len(keys)
        found_fields += n_found
        total_chars += len(text)
        print(f"\n===== {os.path.basename(path)} ({ocr['engine']}, {len(text)} chars) =====")
        print(json.dumps(found, ensure_ascii=False, indent=1))
        if len(text) > 0:
            print("TEXT:", " | ".join(text.splitlines()[:6])[:300])

    print(f"\n--- OVERALL: {found_fields}/{total_fields} fields found across {len(paths)} images, avg {total_chars // max(1, len(paths))} chars/image ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())