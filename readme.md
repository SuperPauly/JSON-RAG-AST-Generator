# JSON RAG AST Generator

## Overview

The **JSON RAG AST Generator** is a Python-based tool for working with Abstract Syntax Trees (ASTs). It provides functionality to extract AST definitions from Python files and rebuild Python source code from these definitions. This project was designed for my RAG Python code experiments it's also useful for analyzing, transforming, and reconstructing Python code programmatically.

---

## Features

- Extract AST definitions from Python files.
- View & manipulate AST as a Dict
- Reconstruct the manipulated Dict into .py file.
- Save AST definitions as JSON.
- Rebuild Python source code from AST definitions or JSON representations.
- Execute reconstructed Python code dynamically. 
- A blank `'summery': []` is in each nested object for adding aditional information E.G. LLM summeries or other contextual info.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/superpauly/json-rag-ast-generator.git
   cd json-rag-ast-generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Extracting AST Definitions

Use the `ExtractASTDefinitions` class to extract AST definitions from a Python file.

```python
from json_rag_ast import ExtractASTDefinitions

# Extract AST as a dictionary
file_path = "example.py"
ast_dict = ExtractASTDefinitions.get_ast_as_dict(file_path)
print(ast_dict)

# Save AST as JSON
ExtractASTDefinitions.save_ast_as_json(file_path, "example_ast.json")
```

### Rebuilding Python Code

Use the `DefinitionRebuilder` class to rebuild Python source code from AST definitions.

```python
from json_rag_ast import DefinitionRebuilder

# Load AST from JSON
ast_data = DefinitionRebuilder.load_ast_from_json("example_ast.json")

# Rebuild source code
rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(ast_data, "rebuilt_example.py")
print("Rebuilt code saved to rebuilt_example.py")
```

### Executing Rebuilt Code

Execute the rebuilt Python code dynamically.

```python
from json_rag_ast import DefinitionRebuilder

# Execute rebuilt code
namespace = DefinitionRebuilder.execute_rebuilt(json.dumps(ast_data))
print(namespace)
```

---

## Classes and Methods

### Class: `ExtractASTDefinitions`

#### Methods:

- **`extract_all_definitions(file_path)`**  
  Extracts AST definitions from the given Python file.

- **`process_node(node, code_string, file_path=None)`**  
  Dispatches AST node processing based on the type (module, class, function).

- **`process_module(node, code_string, file_path=None)`**  
  Processes a module node and extracts module-level definitions.

- **`process_class(node, code_string)`**  
  Processes a class node, extracts its definition, docstring, and inner members.

- **`process_function(node, code_string)`**  
  Processes a function node, extracts its definition, and inner definitions.

- **`get_ast_as_dict(file_path)`**  
  Returns AST definitions as a dictionary.

- **`get_ast_as_json(file_path)`**  
  Returns AST definitions as a JSON string.

- **`save_ast_as_json(file_path_in, file_path_out)`**  
  Saves AST definitions to a JSON file.

---

### Class: `DefinitionRebuilder`

#### Methods:

- **`rebuild_from_json(json_string)`**  
  Rebuilds Python source code from a JSON string representation of AST definitions.

- **`execute_rebuilt(json_string)`**  
  Executes the rebuilt Python source code and returns the namespace.

- **`load_ast_from_json(file_path_in)`**  
  Loads AST definitions from a JSON file.

- **`rebuild_from_dict_or_json(data, output_file_path)`**  
  Rebuilds Python source code from a dictionary or JSON string and saves it to a file.

---

## Example Workflow

1. Extract AST definitions from a Python file:
   ```python
   from json_rag_ast import ExtractASTDefinitions
   ast_dict = ExtractASTDefinitions.get_ast_as_dict("example.py")
   ExtractASTDefinitions.save_ast_as_json("example.py", "example_ast.json")
   ```

2. Load AST definitions and rebuild the source code:
   ```python
   from json_rag_ast import DefinitionRebuilder
   ast_data = DefinitionRebuilder.load_ast_from_json("example_ast.json")
   rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(ast_data, "rebuilt_example.py")
   ```

3. Execute the rebuilt code:
   ```python
   namespace = DefinitionRebuilder.execute_rebuilt(json.dumps(ast_data))
   print(namespace)
   ```

---

## Project Structure

```
JSON-RAG-AST-Generator/
├── json_rag_ast/
│   ├── __init__.py
│   ├── json_rag_ast.py
│   └── ...
├── tests/
│   ├── __init__.py
│   └── test_json_rag_ast.py
├── mong_usage_doc.txt
├── README.md
├── LICENSE
├── setup.py
├── pyproject.toml
└── .gitignore
```

---

## License

This project is licensed under the MIT License.
