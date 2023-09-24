import os
from pathlib import Path
from dep_parser import extract_node_structure_from_script


def get_python_filenames_from_dir(dir):
    """Find all `.py` files in the current directory, ignoring Jupyter detritus.

    Args:
        dir (str): directory name

    Returns:
        list: list of all Python script (relative) filenames
    """
    python_filenames = []
    for root, dirs, files in os.walk(dir):
        root = Path(root)
        if root.stem == ".ipynb_checkpoints":
            continue
        for file in files:
            file = Path(file)
            if file.suffix == ".py":
                python_filenames.append(root / file)
    return python_filenames


def get_all_filenames(directories: list = None, other_python_filenames=None):
    """For each directory in the directories list and each other separately specified
    file name, create a combined lists of Python script filenames.

    Args:
        directories (list): Python directory strings
        other_python_filenames (list, optional): list of separate Python filenames. Defaults to None.

    Returns:
        list: combined list of all Python filenames
    """
    if directories is None:
        directories = []
    filenames = [f for d in directories for f in get_python_filenames_from_dir(d)]
    if other_python_filenames:
        if isinstance(other_python_filenames, str):
            filenames.append(Path(other_python_filenames))
        else:
            filenames.extend([Path(f) for f in other_python_filenames])
    return filenames


def extract_code_information(
    directories: list = None, other_python_filenames=None, verbose=False
):
    """For each Python file in the directories provided as well as the other filename
    list, extract the node structure and create an overall module info dict.

    Args:
        directories (list): Python directory strings
        other_python_filenames (list, optional): list of separate Python filenames. Defaults to None.
        verbose (bool): print more information about process

    Returns:
        dict: module information
    """
    python_filenames = get_all_filenames(directories, other_python_filenames)
    if python_filenames is None:
        print("no code found")
        return {}
    module_info = {}
    for f in python_filenames:
        module_name = f.stem

        (
            import_list,
            call_list,
            func_defs,
            class_list,
        ) = extract_node_structure_from_script(f, verbose=verbose)
        module_info[module_name] = {
            "import_list": import_list,
            "call_list": call_list,
            "func_defs": func_defs,
            "class_list": class_list,
        }
    return module_info
