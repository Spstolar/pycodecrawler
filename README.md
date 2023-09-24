# `pygraphcrawler`

Parse Python code and create Mermaid markdown descriptions of its function dependency graph.

Longer explanation [here](https://simonstolarczyk.com/posts/graph/Graph_My_Code_2.html).

## Use

```python
from code_extraction import extract_code_information
from viz_code import create_graph_description

# m_info will house the code data
m_info = extract_code_information(
    directories=["example", "example2"],  # each directory will be searched
    other_python_filenames=["test.py"]  # or specify particular files
)
print(m_info.keys())  # to show us which modules we parsed
module_to_inspect = "abyss"  # select one of the module names
# this is a markdown description of the select module
mermaid_graph_desc = create_graph_description(m_info[module_to_inspect])
```

For example, on

```python
import numpy as np

z = np.zeroes(5)

def mul():
    a = np.array([[1, 0],
                  [0, 1]])
    b = np.array([[4, 1],
                  [2, 2]])
    return np.matmul(a, b)

def eigs_of_product():
    a = np.array([[1, 0],
                  [0, 1]])
    b = np.array([[4, 1],
                  [2, 2]])
    product = np.matmul(a, b)
    eigs = np.linalg.eigs(product)
    np.linalg.debug.depth.error_print(eigs)  # this is a fake call for testing
    return eigs
```

This markdown is produced

````
```{mermaid}
graph LR;
	mul[mul] -->|2| np.array[np.array];
	mul[mul] -->|2| np.array[np.array];
	mul[mul] --> np.matmul[np.matmul];
	eigs_of_product[eigs_of_product] -->|2| np.array[np.array];
	eigs_of_product[eigs_of_product] -->|2| np.array[np.array];
	eigs_of_product[eigs_of_product] --> np.matmul[np.matmul];
	eigs_of_product[eigs_of_product] --> np.linalg.eigs[np.linalg.eigs];
	eigs_of_product[eigs_of_product] --> np.linalg.debug.dept[np.linalg.debug.depth.error_print];
	main[main] --> np.zeroes[np.zeroes];

subgraph np
	np.linalg.debug.dept
	np.array
	np.linalg.eigs
	np.matmul
	np.zeroes
end
```
````

This is markdown that you can run with Quarto or in VSCode to use [Mermaid](https://mermaid.js.org/) to generate the graph visualization.

## How to Use

See the longer explanation [here](https://simonstolarczyk.com/posts/graph/Graph_My_Code_2.html) for more examples.
