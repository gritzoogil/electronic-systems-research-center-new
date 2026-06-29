"""
Uploads images from the old static site's build/img/ folder to Vercel Blob.
Produces image_url_map.json mapping old relative paths -> new hosted URLs.

Run with: uv run python scripts/upload_images.py
"""
import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()

OLD_IMG_ROOT = r"C:\sync\Work\ESRC\Electronic-Systems-Research-Center.github.io-main\build\img"
OUTPUT_MAP_FILE = "image_url_map.json"
BLOB_TOKEN = os.environ["BLOB_READ_WRITE_TOKEN"]  # from Vercel dashboard

url_map = {}

for root, _, files in os.walk(OLD_IMG_ROOT):
    for filename in files:
        local_path = os.path.join(root, filename)
        rel_path = os.path.relpath(local_path, OLD_IMG_ROOT).replace("\\", "/")
        blob_pathname = f"images/{rel_path}"

        with open(local_path, "rb") as f:
            resp = requests.put(
                f"https://blob.vercel-storage.com/{blob_pathname}",
                data=f.read(),
                headers={
                    "authorization": f"Bearer {BLOB_TOKEN}",
                    "x-content-type": "image/webp" if filename.endswith(".webp") else "application/octet-stream",
                },
            )
        if resp.status_code == 200:
            url_map[rel_path] = resp.json()["url"]
            print(f"Uploaded: {rel_path}")
        else:
            print(f"FAILED: {rel_path} -> {resp.status_code} {resp.text}")

with open(OUTPUT_MAP_FILE, "w", encoding="utf-8") as f:
    json.dump(url_map, f, indent=2, ensure_ascii=False)

print(f"\nDone. {len(url_map)} images uploaded.")