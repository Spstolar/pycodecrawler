from code_graph import create_function_call_edges, create_collapsed_function_call_edges


mermaid_keywords = ["map", "find"]
low_level_functions = [
    "range",
    "len",
    "max",
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
    "values"
]


def update_module_name_lookup(module_name, module_lookup_dict):
    if len(module_name) > 20:
        module_lookup_dict[module_name] = module_name[:20]
    elif module_name in mermaid_keywords:
        module_lookup_dict[module_name] = "py." + module_name
    else:
        module_lookup_dict[module_name] = module_name


def create_graph_description(module_info, collapse_multiple_call_edges: bool = False):
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
        edges = create_collapsed_function_call_edges(module_info)
    else:
        edges = create_function_call_edges(module_info)
    submodule_data = get_module_subgraphs(module_info)
    non_trivial_edges = [e for e in edges if e[0] not in low_level_functions and e[1] not in low_level_functions]
    return generate_desc(non_trivial_edges, other_content=submodule_data)


def generate_desc(import_graph_edges: list, other_content: str = None):
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
        contents.append(other_content)
    contents.append(footer)
    return "\n".join(contents)


def get_subgraph_header(imported_module):
    if imported_module.alias:
        header = f"subgraph {imported_module.alias}"
    else:
        header = f"subgraph {imported_module.module}"
    return header


def get_module_subgraphs(module):
    module_subgraphs = []
    collected = []
    module_lookup = {}
    module_import_list = module["import_list"]
    for imported_module in module_import_list:
        header = get_subgraph_header(imported_module)
        functions = []
        for c in module["call_list"]:
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
