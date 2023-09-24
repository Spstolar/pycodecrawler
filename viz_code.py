from code_graph import create_function_call_edges, create_collapsed_function_call_edges


mermaid_keywords = ["map", "find"]
low_level_functions = [
    "range",
    "len",
    "max",
    "min",
    "sum",
    "all",
    "open",
    "dict",
    "set",
    "list",
    "print",
    "append",
    "isinstance",
    "reverse",
    "extend",
    "items",
    "keys",
    "values",
    "index",
    "map",
    "str",
    "enumerate",
    "type",
    "cls",
    "TypeError",
    "ValueError",
    "tuple",
    "reversed",
    "zip",
    "iter",
    "replace",
    "repr",
    "join",
    "split",
    "KeyError",
]

MAX_NODE_ID_LENGTH = 20


def sanitize_node_id(original_node_id, max_length=MAX_NODE_ID_LENGTH):
    node_id = original_node_id[:max_length]
    if node_id in mermaid_keywords:
        node_id = "py." + node_id

    if "end" in node_id.split("_"):
        # you can't have "end" in the flowchart https://github.com/mermaid-js/mermaid/issues/1444
        # the fix is just just capitalize at least one of the letters of "end"
        parts = node_id.split("_")
        updated_parts = [part.capitalize() if "end" in part else part for part in parts]
        node_id = "_".join(updated_parts)
    return node_id


def update_module_name_lookup(module_name, module_lookup_dict):
    node_id = sanitize_node_id(module_name)
    module_lookup_dict[module_name] = node_id


def create_graph_description(
    module_info,
    collapse_multiple_call_edges: bool = False,
    wanted_classes: list = None,
    include_body_commands: bool = True,
    include_function_defs: bool = True,
):
    """Use the parsed module info to create edges between functions defined and called
    in the module.

    Args:
        module_info (dict): module info parsed with dep_parser
        collapse_multiple_call_edges (bool, optional): Rather than have multiple edges between
        a single pair of nodes, only allow a single edge but apply an edge label to count
        the number of calls. Defaults to False.

    Returns:
        list: edge data
    """
    if collapse_multiple_call_edges:
        edges = create_collapsed_function_call_edges(
            module_info,
            wanted_classes=wanted_classes,
            include_body_commands=include_body_commands,
            include_function_defs=include_function_defs,
        )
    else:
        edges = create_function_call_edges(
            module_info,
            wanted_classes=wanted_classes,
            include_body_commands=include_body_commands,
            include_function_defs=include_function_defs,
        )

    # TODO: propagate this up
    class_data = get_class_subgraphs(module_info, wanted_classes=wanted_classes)
    submodule_data = get_module_subgraphs(module_info)
    non_trivial_edges = [
        e
        for e in edges
        if e[1]
        not in low_level_functions  # we will keep the edge if the source has a low-level name because it could be defining something common for a class, otherwise we exclude edges with low-level target names to reduce clutter
    ]
    return generate_desc(non_trivial_edges, other_content=[class_data, submodule_data])


def generate_desc(import_graph_edges: list, other_content: list = None):
    contents = []
    header = "```{mermaid}"
    figure_type = "graph LR;"
    footer = "```"
    contents.append(header)
    contents.append(figure_type)
    # TODO: this is no longer just module lookup, but a general node name lookup
    module_lookup = {}
    for e in import_graph_edges:
        if len(e) == 2:
            s, t = e
            s_name = module_lookup.get(s, "")
            t_name = module_lookup.get(t, "")
            if not s_name:
                update_module_name_lookup(s, module_lookup)
                s_name = module_lookup[s]
            if not t_name:
                update_module_name_lookup(t, module_lookup)
                t_name = module_lookup[t]
            edge_line = f"\t{s_name}[{s}] --> {t_name}[{t}];"
        if len(e) == 3:
            s, t, edge_data = e
            s_name = module_lookup.get(s, "")
            t_name = module_lookup.get(t, "")
            if not s_name:
                update_module_name_lookup(s, module_lookup)
                s_name = module_lookup[s]
            if not t_name:
                update_module_name_lookup(t, module_lookup)
                t_name = module_lookup[t]
            if edge_data == 1:
                edge_line = f"\t{s_name}[{s}] --> {t_name}[{t}];"
            else:
                edge_line = f"\t{s_name}[{s}] -->|{edge_data}| {t_name}[{t}];"

        contents.append(edge_line)

    if other_content:
        contents.extend(other_content)
    contents.append(footer)
    return "\n".join(contents)


def get_subgraph_header(imported_module):
    if imported_module.alias:
        header = f"subgraph {imported_module.alias}"
    else:
        header = f"subgraph {imported_module.module}"
    return header


def get_class_subgraphs(module, wanted_classes: list):
    class_list = module["class_list"]
    class_subgraphs = []
    for class_node in class_list:
        class_name = class_node.name
        if wanted_classes is not None and class_name not in wanted_classes:
            continue

        header = f"subgraph {class_node.name}"

        class_subgraph_methods = []
        for method in class_node.methods:
            node_id = f"{class_name}.{method.name}"
            node_id = sanitize_node_id(node_id)
            class_subgraph_methods.append("\t" + node_id)
        methods = "\n".join(class_subgraph_methods)
        footer = "end"
        class_subgraphs.append("\n".join([header, methods, footer]))
    return "\n".join(class_subgraphs)


def get_module_subgraphs(module):
    module_subgraphs = []
    collected = []
    module_lookup = {}
    module_import_list = module["import_list"]
    call_list = module["call_list"]
    function_call_list = [c for f in module["func_defs"] for c in f.calls]
    if not call_list:
        call_list = []
    if not function_call_list:
        function_call_list = []
    call_list.extend(function_call_list)
    for imported_module in module_import_list:
        header = get_subgraph_header(imported_module)
        functions = []
        for c in call_list:
            if c in collected:
                continue
            # collected.append(c)  # need to handle this better
            c_module = c.module
            # get the main module if using a submodule
            if isinstance(c_module, list) and c_module:
                c_main_module = c_module[0]
            else:
                c_main_module = c_module

            # if there wasn't a module then we do not need this call for the module subgraph
            if not c_main_module:
                continue

            module_name = ".".join(c_module)  # np.linalg
            full_node_name = module_name + "." + c.name  # np.linalg.norm
            node_name = module_lookup.get(full_node_name, "")
            if not node_name:
                update_module_name_lookup(full_node_name, module_lookup)
                node_name = module_lookup[full_node_name]

            # check if this call belongs to the module we are inspecting
            if (
                c_main_module == imported_module.module
                or c_main_module == imported_module.alias
            ):
                functions.append(node_name)

        # adding indentation
        functions = ["\t" + f for f in set(functions)]

        footer = "end"
        # only include the submodule description if it had functions!
        if functions:
            module_subgraphs.append("\n".join([header, *functions, footer]))
    return "\n".join(module_subgraphs)
