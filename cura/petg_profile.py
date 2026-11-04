"""Build an Ender 3 V2 PETG .curaprofile and the matching CuraEngine CLI args."""
import json
import sys
import zipfile

RES = "/opt/ultimaker-cura/share/cura/resources"
OUT_DIR = sys.argv[1]
PROFILE_NAME = "Ender 3 V2 PETG"

SETTINGS = {
    # Layers / adhesion / support
    "layer_height": "0.2",
    "layer_height_0": "0.2",
    "adhesion_type": "skirt",
    "support_enable": "False",
    # Temperatures
    "material_print_temperature": "230",
    "material_print_temperature_layer_0": "235",
    "material_bed_temperature": "75",
    "material_bed_temperature_layer_0": "80",
    # Cooling: off for first layer, moderate after, more on small/fast layers
    "cool_fan_enabled": "True",
    "cool_fan_speed_0": "0",
    "cool_fan_speed_min": "40",
    "cool_fan_speed_max": "70",
    "cool_min_layer_time_fan_speed_max": "15",
    "cool_min_layer_time": "12",
    "cool_min_speed": "8",
    "cool_lift_head": "False",
    # Retraction (stock Bowden)
    "retraction_enable": "True",
    "retraction_amount": "6",
    "retraction_speed": "45",
    "wall_0_wipe_dist": "0.2",
    "retraction_hop_enabled": "False",
    "retraction_combing": "noskin",
    "travel_avoid_other_parts": "True",
    # Speeds (mm/s)
    "speed_print": "45",
    "speed_wall_0": "25",
    "speed_wall_x": "40",
    "speed_topbottom": "35",
    "speed_infill": "50",
    "speed_layer_0": "20",
    "speed_travel": "150",
    "small_feature_max_length": "20",
    "small_feature_speed_factor": "40",
    # Strength
    "wall_line_count": "3",
    "top_layers": "5",
    "bottom_layers": "4",
    "infill_sparse_density": "20",
    "infill_pattern": "gyroid",
    "z_seam_type": "sharpest_corner",
}


def flatten(node, out):
    for key, val in node.items():
        out[key] = val
        if "children" in val:
            flatten(val["children"], out)


all_settings = {}
fdm = json.load(open(f"{RES}/definitions/fdmprinter.def.json"))
for cat in fdm["settings"].values():
    flatten(cat.get("children", {}), all_settings)

global_vals, extruder_vals = {}, {}
for key, value in SETTINGS.items():
    if key not in all_settings:
        sys.exit(f"unknown setting: {key}")
    per_extruder = all_settings[key].get("settable_per_extruder", True)
    (extruder_vals if per_extruder else global_vals)[key] = value


def inst_cfg(values, extruder):
    lines = [
        "[general]",
        "version = 4",
        f"name = {PROFILE_NAME}",
        "definition = creality_ender3",
        "",
        "[metadata]",
        "type = quality_changes",
        "quality_type = standard",
        "setting_version = 27",
    ]
    if extruder:
        lines.append("position = 0")
    lines += ["", "[values]"] + [f"{k} = {v}" for k, v in values.items()] + [""]
    return "\n".join(lines)


with zipfile.ZipFile(f"{OUT_DIR}/Ender3V2_PETG.curaprofile", "w") as z:
    z.writestr("creality_ender3_ender_3_v2_petg", inst_cfg(global_vals, False))
    z.writestr("creality_base_extruder_0_#2_ender_3_v2_petg", inst_cfg(extruder_vals, True))

# CuraEngine CLI args: -s before -e0 are global, after are extruder 0
args = [f"-s{k}={v}" for k, v in global_vals.items()]
args += ["-e0"] + [f"-s{k}={v}" for k, v in extruder_vals.items()]
open(f"{OUT_DIR}/engine_args.txt", "w").write("\n".join(args) + "\n")
print("global:", sorted(global_vals))
print("extruder:", len(extruder_vals), "settings")
