# Compute SHA-256 of a given file
import sys, hashlib

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python compute_hash.py <path-to-file>')
        sys.exit(1)
    print(sha256_of(sys.argv[1]))
