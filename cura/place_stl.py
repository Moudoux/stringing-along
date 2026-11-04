"""Copy a binary STL, moved so it sits on Z=0 centred at (cx, cy)."""
import struct
import sys

src, dst, cx, cy = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
data = open(src, "rb").read()
count = struct.unpack_from("<I", data, 80)[0]
tris = [struct.unpack_from("<12fH", data, 84 + i * 50) for i in range(count)]
xs = [t[j] for t in tris for j in (3, 6, 9)]
ys = [t[j] for t in tris for j in (4, 7, 10)]
zs = [t[j] for t in tris for j in (5, 8, 11)]
dx = cx - (min(xs) + max(xs)) / 2
dy = cy - (min(ys) + max(ys)) / 2
dz = -min(zs)
out = bytearray(data[:84])
for t in tris:
    v = list(t[:12])
    for j in (3, 6, 9):
        v[j] += dx
        v[j + 1] += dy
        v[j + 2] += dz
    out += struct.pack("<12fH", *v, t[12])
open(dst, "wb").write(out)
print(f"size {max(xs)-min(xs):.1f} x {max(ys)-min(ys):.1f} x {max(zs)-min(zs):.1f} mm")
