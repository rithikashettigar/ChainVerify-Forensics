import os
import pickle
import numpy as np
from PIL import Image, ImageDraw
from config import BLOCK_SIZE, BLOCK_STORAGE

def recover_image(base_img_pil, tampered_indices, block_positions, stored_hashes):
    """
    Generates TWO images:
    1. Forensic Image: Red boxes highlighting suspicious areas.
    2. Reconstructed Image: A grayscale restoration using authentic blocks + backup storage.
    """
    
    # --- A. PREPARE IMAGES ---
    # 1. Forensic (RGB for Red Boxes)
    forensic_img = base_img_pil.convert("RGB")
    draw = ImageDraw.Draw(forensic_img)
    
    # 2. Reconstructed (Grayscale Canvas)
    # We start with a blank black canvas of the same size
    width, height = base_img_pil.size
    reconstructed_array = np.zeros((height, width), dtype=np.uint8)
    
    # We need the base image as a numpy array to copy valid pixels
    base_img_gray = base_img_pil.convert("L")
    base_pixels = np.array(base_img_gray)

    # --- B. PROCESS BLOCKS ---
    print(f"--- RECOVERING: {len(tampered_indices)} blocks tampered ---")

    # Set of tampered indices for fast lookup
    tampered_set = set(tampered_indices)
    
    for idx, (y, x) in enumerate(block_positions):
        # Calculate block bounds
        y_end = min(y + BLOCK_SIZE, height)
        x_end = min(x + BLOCK_SIZE, width)
        
        # LOGIC 1: AUTHENTIC BLOCK (Copy from Input)
        if idx not in tampered_set:
            # If the block is valid, we trust the input pixels
            block_h = y_end - y
            block_w = x_end - x
            
            # Safe copy (handling edge cases)
            if y < base_pixels.shape[0] and x < base_pixels.shape[1]:
                reconstructed_array[y:y_end, x:x_end] = base_pixels[y:y_end, x:x_end]
                
        # LOGIC 2: TAMPERED BLOCK (Forensics & Restoration)
        else:
            # 2a. Forensic View: Draw Red Box
            draw.rectangle([x, y, x + BLOCK_SIZE, y + BLOCK_SIZE], outline="#ff0000", width=2)
            draw.line([x, y, x + BLOCK_SIZE, y + BLOCK_SIZE], fill="#ff0000", width=1)
            
            # 2b. Reconstructed View: Try to Load from Storage (Old Model)
            restored = False
            if idx < len(stored_hashes):
                block_hash = stored_hashes[idx]
                block_path = os.path.join(BLOCK_STORAGE, block_hash)
                
                if os.path.exists(block_path):
                    try:
                        with open(block_path, "rb") as f:
                            saved_block = pickle.load(f)
                            # Ensure shape matches current slot
                            h_s, w_s = saved_block.shape
                            reconstructed_array[y:y+h_s, x:x+w_s] = saved_block
                            restored = True
                    except:
                        pass # File corrupted? Leave black.
            
            # If we couldn't restore it, it stays BLACK (The "Void" of Truth)
            if not restored:
                pass 

    # --- C. RETURN BOTH ---
    return np.array(forensic_img), reconstructed_array