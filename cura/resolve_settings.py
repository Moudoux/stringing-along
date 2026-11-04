"""Resolve every Cura setting for Ender-3 (V2) + 0.4 nozzle + standard PETG quality + a
.curaprofile, the way the Cura front end does, and write CuraEngine `-s key=value` args.

usage: resolve_settings.py profile.curaprofile start_gcode.txt out_args.txt
"""
import configparser
import json
import math
import os
import sys
import zipfile

RES = os.environ["CURA_RESOURCES"]
profile_path, start_gcode_path, out_path = sys.argv[1:4]


def load_def(path):
    return json.load(open(path))


def flatten(node, out):
    for key, val in node.items():
        out[key] = dict(val)
        if "children" in val:
            flatten(val["children"], out)


# Base definitions (fdmprinter + fdmextruder), then the override chain on top.
defs = {}
for cat in load_def(f"{RES}/definitions/fdmprinter.def.json")["settings"].values():
    flatten(cat.get("children", {}), defs)
for cat in load_def(f"{RES}/definitions/fdmextruder.def.json")["settings"].values():
    flatten(cat.get("children", {}), defs)
for path in (
    f"{RES}/definitions/creality_base.def.json",
    f"{RES}/definitions/creality_ender3.def.json",
    f"{RES}/extruders/creality_base_extruder_0.def.json",
):
    for key, ov in load_def(path).get("overrides", {}).items():
        defs.setdefault(key, {}).update(ov)
        if "default_value" in ov and "value" not in ov:
            defs[key].pop("value", None)


def read_cfg_values(text):
    cp = configparser.ConfigParser(interpolation=None)
    cp.read_string(text)
    return dict(cp["values"]) if cp.has_section("values") else {}


# Instance layers, highest priority first.
layers = []
with zipfile.ZipFile(profile_path) as z:
    for name in z.namelist():
        layers.append(read_cfg_values(z.read(name).decode()))
user = {}
for layer in layers:
    user.update(layer)
user["machine_start_gcode"] = open(start_gcode_path).read()
user["material_bed_temp_prepend"] = "False"
user["material_print_temp_prepend"] = "False"
quality_ext = read_cfg_values(open(f"{RES}/quality/creality/base/base_0.4_PETG_standard.inst.cfg").read())
quality_glob = read_cfg_values(open(f"{RES}/quality/creality/base/base_global_standard.inst.cfg").read())
variant = read_cfg_values(open(f"{RES}/variants/creality/creality_base_0.4.inst.cfg").read())
instance_stack = [user, quality_ext, quality_glob, variant]


def convert(key, raw):
    typ = defs.get(key, {}).get("type", "str")
    if typ == "float":
        return float(raw)
    if typ == "int":
        return int(float(raw))
    if typ == "bool":
        return raw.strip().lower() == "true"
    if typ in ("[int]", "polygon", "polygons"):
        return eval(raw)
    return raw


cache, resolving = {}, set()


def evaluate(expr):
    env = {
        "math": math, "sqrt": math.sqrt, "log": math.log, "floor": math.floor, "ceil": math.ceil,
        "tan": math.tan, "cos": math.cos, "atan": math.atan, "radians": math.radians, "degrees": math.degrees,
        "extruderValue": lambda ext, k: get(k),
        "extruderValues": lambda k: [get(k)],
        "resolveOrValue": get,
        "defaultExtruderPosition": lambda: "0",
        "anyExtruderWithMaterial": lambda k: "0",
        "anyExtruderNrWithOrDefault": lambda k: "0",
        "valueFromContainer": lambda k, i=0: get(k),
        "valueFromExtruderContainer": lambda k, i=0: get(k),
    }

    class Names(dict):
        def __missing__(self, name):
            if name in defs:
                return get(name)
            raise KeyError(name)

    return eval(expr, env, Names())


def get(key):
    if key in cache:
        return cache[key]
    if key in resolving:
        raise RecursionError(key)
    resolving.add(key)
    try:
        for layer in instance_stack:
            if key in layer:
                raw = layer[key]
                val = evaluate(raw[1:]) if raw.startswith("=") else convert(key, raw)
                break
        else:
            d = defs[key]
            val = evaluate(d["value"]) if isinstance(d.get("value"), str) else d.get("value", d.get("default_value"))
    finally:
        resolving.discard(key)
    cache[key] = val
    return val


lines, failed = [], []
for key, d in defs.items():
    if d.get("type") == "category":
        continue
    try:
        val = get(key)
    except Exception as e:  # noqa: BLE001 - report and move on
        failed.append(f"{key}: {e!r}")
        continue
    if val is None:
        continue
    # Cura's front end fills this in, and the engine would pass it through as written.
    # Its own value, 235, is past this printer's Y limit of 231.
    if key == "machine_end_gcode":
        val = val.replace("{machine_depth}", "220")
    lines.append(f"{key}={val}")
open(out_path, "w").write("\0".join(lines))
print(f"resolved {len(lines)} settings, {len(failed)} failed")
for f in failed[:15]:
    print("  FAILED", f)
for k in ("wall_thickness", "wall_line_count", "line_width", "material_print_temperature",
          "retraction_amount", "cool_min_layer_time", "speed_wall_0", "top_layers", "infill_pattern",
          "retraction_combing", "small_feature_speed_factor"):
    print(f"  {k} = {cache.get(k)}")
