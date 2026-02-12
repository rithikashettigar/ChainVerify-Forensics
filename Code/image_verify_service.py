import os
import json
import uuid
import traceback
import numpy as np
from PIL import Image

# Core Imports
from core.hashing import sha256_bytes, hash_block
from core.preprocess import load_grayscale, slice_blocks
from core.verify import compare_blocks
from core.recovery import recover_image
from core.registry import get_reference 
from config import BLOCK_STORAGE 

# Output directory
RECOVERY_OUTPUT_DIR = "static/reconstructed"
os.makedirs(RECOVERY_OUTPUT_DIR, exist_ok=True)

def verify_image(ref_id, file_path, original_filename=None):
    print(f"--- VERIFYING IMAGE: {ref_id} ---")

    # 1. Compute Hash of the incoming file
    try:
        with open(file_path, "rb") as f:
            incoming_sha = sha256_bytes(f.read())
    except Exception as e:
        return {"status": "ERROR", "message": f"File read error: {e}"}

    # 2. Find the authentic record
    matched_entry = None
    
    # Strategy A: Search by Reference ID
    if ref_id:
        matched_entry = get_reference(ref_id)
        if not matched_entry:
            chain_path = "registry/blockchain.json"
            if os.path.exists(chain_path):
                with open(chain_path, "r") as f:
                    chain = json.load(f)
                    for key, block in chain.items():
                        if key.lower() == str(ref_id).lower():
                            matched_entry = block
                            matched_entry["reference_id"] = key
                            break

    # Strategy B: Search by SHA
    if not matched_entry:
        chain_path = "registry/blockchain.json"
        if os.path.exists(chain_path):
            with open(chain_path, "r") as f:
                chain = json.load(f)
                for key, block in chain.values():
                    stored_hash = block.get("sha") or block.get("fingerprint")
                    if stored_hash == incoming_sha:
                        matched_entry = block
                        matched_entry["reference_id"] = key
                        break

    # ==========================================
    # CASE: UNREGISTERED
    # ==========================================
    if not matched_entry:
        return {
            "status": "UNREGISTERED",
            "message": f"No record found for ID '{ref_id}' or this file hash.",
            "details": {
                "incoming_sha": incoming_sha,
                "incoming_filename": original_filename
            }
        }

    # Record Found! Check Content.
    stored_sha = matched_entry.get("sha") or matched_entry.get("fingerprint")
    target_ref_id = matched_entry.get("reference_id") or ref_id

    # ==========================================
    # CASE: AUTHENTIC
    # ==========================================
    if stored_sha == incoming_sha:
        return {
            "status": "AUTHENTIC",
            "message": "Integrity is intact. Image is authentic.",
            "details": {
                "sha": incoming_sha,
                "matched_id": target_ref_id,
                "matched_filename": matched_entry.get("filename"),
                "tamper_score": 0
            }
        }

    # ==========================================
    # CASE: TAMPERED (Hash Mismatch)
    # ==========================================
    print(f"-> Hash Mismatch. Starting Forensics on {target_ref_id}...")
    
    try:
        # 1. Load Image for Forensics
        img_gray = load_grayscale(file_path) 
        img_pil = Image.open(file_path).convert("RGB") 

        # 2. Slice and Hash
        img_blocks = slice_blocks(img_gray)
        current_hashes = [hash_block(b) for _, b in img_blocks]
        
        # 3. Get Positions
        current_positions = []
        for pos_tuple, _ in img_blocks:
            if len(pos_tuple) >= 2:
                current_positions.append((pos_tuple[0], pos_tuple[1]))
            else:
                current_positions.append((0, 0))

        # 4. Get Stored Blocks
        stored_blocks = matched_entry.get("blocks", [])

        if not stored_blocks:
            return {
                "status": "TAMPERED", 
                "message": "Tampering detected, but blockchain blocks are missing.",
                "details": {"matched_id": target_ref_id, "tamper_score": 100}
            }

        # 5. Compare Blocks
        tampered_indices, percent = compare_blocks(current_hashes, stored_blocks)

        if not tampered_indices:
            return {"status": "AUTHENTIC", "message": "Metadata mismatch only.", "details": {"tamper_score": 0}}

        # 6. Reconstruct / Recover (Call Dual Generator)
        forensic_arr, clean_arr = recover_image(
            img_pil,
            tampered_indices,
            current_positions, 
            stored_blocks 
        )

        # 7. Save BOTH Results
        unique_id = uuid.uuid4().hex[:8]
        
        # A. Save Forensic Image (Red Grid)
        forensic_filename = f"forensic_{unique_id}.png"
        forensic_path = os.path.join(RECOVERY_OUTPUT_DIR, forensic_filename)
        
        if forensic_arr.dtype != np.uint8: forensic_arr = forensic_arr.astype(np.uint8)
        Image.fromarray(forensic_arr).save(forensic_path)
        
        # B. Save Clean Reconstruction (Grayscale Authentic)
        clean_filename = f"clean_{unique_id}.png"
        clean_path = os.path.join(RECOVERY_OUTPUT_DIR, clean_filename)
        
        if clean_arr.dtype != np.uint8: clean_arr = clean_arr.astype(np.uint8)
        Image.fromarray(clean_arr).save(clean_path)
        
        # URLs for frontend
        forensic_url = f"/static/reconstructed/{forensic_filename}"
        clean_url = f"/static/reconstructed/{clean_filename}"

        return {
            "status": "TAMPERED",
            "message": "Visual manipulation detected.",
            "details": {
                "matched_id": target_ref_id,
                "matched_filename": matched_entry.get("filename"),
                "sha": incoming_sha,
                "expected_sha": stored_sha,
                "tamper_score": round(percent, 2),
                
                # --- RECOMMENDATION FLAGS ---
                "can_reconstruct": True, # Always true for images if we got this far
                "reconstructed_url": forensic_url, # Default view
                "clean_url": clean_url            # Alternative view
            }
        }

    except Exception as e:
        print(f"Forensics Failed: {e}")
        traceback.print_exc() 
        return {
            "status": "TAMPERED", 
            "message": f"Tampering detected, but forensic analysis failed: {str(e)}",
            "details": {
                "matched_id": target_ref_id, 
                "tamper_score": 100,
                "can_reconstruct": False
            }
        }