BLOCK_SIZE = 32

BLOCKCHAIN_PATH = "registry/blockchain.json"
BLOCK_STORAGE = "storage/blocks/"

VIDEO_FRAMES_PATH = "storage/video_frames"
import os

# =========================
# CONFIGURATION
# =========================

# Database Configuration
DB_NAME = "users.db"

# Storage Paths
BLOCK_STORAGE = "storage/blocks"
VIDEO_FRAMES_PATH = "storage/video_frames"

# NEW: Directory for Reconstructed Outputs (Fixes your error)
OUTPUTS_DIR = "outputs"

# Ensure directories exist
os.makedirs(BLOCK_STORAGE, exist_ok=True)
os.makedirs(VIDEO_FRAMES_PATH, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)