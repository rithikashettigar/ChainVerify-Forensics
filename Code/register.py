import sys
import os
import pickle
import json
from PIL import Image

from core.preprocess import load_grayscale, slice_blocks
from core.hashing import sha256_bytes, hash_block
from core.merkle import merkle_root
from core.registry import register_reference, get_reference
from config import BLOCK_STORAGE

os.makedirs(BLOCK_STORAGE, exist_ok=True)


# -------------------------------
# Ledger logging (DISPLAY ONLY)
# -------------------------------
def log_to_ledger(ref_id, full_hash):
    path = "registry/ledger.json"

    if not os.path.exists(path):
        data = {}
    else:
        with open(path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

    index = str(len(data) + 1)

    data[index] = {
        "reference_id": ref_id,
        "short_hash": full_hash[:8],
        "full_hash": full_hash,
        "status": "registered"
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# -------------------------------
# Argument check
# -------------------------------
if len(sys.argv) < 3:
    print("Usage: python register.py <ref_id> <image>")
    sys.exit(1)

ref_id = sys.argv[1]
image_path = sys.argv[2]


# -------------------------------
# Prevent re-registration
# -------------------------------
if get_reference(ref_id):
    print(f"Reference '{ref_id}' already exists.")
    print("Registration aborted. Use verify instead.")
    sys.exit(0)


# -------------------------------
# Image processing
# -------------------------------
img = load_grayscale(image_path)
blocks = slice_blocks(img)

block_hashes = []
positions = []

for pos, block in blocks:
    h = hash_block(block)
    block_hashes.append(h)
    positions.append(pos)

    with open(BLOCK_STORAGE + h, "wb") as f:
        pickle.dump(block, f)


# -------------------------------
# Hashing & Merkle Tree
# -------------------------------
root = merkle_root(block_hashes)
sha = sha256_bytes(open(image_path, "rb").read())


# -------------------------------
# Core registration (REAL LOGIC)
# -------------------------------
register_reference(ref_id, {
    "sha": sha,
    "merkle_root": root,
    "blocks": block_hashes,
    "positions": positions
})


# -------------------------------
# Ledger logging (SAFE ADD-ON)
# -------------------------------
log_to_ledger(ref_id, sha)

print(f"Registered reference: {ref_id}")
