import json
import os
from config import BLOCKCHAIN_PATH

def load_chain():
    if not os.path.exists(BLOCKCHAIN_PATH):
        return {}
    with open(BLOCKCHAIN_PATH, "r") as f:
        return json.load(f)

def save_chain(data):
    with open(BLOCKCHAIN_PATH, "w") as f:
        json.dump(data, f, indent=2)

def register_reference(ref_id, data):
    chain = load_chain()
    chain[ref_id] = data
    save_chain(chain)

def get_reference(ref_id):
    return load_chain().get(ref_id)
