"""Slice STLs with CuraEngine using fully resolved settings.

usage: slice.py settings.nul out.gcode model.stl [model.stl ...]
"""
import os
import subprocess
import sys

RES = "/opt/ultimaker-cura/share/cura/resources"
settings_path, out, models = sys.argv[1], sys.argv[2], sys.argv[3:]
settings = [s for s in open(settings_path).read().split("\0") if s]
set_args = [a for s in settings for a in ("-s", s)]

cmd = ["/lib64/ld-linux-x86-64.so.2", "/opt/ultimaker-cura/CuraEngine", "slice",
       "-j", f"{RES}/definitions/creality_ender3.def.json", *set_args,
       "-e0", "-j", f"{RES}/extruders/creality_base_extruder_0.def.json", *set_args]
for m in models:
    cmd += ["-l", m]
cmd += ["-o", out]
env = dict(os.environ, LD_LIBRARY_PATH="/opt/ultimaker-cura",
           CURA_ENGINE_SEARCH_PATH=f"{RES}/definitions:{RES}/extruders")
res = subprocess.run(cmd, env=env, capture_output=True, text=True)
errors = [l for l in (res.stdout + res.stderr).splitlines() if "[error]" in l or "[critical]" in l]
print("exit", res.returncode)
print("\n".join(errors[:10]))
