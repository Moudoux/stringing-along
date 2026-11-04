"""Fill in the real print time and filament length in a CuraEngine CLI G-code header."""
import re
import sys

path = sys.argv[1]
lines = open(path).read().split("\n")
total = e = 0.0
elapsed = 0.0
for line in lines:
    if line.startswith("G92") and " E" in line:
        e = float(re.search(r"E([-\d.]+)", line)[1])
    elif line.startswith(("G0", "G1")):
        m = re.search(r" E([-\d.]+)", line)
        if m:
            ne = float(m[1]); total += max(0.0, ne - e); e = ne
    if line.startswith(";TIME_ELAPSED:"):
        elapsed = float(line[14:])
out = []
for line in lines:
    if line.startswith(";TIME:"):
        line = f";TIME:{int(elapsed)}"
    elif line.startswith(";Filament used:"):
        line = f";Filament used: {total/1000:.2f}m"
    out.append(line)
open(path, "w").write("\n".join(out))
print(f"{path.split('/')[-1]}: {int(elapsed//3600)}h{int(elapsed%3600//60):02d}m, {total/1000:.1f} m filament")
