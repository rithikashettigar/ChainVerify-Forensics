import os
import json
import hashlib
from datetime import datetime

from core_video.extract_frames import extract_frames
from core_video.frame_hashing import hash_frame
from core_video.video_merkle import video_merkle_root
from core.hashing import sha256_bytes
from core.registry import register_reference, get_reference
from config import VIDEO_FRAMES_PATH

os.makedirs(VIDEO_FRAMES_PATH, exist_ok=True)

# ================================
# UPDATED: LEDGER LOGGING (With Blockchain Links)
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
    indices = [int(k) for k in data.keys()]
    last_index = max(indices) if indices else 0
    prev_block = data[str(last_index)]
    
    prev_hash = prev_block.get("block_hash", "00000000000000000000000000000000_LEGACY")
    new_index = last_index + 1

    # 4. Create New Block Data
    block_content = {
        "index": new_index,
        "reference_id": ref_id,
        "media_type": "video",
        "filename": filename,
        "owner": owner,
        "fingerprint": sha,
        "timestamp": datetime.utcnow().isoformat(),
        "prev_hash": prev_hash
    }

    # 5. Calculate Block Hash
    block_string = json.dumps(block_content, sort_keys=True).encode()
    current_block_hash = hashlib.sha256(block_string).hexdigest()
    
    block_content["block_hash"] = current_block_hash

    # 6. Save
    data[str(new_index)] = block_content

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return new_index


# ================================
# REGISTER VIDEO FUNCTION
# ================================
def register_video(ref_id, video_path, owner):
    ref_id = ref_id.strip()

    # ---- Basic Validation ----
    if not ref_id:
        return {
            "status": "error",
            "message": "Reference ID cannot be empty."
        }

    # ---- Duplicate Reference ID Check ----
    if get_reference(ref_id):
        return {
            "status": "error",
            "message": "Reference ID already exists. Registration aborted."
        }

    # ---- Compute Full Video SHA ----
    with open(video_path, "rb") as f:
        video_sha = sha256_bytes(f.read())

    # ---- Duplicate MEDIA Check ----
    chain_path = "registry/blockchain.json"
    if os.path.exists(chain_path):
        with open(chain_path, "r") as f:
            try:
                chain = json.load(f)
                for entry in chain.values():
                    if entry.get("sha") == video_sha:
                        return {
                            "status": "duplicate",
                            "message": "This video already exists on the blockchain.",
                            "existing_ref": entry
                        }
            except:
                pass

    # ---- Extract Frames ----
    frames_dir = os.path.join(VIDEO_FRAMES_PATH, ref_id)
    os.makedirs(frames_dir, exist_ok=True)

    frames = extract_frames(video_path, frames_dir)

    frame_hashes = []
    frame_indexes = []

    for idx, frame_path in frames:
        frame_hashes.append(hash_frame(frame_path))
        frame_indexes.append(idx)

    # ---- Merkle Root ----
    merkle_root_hash = video_merkle_root(frame_hashes)

    filename = os.path.basename(video_path)

    # ---- Core Registry Write ----
    register_reference(ref_id, {
        "media_type": "video",
        "filename": filename,
        "owner": owner,
        "sha": video_sha,
        "merkle_root": merkle_root_hash,
        "frames": frame_hashes,
        "frame_indexes": frame_indexes,
        "timestamp": datetime.utcnow().isoformat()
    })

    # ---- Ledger Logging ----
    block_index = log_to_ledger(ref_id, video_sha, owner, filename)

    return {
        "status": "registered",
        "ref_id": ref_id,
        "media_type": "video",
        "sha": video_sha,
        "block_index": block_index,
        "total_frames": len(frame_hashes),
        "filename": filename
    }