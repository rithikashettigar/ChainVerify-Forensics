import os
import json
import uuid
import traceback
from werkzeug.utils import secure_filename

# --- IMPORTS ---
from core.hashing import sha256_bytes
from config import VIDEO_FRAMES_PATH, OUTPUTS_DIR

# Import the reconstruction tool safely
try:
    from core_video.video_reconstruction import reconstruct_video_from_frames
except ImportError:
    reconstruct_video_from_frames = None

# =======================================================
# HELPER: ROBUST BLOCKCHAIN LOADER
# =======================================================
def load_blockchain_blocks():
    """Loads blocks from blockchain.json or ledger.json and normalizes IDs."""
    blocks = []
    
    def load_from_file(path):
        loaded = []
        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Inject Key as Ref ID
                        for key, block in data.items():
                            if isinstance(block, dict):
                                if "reference_id" not in block:
                                    block["reference_id"] = key
                                loaded.append(block)
                    elif isinstance(data, list):
                        loaded = data
                except: pass
        return loaded

    # Try Primary
    blocks = load_from_file("registry/blockchain.json")
    # Try Backup
    if not blocks:
        blocks = load_from_file("registry/ledger.json")
        
    return blocks

# =======================================================
# 1. VERIFY ONLY (FAST)
# Checks hash & metadata. "Recommends" reconstruction if tampered.
# =======================================================
def verify_video(ref_id, video_path, original_filename=None):
    # 1. Compute Hash
    try:
        with open(video_path, "rb") as f:
            incoming_sha = sha256_bytes(f.read())
    except Exception as e:
        return {"status": "ERROR", "message": f"File read error: {e}"}

    # 2. Load Blocks
    blocks = load_blockchain_blocks()
    matched_entry = None
    
    def normalize(s): return str(s).strip().lower() if s else ""
    target_id = normalize(ref_id)

    # STRATEGY 1: Search by HASH (Authentic)
    for block in blocks:
        stored_sha = block.get("sha") or block.get("fingerprint")
        if stored_sha == incoming_sha:
            return {
                "status": "AUTHENTIC",
                "details": {
                    "sha": incoming_sha,
                    "matched_id": block.get("reference_id"),
                    "matched_filename": block.get("filename"),
                    "tamper_score": 0
                }
            }

    # STRATEGY 2: Search by ID (Tampered)
    if target_id:
        for block in blocks:
            bid = block.get("reference_id") or block.get("ref_id") or block.get("id")
            if normalize(bid) == target_id:
                matched_entry = block
                break

    # STRATEGY 3: Search by Filename (Last Resort)
    if not matched_entry and original_filename:
        for block in blocks:
            if block.get("filename") == original_filename:
                matched_entry = block
                break

    # FINAL DECISION
    if matched_entry:
        target_ref_id = matched_entry.get("reference_id")
        
        # Check if frames exist (THE RECOMMENDATION)
        frames_dir = os.path.join(VIDEO_FRAMES_PATH, str(target_ref_id))
        can_reconstruct = os.path.exists(frames_dir) and (reconstruct_video_from_frames is not None)

        return {
            "status": "TAMPERED",
            "message": "Hash mismatch against registered record.",
            "details": {
                "incoming_sha": incoming_sha,
                "expected_sha": matched_entry.get("sha"),
                "matched_id": target_ref_id,
                "matched_filename": matched_entry.get("filename"),
                "tamper_score": 100,
                # RECOMMENDATION FLAG:
                "can_reconstruct": can_reconstruct,
                "reconstructed_url": None 
            }
        }

    return {
        "status": "UNREGISTERED",
        "details": {"incoming_sha": incoming_sha, "message": "ID not found in blockchain."}
    }


# =======================================================
# 2. RECONSTRUCT CONTENT (ON-DEMAND) - FIXED
# Now accepts ref_id directly. No filename lookup.
# =======================================================
def reconstruct_video_content(ref_id):
    print(f"--- STARTING VIDEO RECONSTRUCTION FOR ID: {ref_id} ---")
    
    if not ref_id:
        raise Exception("No Reference ID provided for reconstruction.")

    # 1. Locate Frames Directory DIRECTLY using the ID
    # We trust the ID because the Verification step found it.
    frames_dir = os.path.join(VIDEO_FRAMES_PATH, str(ref_id))
    
    if not os.path.exists(frames_dir):
        # Debugging aid: Print what we are looking for
        print(f"DEBUG: Looking for frames at {frames_dir}")
        raise Exception(f"Forensic frames not found on server for ID: {ref_id}")

    # 2. Prepare Output Path
    # Create a unique filename for the user to view
    rec_filename = f"reconstructed_{ref_id}_{uuid.uuid4().hex[:6]}.mp4"
    rec_path = os.path.join(OUTPUTS_DIR, rec_filename)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    # 3. Run Reconstruction Tool
    if reconstruct_video_from_frames:
        success = reconstruct_video_from_frames(frames_dir, rec_path)
        
        if success and os.path.exists(rec_path):
            return f"/outputs/{rec_filename}"
        else:
            raise Exception("Video generation failed (Output file creation failed).")
    else:
        raise Exception("Reconstruction module (core_video) is not loaded.")