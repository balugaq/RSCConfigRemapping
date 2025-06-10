import os
import sys
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

if sys.version_info[0] == 3:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

def log_change(old_material: str, new_material: str) -> None:
    print(old_material + " -> " + new_material)

def processMaterial(material: str) -> str | None:
    if not isinstance(material, str):
        return None
        
    if "|" in material:
        original_parts = {part.strip() for part in material.replace(" ", "").split("|") if part.strip()}
        result_set = set(original_parts)
        added_elements = False
        
        for part in original_parts:
            if part in mapping:
                for item in mapping[part]:
                    if item not in original_parts:
                        result_set.add(item)
                        added_elements = True
        
        if added_elements:
            v = " | ".join(sorted(result_set))
            log_change(material, v)
            return v
        else:
            return None
    else:
        if material in mapping:
            mapped_items = set(mapping[material])
            if mapped_items != {material}:
                v = " | ".join(sorted(mapped_items))
                log_change(material, v)
                return v
        return None

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 32768
yaml.indent(mapping=2, sequence=4, offset=2)

mapping = {}
script_dir = Path(__file__).parent
fix_yml_path = script_dir / "mappings.yml"

if fix_yml_path.exists():
    try:
        yaml_fix = YAML()
        with open(fix_yml_path, "r", encoding="utf-8") as f:
            fix_data = yaml_fix.load(f) or {}
            for class_name, materials in fix_data.items():
                if isinstance(materials, (list, CommentedSeq)):
                    for material in materials:
                        if isinstance(material, str):
                            mapping[material] = materials
    except Exception as e:
        print(f"加载mappings.yml失败: {e}")
else:
    print(f"警告: 未找到mappings.yml文件 ({fix_yml_path})")

def process_dict(data, parent=None, key=None):
    modified = False
    if isinstance(data, (dict, CommentedMap)):
        if "material" in data and data.get("material_type") == "slimefun":
            original = data["material"]
            if isinstance(original, str):
                processed = processMaterial(original)
                if processed is not None and processed != original:
                    data["material"] = processed
                    modified = True

        for k, v in list(data.items()):
            if process_dict(v, data, k):
                modified = True
                
    elif isinstance(data, (list, CommentedSeq)):
        for item in data:
            if process_dict(item, data, None):
                modified = True
                
    return modified

def process_yml_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.load(f)
        
        modified = process_dict(data)
        
        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f)
            return True
        return False
    
    except Exception as e:
        print(f"无法处理文件失败 {file_path}: {e}")
        return False

addons_dir = script_dir / "addons"
processed_count = 0
modified_count = 0

if addons_dir.exists():
    for root, dirs, files in os.walk(addons_dir):
        if "saveditems" in root.split(os.sep) or "scripts" in root.split(os.sep):
            dirs[:] = []
            continue
        
        for file in files:
            if file.lower().endswith((".yml", ".yaml")):
                file_path = Path(root) / file
                if process_yml_file(file_path):
                    print(f"已修改: {file_path}")
                    modified_count += 1
                processed_count += 1
    
    print(f"\n共处理 {processed_count} 个文件，修改了 {modified_count} 个文件")
else:
    print(f"未找到addons目录 ({addons_dir})")