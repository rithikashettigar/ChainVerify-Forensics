import hashlib

def hash_frame(frame_path):
    with open(frame_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()
