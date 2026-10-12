import re, io, os, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "index.html")
DESTS = [
    os.path.join(ROOT, "android", "app", "src", "main", "assets", "index.html"),
    os.path.join(ROOT, "desktop", "index.html"),
]

with io.open(SRC, "r", encoding="utf-8", newline="") as f:
    s = f.read()

n = len(re.findall(r'\s+data-page-node-id="[^"]*"', s))
clean = re.sub(r'\s+data-page-node-id="[^"]*"', "", s)

with io.open(SRC, "w", encoding="utf-8", newline="") as f:
    f.write(clean)
for d in DESTS:
    with io.open(d, "w", encoding="utf-8", newline="") as f:
        f.write(clean)

print("stripped occurrences:", n)
for p in [SRC] + DESTS:
    b = io.open(p, "rb").read()
    print(" ", os.path.relpath(p, ROOT), len(b), "bytes  md5", hashlib.md5(b).hexdigest())
print("remaining tags in source:", len(re.findall(r'data-page-node-id', clean)))
