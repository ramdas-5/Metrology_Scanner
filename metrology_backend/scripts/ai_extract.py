"""
Step 2 of the pipeline (standalone): OCR an image, then send the raw text to
OpenRouter and print the fixed-shape JSON (declarations + AI compliance score,
status, violations and narrative report).

Usage (from the metrology_backend directory, with the venv active):

    export OPENROUTER_API_KEY=sk-or-...        # Windows: set OPENROUTER_API_KEY=sk-or-...
    python scripts/ai_extract.py path/to/your_image.jpg

This only prints the JSON - it does NOT save anything. To save into the
database, upload the image through the running API (POST /api/scans), which
also applies the 80% similarity cache before calling the AI.

Output: JSON with the exact keys the backend stores.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings  # noqa: E402
from app.services import ai_service, ocr_service  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}", file=sys.stderr)
        return 1
    if not ai_service.is_ai_configured():
        print(
            "OPENROUTER_API_KEY is not set in .env. Add it (see .env.example) "
            "or export it, then retry.",
            file=sys.stderr,
        )
        return 1

    print(f"[1/2] OCR: {image_path}", file=sys.stderr)
    ocr = ocr_service.run_ocr_engine(image_path)
    print(f"      engine={ocr['engine']} chars={len(ocr['text'])}", file=sys.stderr)

    if not ocr["text"].strip():
        print("No text was detected in the image; nothing to send to the AI.", file=sys.stderr)
        return 1

    print(f"[2/2] Calling OpenRouter ({settings.OPENROUTER_MODEL})...", file=sys.stderr)
    payload = ai_service.extract_label_data(ocr["text"])
    payload["ocr_engine"] = ocr["engine"]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
