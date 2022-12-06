"""Generate the code reference pages."""
from pathlib import Path

import mkdocs_gen_files


nav = mkdocs_gen_files.Nav()

project_path = "../watervize/watervize/assets/"

for path in sorted(Path(project_path).rglob("*.py")):  # 
    module_path = path.relative_to(project_path).with_suffix("")  # 
    doc_path = path.relative_to(project_path).with_suffix(".md")  # 
    full_doc_path = Path("reference", doc_path)  # 

    print(f"module_path: {module_path} ({module_path.resolve()})")
    print(f"doc_path: {doc_path} ({doc_path.resolve()})")
    print(f"full_doc_path: {full_doc_path} ({full_doc_path.resolve()})")

    parts = list(module_path.parts)

    print(f"parts (before): {parts}")

    if parts[-1] == "__init__":  # 
        parts = parts[:-1]
    elif parts[-1] == "__main__":
        continue
    
    print(f"parts (after): {parts}")
    print()

    if len(parts) > 0:
        nav[parts] = doc_path.as_posix()

    # with mkdocs_gen_files.open(full_doc_path, "w") as fd:  # 
    #     identifier = ".".join(parts)  # 
    #     print("::: " + identifier, file=fd)  # 

    # mkdocs_gen_files.set_edit_path(full_doc_path, path)

    print(f"mkdocs_gen_files path: {full_doc_path, path}")