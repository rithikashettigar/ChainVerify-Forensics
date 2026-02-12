def compare_blocks(current_hashes, stored_hashes):
    """
    Compares two lists of hashes and identifies indices where they differ.
    Handles cases where the lists are of different lengths (resized/cropped images)
    to prevent 'list index out of range' errors.
    """
    tampered_indices = []
    
    # 1. Find the length of both lists
    len_curr = len(current_hashes)
    len_stored = len(stored_hashes)
    
    # 2. Compare the overlapping part (the safe range)
    # We only loop up to the length of the SHORTER list to avoid crashing.
    safe_limit = min(len_curr, len_stored)
    
    for i in range(safe_limit):
        if current_hashes[i] != stored_hashes[i]:
            tampered_indices.append(i)
            
    # 3. Handle Size Mismatch (Automatic Tampering)
    # If the incoming image is LARGER, all extra blocks are considered tampered
    if len_curr > len_stored:
        for i in range(len_stored, len_curr):
            tampered_indices.append(i)
            
    # If the incoming image is SMALLER (cropped), we mark the missing parts as tampered
    # (We add them to the list so the percentage score is accurate)
    elif len_stored > len_curr:
        for i in range(len_curr, len_stored):
            tampered_indices.append(i)

    # 4. Calculate Tamper Score
    # We divide by the LARGEST possible size to give a fair percentage
    total_blocks = max(len_curr, len_stored)
    
    if total_blocks == 0:
        percent = 0
    else:
        percent = (len(tampered_indices) / total_blocks) * 100
        
    return tampered_indices, percent