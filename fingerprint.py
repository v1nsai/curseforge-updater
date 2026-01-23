import struct
import sys

def murmur2_32(data, seed=1):
    m = 0x5bd1e995
    r = 24
    length = len(data)
    h = seed ^ length
    i = 0
    while length >= 4:
        k = struct.unpack_from("<I", data, i)[0]
        k = (k * m) & 0xFFFFFFFF
        k ^= k >> r
        k = (k * m) & 0xFFFFFFFF
        h = (h * m) & 0xFFFFFFFF
        h ^= k
        i += 4
        length -= 4
    if length == 3:
        h ^= data[i+2] << 16
    if length >= 2:
        h ^= data[i+1] << 8
    if length >= 1:
        h ^= data[i]
        h = (h * m) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * m) & 0xFFFFFFFF
    h ^= h >> 15
    return h & 0xFFFFFFFF

with open(sys.argv[1], "rb") as f:
    # CurseForge ignores whitespace characters: 0x9, 0xa, 0xd, 0x20
    content = f.read()
    filtered = bytearray(b for b in content if b not in [0x9, 0xa, 0xd, 0x20])
    print(murmur2_32(filtered))