"""
Step 1 of the pipeline (standalone): OCR any image and print as much raw text
as possible, using the engine configured via OCR_ENGINE in .env.

Usage (from the metrology_backend directory, with the venv active):

    python scripts/ocr_text.py path/to/your_image.jpg

Output: JSON  { "engine": "paddle" | "tesseract", "text": "..." }
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import ocr_service  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}", file=sys.stderr)
        return 1

    result = ocr_service.run_ocr_engine(image_path)
    print(json.dumps({"engine": result["engine"], "text": result["text"]}, ensure_ascii=False, indent=2))

    if not result["text"].strip():
        print("No text was detected. Try a clearer / flatter photo.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
