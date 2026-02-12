import hashlib

def merkle_root(hashes):
    if not hashes:
        return None

    while len(hashes) > 1:
        temp = []
        for i in range(0, len(hashes), 2):
            left = hashes[i]
            right = hashes[i+1] if i+1 < len(hashes) else left
            temp.append(
                hashlib.sha256((left + right).encode()).hexdigest()
            )
        hashes = temp

    return hashes[0]
