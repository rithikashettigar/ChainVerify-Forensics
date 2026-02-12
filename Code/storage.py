'''# core/storage.py
import os
import pickle
from config import IPFS_PATH

os.makedirs(IPFS_PATH, exist_ok=True)

def store_block(block_hash, block):
    path = IPFS_PATH + block_hash
    if not os.path.exists(path):
        with open(path, "wb") as f:
            pickle.dump(block, f)

def fetch_block(block_hash):
    with open(IPFS_PATH + block_hash, "rb") as f:
        return pickle.load(f)
'''