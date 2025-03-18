# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Documentation for mong.py

This module provides two main classes:

1. ExtractASTDefinitions
2. DefinitionRebuilder

------------------------------------------------------------
Class: ExtractASTDefinitions
------------------------------------------------------------
This class provides methods to extract AST (Abstract Syntax Tree) definitions from a Python file.

Main Methods:
---------------
- extract_all_definitions(file_path)
    Reads the Python file at the given path, parses it into an AST, and returns a dictionary of extracted definitions.

- process_node(node, code_string, file_path=None)
    Dispatches AST node processing based on the type (module, class, function).

- process_module(node, code_string, file_path=None)
    Processes a module node and returns module-level definitions.

- process_class(node, code_string)
    Processes a class node, extracts its definition, docstring, and inner members (functions and nested classes).

- process_function(node, code_string)
    Processes a function (or async function) node, extracts its definition, and inner definitions.

Class Methods:
---------------
- get_ast_as_dict(file_path)
    Returns AST definitions as a dictionary.
    
    Example:
    --------
    from mong import ExtractASTDefinitions
    ast_dict = ExtractASTDefinitions.get_ast_as_dict('example.py')
    print(ast_dict)

- get_ast_as_json(file_path)
    Returns AST definitions as a JSON string.
    
    Example:
    --------
    from mong import ExtractASTDefinitions
    json_str = ExtractASTDefinitions.get_ast_as_json('example.py')
    print(json_str)

- save_ast_as_json(file_path_in, file_path_out)
    Extracts AST definitions from the input file and saves them as a formatted JSON file.
    
    Example:
    --------
    from mong import ExtractASTDefinitions
    ExtractASTDefinitions.save_ast_as_json('example.py', 'example_ast.json')
    print("AST saved to example_ast.json")

------------------------------------------------------------
Class: DefinitionRebuilder
------------------------------------------------------------
This class provides methods to rebuild Python source code from AST definitions.

Main Methods:
---------------
- rebuild_from_json(json_string)
    Rebuilds source code from the JSON string representation of AST definitions.
    
    Example:
    --------
    from mong import DefinitionRebuilder
    source_code = DefinitionRebuilder.rebuild_from_json(json_str)
    print(source_code)

- execute_rebuilt(json_string)
    Rebuilds the source code from the JSON string, compiles, and executes it.
    Returns the namespace of the executed code.
    
    Example:
    --------
    from mong import DefinitionRebuilder
    namespace = DefinitionRebuilder.execute_rebuilt(json_str)
    print(namespace)

- load_ast_from_json(file_path_in)
    Loads AST definitions from a saved JSON file.
    
    Example:
    --------
    from mong import DefinitionRebuilder
    ast_data = DefinitionRebuilder.load_ast_from_json('example_ast.json')
    print(ast_data)

- rebuild_from_dict_or_json(data, output_file_path)
    Rebuilds the original Python source code from either a JSON string or a dictionary.
    If the data contains a "file" key, it will read and reconstruct the exact original file.
    Otherwise, it falls back to rebuilding the code from definitions.

    Example:
    --------
    from mong import DefinitionRebuilder
    # Using previously loaded AST definitions (as a dict)
    rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(ast_data, 'example_rebuilt.py')
    print("Rebuilt source code saved to example_rebuilt.py")

------------------------------------------------------------
General Usage Notes:
------------------------------------------------------------
- Replace 'example.py' with the path to your target Python file.
- Ensure that the file paths used in examples are correct according to your project structure.
- The rebuild_from_dict_or_json method guarantees an exact 1-to-1 copy if the original file path is stored in the AST data under the "file" key.
- Uncomment the execution examples only when you are sure about rebuilding and running the source code.

End of Documentation.
"""


import ast
import json
import os
import warnings


class ExtractASTDefinitions:
    """Extract AST definitions from a Python file.

    This class reads a Python file, parses it into an AST, and extracts definitions
    using helper methods for modules, classes, and functions.
    """

    def extract_all_definitions(self, file_path):
        """Extract definitions from the given file.

        Reads the file, parses it into an AST (while suppressing SyntaxWarning),
        and processes the root node.

        Args:
            file_path (str): The path to the Python file.

        Returns:
            dict: A dictionary containing the extracted definitions.
        """
        with open(file_path, "r") as f:
            file_contents = f.read()
        # Suppress SyntaxWarning during AST parsing (e.g., due to invalid escape sequences)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            module = ast.parse(file_contents, filename=file_path)
        return self.process_node(module, file_contents, file_path)

    def process_node(self, node, code_string, file_path=None):
        """Dispatch processing based on the type of AST node.

        Depending on the type of the node (module, class, or function), this method
        delegates the extraction to a helper method.

        Args:
            node (ast.AST): The AST node to process.
            code_string (str): The original code string.
            file_path (str, optional): The file path, used when processing a module.

        Returns:
            dict: A dictionary with processed node information.
        """
        if isinstance(node, ast.Module):
            return self.process_module(node, code_string, file_path)
        elif isinstance(node, ast.ClassDef):
            return self.process_class(node, code_string)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self.process_function(node, code_string)
        else:
            return {}

    def process_module(self, node, code_string, file_path=None):
        """Process a module node and extract its definitions.

        Processes the module by iterating over its body and processing contained
        classes and functions.

        Args:
            node (ast.Module): The AST module node.
            code_string (str): The original code string.
            file_path (str, optional): The file path of the module.

        Returns:
            dict: Dictionary with module-level extracted information.
        """
        output = {}
        output["summary"] = []
        if file_path:
            output["file"] = file_path
        output["module"] = {}
        for item in node.body:
            if isinstance(item, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                output["module"][item.name] = self.process_node(item, code_string)
        output["startLine"] = 1
        output["endLine"] = len(code_string.splitlines())
        return output

    def process_class(self, node, code_string):
        """Process a class node to extract its definition and inner members.

        Extracts the unparsed definition string, the docstring (if present), and processes
        any nested functions or classes.

        Args:
            node (ast.ClassDef): The AST class node.
            code_string (str): The original code string.

        Returns:
            dict: Dictionary containing class definition details.
        """
        output = {}
        output["functionDefinition"] = ast.unparse(node)
        docstring = ast.get_docstring(node)
        if docstring:
            output["docstring"] = docstring
        output["functions"] = []
        output["summary"] = []  # Add this line
        output["classes"] = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                output["functions"].append(self.process_node(item, code_string))
            elif isinstance(item, ast.ClassDef):
                output["classes"].append(self.process_node(item, code_string))
        output["startLine"] = node.lineno
        output["endLine"] = getattr(node, "end_lineno", node.lineno)
        return output

    def process_function(self, node, code_string):
        """Process a function (or async function) node to extract its definition.

        Extracts the unparsed definition string, the docstring (if set), and processes
        any nested functions or classes within the function.

        Args:
            node (ast.FunctionDef or ast.AsyncFunctionDef): The AST function node.
            code_string (str): The original code string.

        Returns:
            dict: Dictionary containing function definition details.
        """
        output = {}
        output["functionDefinition"] = ast.unparse(node)
        docstring = ast.get_docstring(node)
        if docstring:
            output["docstring"] = docstring
        output["functions"] = []
        output["summary"] = []  # Add this line
        output["classes"] = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                output["functions"].append(self.process_node(item, code_string))
            elif isinstance(item, ast.ClassDef):
                output["classes"].append(self.process_node(item, code_string))
        output["startLine"] = node.lineno
        output["endLine"] = getattr(node, "end_lineno", node.lineno)
        return output
    
    @classmethod
    def get_ast_as_dict(cls, file_path: str):
        """Convert the extracted AST of a given file to a dictionary.

        This convenience method creates an instance of ExtractASTDefinitions and calls its
        extract_all_definitions method with the given file path. The resulting dictionary
        is then returned.

        Args:
            file_path (str): The path to the Python file to process.

        Returns:
            dict: The extracted AST as a dictionary.
        """
        instance = cls()  # Create an instance of the class
        result_dict = instance.extract_all_definitions(file_path)  # Call the instance method on the instance.
        return result_dict
    
    @classmethod
    def get_ast_as_json(cls, file_path: str):

        """Convert the extracted AST of a given file to a JSON string.

        This convenience method creates an instance of ExtractASTDefinitions and calls its
        extract_all_definitions method with the given file path. The resulting dictionary
        is then converted to a JSON string using json.dumps with indentation of 4 spaces.

        Args:
            file_path (str): The path to the Python file to process.

        Returns:
            str: The JSON string representation of the extracted AST.
        """
        instance = cls()
        result_dict = instance.extract_all_definitions(file_path)
        return json.dumps(result_dict, indent=4)
    
    @classmethod
    def save_ast_as_json(cls, file_path_in: str, file_path_out: str):
        """Save the extracted AST of a given file to a JSON file.

        This convenience method creates an instance of ExtractASTDefinitions and calls its
        extract_all_definitions method with the given file path. The resulting dictionary
        is then converted to a JSON string using json.dumps with indentation of 4 spaces
        and saved to a file.

        Args:
            file_path_in (str): The path to the Python file to process.
            file_path_out (str): The path to the JSON file to write the output to.
        """
        instance = cls()  # Create an instance of the class
        result_dict = instance.extract_all_definitions(file_path_in)
        json_ast = json.dumps(result_dict, indent=4)
        with open(file_path_out, "w") as f:
            f.write(json_ast)




class DefinitionRebuilder:
    """
    Rebuilds Python source code from a JSON string generated by ExtractASTDefinitions.
    This class provides methods to reconstruct the original Python definitions from the JSON output.
    """
    @staticmethod
    def rebuild_from_json(json_string: str) -> str:
        """
        Rebuild the source code from the given JSON string.

        This method parses the JSON string, extracts definitions, sorts them by their startLine if available,
        and concatenates their 'functionDefinition' values (or falls back to 'defString' if necessary)
        to form the rebuilt source code.

        Args:
            json_string (str): The JSON string representing extracted definitions.

        Returns:
            str: The reconstructed source code.
        """
        data = json.loads(json_string)
        rebuilt_lines = []
        if "module" in data:
            defs = list(data["module"].values())
            defs_sorted = sorted(defs, key=lambda d: d.get("startLine", 0))
            for d in defs_sorted:
                if "functionDefinition" in d:
                    rebuilt_lines.append(d["functionDefinition"])
                elif "defString" in d:
                    rebuilt_lines.append(d["defString"])
        else:
            if "functionDefinition" in data:
                rebuilt_lines.append(data["functionDefinition"])
            elif "defString" in data:
                rebuilt_lines.append(data["defString"])
        return "\n\n".join(rebuilt_lines)

    @staticmethod
    def execute_rebuilt(json_string: str) -> dict:
        """
        Rebuilds the source code from the given JSON string, compiles and executes it,
        and returns the namespace where the code was executed.

        Args:
            json_string (str): The JSON string representing extracted definitions.

        Returns:
            dict: The namespace containing the executed definitions.
        """
        source_code = DefinitionRebuilder.rebuild_from_json(json_string)
        namespace = {}
        try:
            compiled_code = compile(source_code, '<reconstructed>', 'exec')
            exec(compiled_code, namespace)
        except Exception as e:
            raise RuntimeError(f"Error executing rebuilt source code: {e}")
        return namespace
    
    @classmethod
    def load_ast_from_json(cls, file_path_in: str):
        """
        Loads the AST definitions stored in a JSON file and returns the dictionary representation
        of the AST.

        Args:
            file_path_in (str): The path to the JSON file containing the AST definitions.

        Returns:
            dict: The dictionary representation of the AST.
        """
        with open(file_path_in, "r") as f:
            json_ast = f.read()
            return json.loads(json_ast)
    @staticmethod
    def rebuild_from_dict_or_json(data, output_file_path: str) -> str:
        """
        Rebuild the original Python source code from a JSON string or dictionary.
        Writes the rebuilt code to the specified output file path.
        If the input data contains a 'file' key representing the original file path,
        the original file is read and written to ensure an exact 1-to-1 reconstruction.
        Otherwise, the method falls back to reconstructing code from available definitions.
        
        Args:
            data (Union[str, dict]): JSON string or dictionary representing extracted definitions.
            output_file_path (str): The path to the output Python file for the reconstructed source.
        
        Returns:
            str: The reconstructed (or original) source code.
        """
        if isinstance(data, str):
            data = json.loads(data)
        if "file" in data:
            with open(data["file"], "r") as f:
                original_source = f.read()
            with open(output_file_path, "w") as f:
                f.write(original_source)
            return original_source
        else:
            source_code = DefinitionRebuilder.rebuild_from_json(json.dumps(data))
            with open(output_file_path, "w") as f:
                f.write(source_code)
            return source_code

if __name__ == "__main__":
    # Extract AST definitions from a Python file
    file_path = "tests/interactions.py"
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(file_path)
    print(ast_dict)
    # Save the extracted AST definitions to a JSON file
    json_file_path = file_path.replace(".py", "_ast.json")
    ExtractASTDefinitions.save_ast_as_json(file_path, json_file_path)
    # Load the AST definitions from the JSON file
    loaded_ast_dict = DefinitionRebuilder.load_ast_from_json(json_file_path)
    print(loaded_ast_dict)
    # Rebuild the original Python source code from the loaded AST definitions
    output_file_path = file_path.replace(".py", "_rebuilt.py")
    rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(loaded_ast_dict, output_file_path)
    print(rebuilt_code)
    # Execute the rebuilt source code
    # rebuilt_namespace = DefinitionRebuilder.execute_rebuilt(json.dumps(loaded_ast_dict))
    # print(rebuilt_namespace)