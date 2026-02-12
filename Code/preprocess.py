import numpy as np
from PIL import Image
from config import BLOCK_SIZE

def load_grayscale(path):
    img = Image.open(path).convert("L")
    return np.array(img)

def slice_blocks(img):
    blocks = []
    h, w = img.shape

    for y in range(0, h, BLOCK_SIZE):
        for x in range(0, w, BLOCK_SIZE):
            block = img[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE]
            blocks.append(((y, x), block))

    return blocks
