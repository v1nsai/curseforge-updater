import sys
import murmurhash2

with open(sys.argv[1], "rb") as f:
    # CurseForge ignores whitespace characters: 0x9, 0xa, 0xd, 0x20
    content = f.read()
    filtered = bytearray(b for b in content if b not in [0x9, 0xa, 0xd, 0x20])
    print(murmurhash2.murmurhash2(bytes(filtered), seed=1))