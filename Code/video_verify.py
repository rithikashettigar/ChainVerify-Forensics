import os
import json
import shutil
from datetime import datetime

from core_video.extract_frames import extract_frames
from core_video.frame_hashing import hash_frame
from core.hashing import sha256_bytes
from core.registry import get_reference
from config import VIDEO_FRAMES_PATH

# ==========================================
# VIDEO VERIFICATION LOGIC
# ==========================================
def verify_video(ref_id, video_path, original_filename=None):
    """
    Verifies a video by:
    1. Checking if the Reference ID exists (if provided).
    2. Hashing the incoming video file.
    3. Checking against the Blockchain Ledger.
    4. (Optional) Checking frame-by-frame integrity.
    """
    
    # 1. Compute Hash of the incoming video
    with open(video_path, "rb") as f:
        incoming_sha = sha256_bytes(f.read())

    # 2. Look up in Blockchain / Registry
    chain_path = "registry/ledger.json"
    matched_entry = None
    
    # Strategy A: Search by Reference ID if provided
    if ref_id:
        # Check standard registry first
        reg_entry = get_reference(ref_id)
        if reg_entry:
            matched_entry = reg_entry
    
    # Strategy B: Search Blockchain by SHA (if Ref ID failed or empty)
    if not matched_entry and os.path.exists(chain_path):
        try:
            with open(chain_path, "r") as f:
                chain = json.load(f)
                # Search for the SHA in the ledger
                for block in chain.values():
                    if block.get("fingerprint") == incoming_sha:
                        matched_entry = block
                        break
        except:
            pass

    # ==========================================
    # CASE 1: EXACT MATCH (Authentic)
    # ==========================================
    if matched_entry:
        # If we found it by SHA, it's authentic.
        # If we found it by Ref ID, we check if SHAs match.
        stored_sha = matched_entry.get("sha") or matched_entry.get("fingerprint")
        
        if stored_sha == incoming_sha:
            return {
                "status": "AUTHENTIC",
                "details": {
                    "sha": incoming_sha,
                    "matched_id": matched_entry.get("reference_id") or matched_entry.get("index"),
                    "matched_filename": matched_entry.get("filename", "Unknown"),
                    "owner": matched_entry.get("owner", "Unknown")
                }
            }
        else:
            # Ref ID found, but hash doesn't match -> TAMPERED
            return {
                "status": "TAMPERED",
                "details": {
                    "incoming_sha": incoming_sha,
                    "expected_sha": stored_sha,
                    "matched_id": ref_id,
                    "matched_filename": matched_entry.get("filename"),
                    "tamper_score": 100,  # File hash mismatch is 100% fail
                    "message": "File hash does not match the registered record."
                }
            }

    # ==========================================
    # CASE 2: NO MATCH (Unregistered)
    # ==========================================
    return {
        "status": "UNREGISTERED",
        "details": {
            "incoming_sha": incoming_sha,
            "message": "No record found for this file or Reference ID."
        }
    }