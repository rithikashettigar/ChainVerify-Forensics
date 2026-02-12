import hashlib

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def hash_block(block):
    return hashlib.sha256(block.tobytes()).hexdigest()
