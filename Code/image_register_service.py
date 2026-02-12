import os
import pickle
import json
import hashlib
from datetime import datetime

from core.preprocess import load_grayscale, slice_blocks
from core.hashing import sha256_bytes, hash_block
from core.merkle import merkle_root
from core.registry import register_reference, get_reference
from config import BLOCK_STORAGE

# Ensure storage exists
os.makedirs(BLOCK_STORAGE, exist_ok=True)

# ================================
# LEDGER LOGGING (With Blockchain Links)
# ================================
def log_to_ledger(ref_id, sha, owner, filename):
    path = "registry/ledger.json"
    data = {}
    
    # 1. Load Existing Chain
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {}

    # 2. Initialize Genesis Block if empty
    if not data:
        genesis_block = {
            "index": 0,
            "timestamp": str(datetime.utcnow()),
            "filename": "GENESIS",
            "media_type": "none",
            "owner": "system",
            "fingerprint": "0" * 64,
            "prev_hash": "0" * 64,
            "block_hash": hashlib.sha256(b"GENESIS_BLOCK").hexdigest()
        }
        data["0"] = genesis_block

    # 3. Get Previous Block Info
    # We find the highest index to link to
    indices = [int(k) for k in data.keys()]
    last_index = max(indices) if indices else 0
    prev_block = data[str(last_index)]
    
    # Handle case where old ledger data might miss 'block_hash'
    prev_hash = prev_block.get("block_hash", "00000000000000000000000000000000_LEGACY")
    
    new_index = last_index + 1

    # 4. Create New Block Data
    block_content = {
        "index": new_index,
        "reference_id": ref_id,
        "media_type": "image",
        "filename": filename,
        "owner": owner,
        "fingerprint": sha,
        "timestamp": datetime.utcnow().isoformat(),
        "prev_hash": prev_hash
    }

    # 5. Calculate Block Hash (The "Crypto" part)
    block_string = json.dumps(block_content, sort_keys=True).encode()
    current_block_hash = hashlib.sha256(block_string).hexdigest()
    
    block_content["block_hash"] = current_block_hash

    # 6. Save
    data[str(new_index)] = block_content

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return new_index


# ================================
# REGISTER IMAGE FUNCTION
# ================================
def register_image(ref_id, image_path, owner):
    ref_id = ref_id.strip()

    # 1. Validation
    if not ref_id:
        return {"status": "error", "message": "Reference ID cannot be empty."}

    if get_reference(ref_id):
        return {"status": "error", "message": "Reference ID already exists."}

    # 2. Compute SHA
    with open(image_path, "rb") as f:
        sha = sha256_bytes(f.read())

    # 3. Duplicate Check
    chain_path = "registry/blockchain.json"
    if os.path.exists(chain_path):
        with open(chain_path, "r") as f:
            try:
                chain = json.load(f)
                for entry in chain.values():
                    if entry.get("sha") == sha:
                        return {"status": "duplicate", "message": "Media already on blockchain."}
            except:
                pass

    # 4. Processing
    img = load_grayscale(image_path)
    blocks = slice_blocks(img)

    block_hashes = []
    positions = []

    for pos, block in blocks:
        h = hash_block(block)
        block_hashes.append(h)
        positions.append(pos)

        with open(os.path.join(BLOCK_STORAGE, h), "wb") as f:
            pickle.dump(block, f)

    # 5. Merkle Root
    merkle_root_hash = merkle_root(block_hashes)
    filename = os.path.basename(image_path)

    # 6. Save to Registry
    register_reference(ref_id, {
        "media_type": "image",
        "filename": filename,
        "owner": owner,
        "sha": sha,
        "merkle_root": merkle_root_hash,
        "blocks": block_hashes,
        "positions": positions,
        "timestamp": datetime.utcnow().isoformat()
    })

    # 7. Log to Ledger (Calls the updated function above)
    block_index = log_to_ledger(ref_id, sha, owner, filename)

    return {
        "status": "registered",
        "ref_id": ref_id,
        "media_type": "image",
        "sha": sha,
        "block_index": block_index,
        "filename": filename
    }