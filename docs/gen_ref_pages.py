"""Generate the code reference pages."""
import logging


from pathlib import Path

import mkdocs_gen_files

logger = logging.getLogger("mkdocs")


nav = mkdocs_gen_files.Nav()

project_path = "./flexible_list_of_values/"

logger.debug("STARTING GEN_REF_PAGES")
logger.debug(f"Path(project_path).resolve(): {Path(project_path).resolve()}")
logger.debug(f"sorted(Path(project_path).rglob('*.py')): {sorted(Path(project_path).rglob('*.py'))}")

ignore_list = ["/migrations/",]

for path in sorted(Path(project_path).rglob("*.py")):  # 
    if not any(substring in str(path) for substring in ignore_list):
        module_path = path.relative_to(project_path).with_suffix("")  # 
        doc_path = path.relative_to(project_path).with_suffix(".md")  # 
        full_doc_path = Path("reference", doc_path)  # 

        logger.debug(f"path: {module_path} ({path.resolve()})")
        logger.debug(f"module_path: {module_path} ({module_path.resolve()})")
        logger.debug(f"doc_path: {doc_path} ({doc_path.resolve()})")
        logger.debug(f"full_doc_path: {full_doc_path} ({full_doc_path.resolve()})")

        parts = list(module_path.parts)

        logger.debug(f"parts (before): {parts}")

        if parts[-1] == "__init__":  # 
            parts = parts[:-1]
        elif parts[-1] == "__main__":
            continue

        logger.debug(f"parts (after): {parts}")
        logger.debug("")
            
        if len(parts) > 0:
            nav[parts] = doc_path.as_posix()

            with mkdocs_gen_files.open(full_doc_path, "w") as fd:  # 
                identifier = ".".join(parts)  # 
                if not identifier == "" or identifier == " ":
                    print("::: " + "flexible_list_of_values." + identifier, file=fd)  # 

            mkdocs_gen_files.set_edit_path(full_doc_path, path)

            logger.debug(f"mkdocs_gen_files path: {full_doc_path, path}")

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:  # 
    nav_file.writelines(nav.build_literate_nav())  # 
