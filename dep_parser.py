from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import ast
import inspect


common_functions_to_skip = [
    "append",
    "sum",
    "reverse",
    "extend",
    "keys",
    "items",
    "values",
]
# import builtins
# builtin_names = dir(builtins)
# add some additional ones add the top
builtin_names = [
    "append",
    "ArithmeticError",  # here down is from dir(builtins)
    "AssertionError",
    "AttributeError",
    "BaseException",
    "BlockingIOError",
    "BrokenPipeError",
    "BufferError",
    "BytesWarning",
    "ChildProcessError",
    "ConnectionAbortedError",
    "ConnectionError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "DeprecationWarning",
    "EOFError",
    "Ellipsis",
    "EnvironmentError",
    "Exception",
    "False",
    "FileExistsError",
    "FileNotFoundError",
    "FloatingPointError",
    "FutureWarning",
    "GeneratorExit",
    "IOError",
    "ImportError",
    "ImportWarning",
    "IndentationError",
    "IndexError",
    "InterruptedError",
    "IsADirectoryError",
    "KeyError",
    "KeyboardInterrupt",
    "LookupError",
    "MemoryError",
    "ModuleNotFoundError",
    "NameError",
    "None",
    "NotADirectoryError",
    "NotImplemented",
    "NotImplementedError",
    "OSError",
    "OverflowError",
    "PendingDeprecationWarning",
    "PermissionError",
    "ProcessLookupError",
    "RecursionError",
    "ReferenceError",
    "ResourceWarning",
    "RuntimeError",
    "RuntimeWarning",
    "StopAsyncIteration",
    "StopIteration",
    "SyntaxError",
    "SyntaxWarning",
    "SystemError",
    "SystemExit",
    "TabError",
    "TimeoutError",
    "True",
    "TypeError",
    "UnboundLocalError",
    "UnicodeDecodeError",
    "UnicodeEncodeError",
    "UnicodeError",
    "UnicodeTranslateError",
    "UnicodeWarning",
    "UserWarning",
    "ValueError",
    "Warning",
    "ZeroDivisionError",
    "__IPYTHON__",
    "__build_class__",
    "__debug__",
    "__doc__",
    "__import__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
    "abs",
    "all",
    "any",
    "ascii",
    "bin",
    "bool",
    "breakpoint",
    "bytearray",
    "bytes",
    "callable",
    "chr",
    "classmethod",
    "compile",
    "complex",
    "copyright",
    "credits",
    "delattr",
    "dict",
    "dir",
    "display",
    "divmod",
    "enumerate",
    "eval",
    "exec",
    "execfile",
    "filter",
    "float",
    "format",
    "frozenset",
    "get_ipython",
    "getattr",
    "globals",
    "hasattr",
    "hash",
    "help",
    "hex",
    "id",
    "input",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "license",
    "list",
    "locals",
    "map",
    "max",
    "memoryview",
    "min",
    "next",
    "object",
    "oct",
    "open",
    "ord",
    "pow",
    "print",
    "property",
    "range",
    "repr",
    "reversed",
    "round",
    "runfile",
    "set",
    "setattr",
    "slice",
    "sorted",
    "staticmethod",
    "str",
    "sum",
    "super",
    "tuple",
    "type",
    "vars",
    "zip",
]


@dataclass
class ImportNode:
    module: str  # module name of the import
    function_names: list  # functions brought it
    level: int  # data to track use of submodules
    alias: str = ""  # alias name if used, e.g. "np" when `import numpy as np`


def walk_script(filename: str):
    """Read the provided Python file and return the walked parse tree.

    Args:
        filename (str): Python filename

    Returns:
        list: ast node list
    """
    worker_script = open(filename, "r")
    parsed_worker = ast.parse(worker_script.read())
    walked_worker = ast.walk(parsed_worker)
    work_w = list(walked_worker)
    return work_w


def get_submodule_desc(value):
    """Extract the list of nested submodules provided an ast Attribute or Name node.

    Args:
        value (ast.Attribute): ast Attribute or Name node

    Returns:
        list[str]: list of module names in the submodule function call
    """
    module_call = []
    if isinstance(value, ast.Attribute):
        module_call.append(value.attr)
        module_call.extend(get_submodule_desc(value.value))
    elif isinstance(value, ast.Name):
        module_call.append(value.id)
    return module_call


def process_from_import_node(node: ast.ImportFrom) -> ImportNode:
    """Return descriptor of ImportFrom node. The difference here is that functions
    are explicitly named in the import.

    Args:
        node (ast.ImportFrom): ast ImportFrom node

    Returns:
        ImportNode: import data
    """
    return ImportNode(
        module=node.module,
        function_names=[f.name for f in node.names],
        level=node.level,
    )


def process_import_node(node: ast.Import) -> ImportNode:
    """Extract data from import node.

    Args:
        node (ast.Import): ast node for basic import

    Returns:
        ImportNode: import data
    """
    node_data = node.names[0]
    return ImportNode(
        module=node_data.name, function_names=[], alias=node_data.asname, level=-1
    )


@dataclass
class CallNode:
    module: str  # what module does the called function belong to
    name: str  # function name
    call_lineno: int  # where was the call
    called_by: str = None  # what was the caller


def print_call_node_info(node):
    func_data = node.func
    print(node)
    print(func_data)
    if isinstance(func_data, ast.Attribute):
        print(node.func.value)
        print(node.func.attr)
    print("-" * 80)


def process_call_node(node: ast.Call, called_by=None, verbose: bool = False):
    """Extract function call data from a call node.

    Args:
        node (ast.Call): ast call node
        verbose (bool, optional): print information about the function. Defaults to False.

    Returns:
        CallNode: data about the call
    """
    func_data = node.func
    if verbose:
        print_call_node_info(node)

    if isinstance(func_data, ast.Attribute):
        function_name = func_data.attr
        value = func_data.value
        submodule_desc = get_submodule_desc(value)
        submodule_desc.reverse()

        call_node = CallNode(
            module=submodule_desc, name=function_name, call_lineno=node.lineno
        )
    elif isinstance(func_data, ast.Name):
        call_node = CallNode(
            name=func_data.id,
            module=[],  # the module is provided in the imports or this function is defined in this script
            call_lineno=node.lineno,
        )
    else:
        print("error")
        print(node)
        return None

    # we want to avoid creating nodes for things like `some_list.append(item)`
    # this makes it so that we aren't treating some_list like a model so the
    # edges to this call will eventually be skipped
    if call_node.name in common_functions_to_skip:
        call_node.module = []
    call_node.called_by = called_by
    return call_node


@dataclass
class FuncDefNode:
    name: str  # name of the function
    module: str  # what module the function belongs to
    defined_in: str  # what module the function belongs to
    start_lineno: int  # where does the definition start
    end_lineno: int  # where does the definition stop
    calls: list  # what functions are called in the definition


def process_func_def_node(node: ast.FunctionDef, module_name=None, defined_in=None):
    return FuncDefNode(
        name=node.name,
        module=module_name,
        defined_in=defined_in,
        start_lineno=node.lineno,
        end_lineno=node.end_lineno,
        calls=[],
    )

@dataclass
class ClassNode:
    name: str
    module: str
    methods: list

def process_class_node(node: ast.ClassDef, module_name=None, methods=None):
    return ClassNode(
        name=node.name,
        module=module_name,
        methods=methods,
    )

# TODO: may need to use this instead depending on how to handle class data
def process_class_func_node(node: ast.FunctionDef, class_name=None):
    return FuncDefNode(
        name=node.name,
        module=class_name,
        start_lineno=node.lineno,
        end_lineno=node.end_lineno,
        calls=[],
    )


def add_call_or_import(node, call_list, import_list):
    """Determine if the note is an import or call, parse, and add to the
    corresponding list.

    Args:
        node (ast.AST): node to parse
        call_list (list): list of call data
        import_list (list): list of import data
    """
    if isinstance(node, ast.Import):
        import_list.append(process_import_node(node))
    elif isinstance(node, ast.ImportFrom):
        import_list.append(process_from_import_node(node))
    elif isinstance(node, ast.Call):
        call_data = process_call_node(node)
        if not call_data.module and call_data.name not in builtin_names:
            for import_node in import_list:
                if call_data.name in import_node.function_names:
                    call_data.module = [import_node.module]
                    break
        call_list.append(call_data)


def walk_node_children(node):
    """Return all children of the provided node.

    Args:
        node (ast.AST): node to walk

    Returns:
        list: list of child nodes
    """
    return list(ast.walk(node))


def process_class_function_def(node, context_name):
    class_method_def = process_func_def_node(node, context_name, defined_in=context_name)
    return class_method_def

def process_class_methods(node):
    class_name = node.name
    class_body = node.body
    class_methods = []
    # this should mostly be class methods
    for body_node in class_body:
        if isinstance(body_node, ast.FunctionDef):
            method = process_class_function_def(body_node, class_name)
            class_methods.append(method)
    return class_methods


def process_func_def_children(
    node: ast.AST,
    func_def: FuncDefNode,
    module_func_defs: list,
    call_list: list,
    import_list: list,
):
    # we have already parsed the top level function def node, so we use walk on each node in the
    # body and combine them to get all of the children. It is likely easier to do walk_node_children[1:]
    # but that feels a little less transparent.
    # node_children = walk_node_children(node)[1:]
    node_children = [
        grandchild for child in node.body for grandchild in walk_node_children(child)
    ]
    for child in node_children:
        if isinstance(child, ast.FunctionDef):
            # TODO: this will be a helper function, which we may want to handle differently
            # for now we just add the function name to the helper function's `.module`
            helper_function_module = func_def.module + func_def.name
            helper_function = process_func_def_node(child, helper_function_module, defined_in=func_def.name)
            module_func_defs.append(helper_function)
        else:
            if not isinstance(node, ast.Call):
                # we no longer want to add calls to the module call list when they are called in function definitions, but
                # we do want to continue adding imports
                add_call_or_import(child, [], import_list)
            if isinstance(child, ast.Call):
                call_data = process_call_node(child, func_def.name)

                if not call_data.module and call_data.name not in builtin_names:
                    for import_node in import_list:
                        if call_data.name in import_node.function_names:
                            call_data.module = [import_node.module]
                            break
                func_def.calls.append(call_data)


def process_node_children(node, context_name, func_defs, call_list, import_list):
    """Walk all children of the node and process them.

    Args:
        node (ast.AST): node to process
        context_name (str): the class name if this node was a member of a class, otherwise the module name
        func_defs (list): function definitions
        call_list (list): calls
        import_list (list): imports
    """
    # context_name - either the current module name or the class name
    node_children = walk_node_children(node)
    if isinstance(node, ast.FunctionDef):
        func_defs.append(process_func_def_node(node, context_name))
        # TODO: handle the children of the node and avoid duplicating their parsing next
    for child in node_children:
        add_call_or_import(child, call_list, import_list)




def parse_module_node(module_node: ast.Module, current_module_name=None, verbose=False):
    """Crawl the children of the module node and extract code structure data."""

    class_list = []
    func_defs = []
    import_list = []
    call_list = []

    module_body = module_node.body
    for node in module_body:
        if isinstance(node, ast.ClassDef):
            # we handle classes differently because we want to attach data about the class to its elements
            class_methods = process_class_methods(node)
            class_data = process_class_node(node, methods=class_methods)
            class_list.append(class_data)
        elif isinstance(node, ast.FunctionDef):
            function_def = process_func_def_node(node, current_module_name)
            if verbose:
                print("Function definition:", function_def.name)
            process_func_def_children(
                node,
                function_def,
                module_func_defs=func_defs,
                call_list=call_list,
                import_list=import_list,
            )
            func_defs.append(function_def)
        else:
            # otherwise, this should be an import or a function definition, unless there is work performed in the script
            process_node_children(
                node,
                current_module_name,
                func_defs=func_defs,
                call_list=call_list,
                import_list=import_list,
            )

    return import_list, call_list, func_defs, class_list


def append_module_info_to_call_list(
    call_list: list, func_defs: list, import_list: list, current_module_name: str
):
    # deprecated
    # free-standing function calls
    for call in call_list:
        if call.module is None:
            if call.module in [f.name for f in func_defs]:
                call.module = current_module_name
            else:
                for module in import_list:
                    if call.name in module.function_names:
                        call.module = module.module
    return call_list


def append_func_calls_to_defs(func_defs: list, call_list: list):
    # Deprecated: don't want to depend on the line numbers
    # attach function calls to function defs
    for f_def in func_defs:
        for call in call_list:
            lineno = call.call_lineno
            if lineno >= f_def.start_lineno and lineno <= f_def.end_lineno:
                call.called_by = f_def.name
                f_def.calls.append(call)


def manage_module_imports(import_list: list):
    # handle duplicate module imports
    module_dict = defaultdict(list)
    for module in import_list:
        module_dict[module.module].append(module)
    deduplicated_import_list = []
    for same_module_imports in module_dict.values():
        if len(same_module_imports) == 1:
            deduplicated_import_list.append(same_module_imports[0])
        else:
            module_name = same_module_imports[0].module
            function_name_lists = [m.function_names for m in same_module_imports]
            aliases = list(set([m.alias for m in same_module_imports if m.alias]))
            levels = [m.level for m in same_module_imports]

            if len(aliases) == 1:
                alias = aliases[0]
            elif len(aliases) > 1:
                alias = aliases
            else:
                alias = None

            deduped_node = ImportNode(
                module=module_name,
                function_names=list(set([i for l in function_name_lists for i in l])),
                alias=alias,
                level=max(levels),
            )
            deduplicated_import_list.append(deduped_node)
    return deduplicated_import_list


def get_walked_scripted_from_filename(filename: str):
    """Open the file and use ast to return the walked syntax tree.

    Args:
        filename (str): file to parse

    Returns:
        list: list of all ast nodes
    """
    path = Path(filename)
    work_w = walk_script(path)
    return work_w


def get_top_level_node_from_filename(filename: Path):
    """Open the file, use ast to parse it, and return the top-level module node.

    Args:
        filename (Path): script path

    Returns:
        ast.Module: top-level module node of the script
    """
    script_contents = open(filename, "r")
    module = ast.parse(script_contents.read())
    return module


# main method
def extract_node_structure_from_script(filename: str, verbose=False):
    """Extract data from the provided script.

    Args:
        filename (str): script file name
        verbose (bool): print more information about process

    Returns:
        list: collections of code data
    """
    path = Path(filename)
    # a module's name is exactly the stem of the file name
    current_module_name = path.stem
    if verbose:
        print(f"Extracting info from {current_module_name}.")

    # we start by parsing to get the top level module object
    module_node = get_top_level_node_from_filename(path)

    # TODO: decide how to use the class data
    import_list, call_list, func_defs, class_list = parse_module_node(
        module_node, current_module_name, verbose=verbose
    )

    # TODO: may no longer be needed
    # call_list = append_module_info_to_call_list(
    #     call_list=call_list,
    #     import_list=import_list,
    #     func_defs=func_defs,
    #     current_module_name=current_module_name,
    # )
    deduplicated_import_list = manage_module_imports(import_list)

    # TODO: option for non-deduped call list in order to provide cleanup suggestions
    return deduplicated_import_list, call_list, func_defs, class_list
