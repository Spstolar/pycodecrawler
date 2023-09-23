from collections import Counter


def create_collapsed_function_call_edges(module: dict):
    """Create code dependency graph from function definition data.

    Args:
        module (dict): parsed module data

    Returns:
        list: edges between defined function names and calls in the definition
    """
    edge_list = []
    for f in module["func_defs"]:
        name = f.name
        for call in f.calls:
            if call.module:
                module = ".".join(call.module)
                edge_list.append((name, f"{module}.{call.name}"))
            else:
                edge_list.append((name, f"{call.name}"))
    return edge_list


def create_function_call_edges(module: dict):
    """Create code dependency graph from function definition data. Compress repeated call into a counter.

    Args:
        module (dict): parsed module data

    Returns:
        list: edges with weights (s, t, w) between defined function names and calls in the definition
    """
    edge_list = []
    for f in module["func_defs"]:
        name = f.name
        aggregated_calls = Counter()
        for call in f.calls:
            if call.module:
                module = ".".join(call.module)
                full_call_name = f"{module}.{call.name}"
            else:
                full_call_name = f"{call.name}"
            aggregated_calls[full_call_name] += 1
        for full_call_name, call_count in aggregated_calls.items():
            edge_list.append((name, full_call_name, call_count))
    return edge_list
