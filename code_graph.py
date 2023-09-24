from collections import Counter


def get_edges_from_func_defs(function_defs):
    edge_list = []
    for f in function_defs:
        name = f.name
        if f.defined_in is not None:
            name = f"{f.defined_in}.{name}"
        for call in f.calls:
            if call.module:
                module = ".".join(call.module)
                edge_list.append((name, f"{module}.{call.name}"))
            else:
                edge_list.append((name, f"{call.name}"))
    return edge_list


def get_edges_from_class_defs(classes, wanted_classes: list = None):
    class_method_edge_list = []
    for class_data in classes:
        if wanted_classes is not None and class_data.name not in wanted_classes:
            continue
        class_edges = get_edges_from_func_defs(class_data.methods)
        class_method_edge_list.extend(class_edges)
    return class_method_edge_list


def get_edges_from_calls(calls):
    edge_list = []
    name = "main"
    for call in calls:
        if call.module:
            module = ".".join(call.module)
            edge_list.append((name, f"{module}.{call.name}"))
        else:
            edge_list.append((name, f"{call.name}"))
    return edge_list


def create_function_call_edges(
    module: dict,
    wanted_classes: list = None,
    include_body_commands: bool = True,
    include_function_defs: bool = True,
):
    """Create code dependency graph from function definition data.

    Args:
        module (dict): parsed module data

    Returns:
        list: edges between defined function names and calls in the definition
    """
    edge_list = []
    if include_function_defs:
        function_def_edge_list = get_edges_from_func_defs(module["func_defs"])
        edge_list.extend(function_def_edge_list)
    class_method_edges = get_edges_from_class_defs(
        module["class_list"], wanted_classes=wanted_classes
    )
    edge_list.extend(class_method_edges)
    if include_body_commands:
        main_edges = get_edges_from_calls(module["call_list"])
        edge_list.extend(main_edges)
    return edge_list


def create_collapsed_function_call_edges(
    module: dict,
    wanted_classes: list = None,
    include_body_commands: bool = True,
    include_function_defs: bool = True,
):
    """Create code dependency graph from function definition data. Compress repeated call into a counter.

    Args:
        module (dict): parsed module data

    Returns:
        list: edges with weights (s, t, w) between defined function names and calls in the definition
    """
    edge_list = create_function_call_edges(
        module,
        wanted_classes=wanted_classes,
        include_body_commands=include_body_commands,
        include_function_defs=include_function_defs,
    )
    aggregated_calls = Counter()
    for s, t in edge_list:
        combined_name = s + "_" + t
        aggregated_calls[combined_name] += 1

    weighted_edge_list = []
    for s, t in edge_list:
        combined_name = s + "_" + t
        weight = aggregated_calls[combined_name]
        weighted_edge_list.append((s, t, weight))
    return weighted_edge_list
