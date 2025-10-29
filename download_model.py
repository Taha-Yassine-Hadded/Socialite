import hashlib
import os
import sys
import urllib.request

MODEL_DIR = os.path.join('models')
MODEL_PATH = os.path.join(MODEL_DIR, 'travel_classifier.pth')
# Provide a direct URL via env var or edit this default
MODEL_URL = os.environ.get('TRAVEL_MODEL_URL', '').strip()
# Optional checksum to verify integrity
MODEL_SHA256 = os.environ.get('TRAVEL_MODEL_SHA256', '').strip()


def sha256sum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    if os.path.exists(MODEL_PATH):
        print(f"✅ Found existing model: {MODEL_PATH}")
        if MODEL_SHA256:
            digest = sha256sum(MODEL_PATH)
            if digest != MODEL_SHA256:
                print(f"⚠️  Checksum mismatch. Expected {MODEL_SHA256}, got {digest}. Re-download suggested.")
        return 0

    if not MODEL_URL:
        print("❌ No model URL provided. Set TRAVEL_MODEL_URL env var to a direct download link.")
        print("Example (PowerShell):")
        print("  $env:TRAVEL_MODEL_URL='https://example.com/travel_classifier.pth'")
        print("Optionally set TRAVEL_MODEL_SHA256 for integrity checks.")
        return 1

    print(f"⬇️  Downloading model from: {MODEL_URL}")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 1

    print(f"✅ Saved: {MODEL_PATH}")
    if MODEL_SHA256:
        digest = sha256sum(MODEL_PATH)
        print(f"   SHA256: {digest}")
        if digest != MODEL_SHA256:
            print("⚠️  Checksum mismatch. File may be corrupted.")
            return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
