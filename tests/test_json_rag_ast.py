import ast
import json
import pytest
from ..json_rag_ast_generator import ExtractASTDefinitions, DefinitionRebuilder

# Helper function to create a temporary test file.
def create_temp_file(tmp_path, content, filename="test.py"):
    file_path = tmp_path / filename
    file_path.write_text(content)
    return file_path

def test_simple_function(tmp_path):
    # Test parsing a simple function with a docstring.
    code = '''\
def hello(name: str) -> str:
    """Say hello"""
    return f"Hello {name}"
'''
    test_file = create_temp_file(tmp_path, code, "simple_func.py")
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
    # Check that the module contains the function "hello".
    assert "hello" in ast_dict["module"]
    func_def = ast_dict["module"]["hello"]
    assert "functionDefinition" in func_def
    assert "hello" in func_def["functionDefinition"]

def test_simple_class(tmp_path):
    # Test parsing a simple class with an __init__ method.
    code = '''\
class Person:
    """Person class"""
    def __init__(self, name):
        self.name = name
'''
    test_file = create_temp_file(tmp_path, code, "simple_class.py")
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
    # Check that the module contains the class "Person".
    assert "Person" in ast_dict["module"]
    class_def = ast_dict["module"]["Person"]
    # Verify that the docstring was captured.
    assert "docstring" in class_def
    assert "Person" in class_def["functionDefinition"]

def test_module_level(tmp_path):
    # Test module-level parsing that includes a function and a class.
    code = '''\
import os

def func1():
    pass

class Class1:
    pass
'''
    test_file = create_temp_file(tmp_path, code, "module_level.py")
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
    module = ast_dict.get("module", {})
    assert "func1" in module
    assert "Class1" in module

def test_empty_file(tmp_path):
    # Test handling of an empty file.
    code = ''
    test_file = create_temp_file(tmp_path, code, "empty.py")
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
    # For an empty file, the "module" dict should be empty.
    assert ast_dict["module"] == {}
    # startLine defaults to 1 and endLine equals number of lines in file (0 for empty).
    assert ast_dict["startLine"] == 1
    assert ast_dict["endLine"] == 0

def test_roundtrip(tmp_path):
    # Test full roundtrip: Python source -> JSON AST -> Python source (exact reconstruction).
    code = '''\
def greet():
    return "Hello, World!"
'''
    test_file = create_temp_file(tmp_path, code, "roundtrip.py")
    # Get JSON representation of the AST.
    json_str = ExtractASTDefinitions.get_ast_as_json(str(test_file))
    # Rebuild from JSON; since the AST data includes the "file" key, it will read the original file.
    output_file = tmp_path / "rebuilt.py"
    rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(json.loads(json_str), str(output_file))
    original = test_file.read_text()
    # The rebuilt code should be exactly the same as the original.
    assert rebuilt_code == original
    # Also check that the output file contains the original code.
    assert output_file.read_text() == original

def test_code_execution(tmp_path):
    # Test that executing the rebuilt code produces a valid namespace.
    code = '''\
def add(a, b):
    return a + b
'''
    test_file = create_temp_file(tmp_path, code, "exec_test.py")
    json_str = ExtractASTDefinitions.get_ast_as_json(str(test_file))
    namespace = DefinitionRebuilder.execute_rebuilt(json_str)
    # Verify that the function "add" exists in the namespace.
    assert "add" in namespace
    # Test that the function works as expected.
    assert namespace["add"](2, 3) == 5

def test_invalid_file():
    # Test that providing a non-existent file path raises a FileNotFoundError.
    with pytest.raises(FileNotFoundError):
        ExtractASTDefinitions.get_ast_as_dict("nonexistent.py")

def test_invalid_json():
    # Test that rebuilding from invalid JSON raises a JSONDecodeError.
    with pytest.raises(json.JSONDecodeError):
        DefinitionRebuilder.rebuild_from_json("invalid json")

def test_nested_definitions(tmp_path):
    # Test handling of nested classes and functions
    code = '''\
class Outer:
    """Outer class docstring"""
    
    def outer_method(self):
        """Outer method docstring"""
        def inner_function():
            return "inner"
        return inner_function()
        
    class Inner:
        """Inner class docstring"""
        def inner_method(self):
            return "inner method"
'''
    test_file = create_temp_file(tmp_path, code, "nested.py")
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
    
    # Check outer class exists
    assert "Outer" in ast_dict["module"]
    outer_class = ast_dict["module"]["Outer"]
    
    # Check outer class docstring
    assert outer_class["docstring"] == "Outer class docstring"
    
    # Check outer method exists
    assert any(func["functionDefinition"].startswith("def outer_method") 
               for func in outer_class["functions"])
    
    # Check inner class exists
    assert any(cls["functionDefinition"].startswith("class Inner") 
               for cls in outer_class["classes"])

def test_async_functions(tmp_path):
    # Test handling of async functions
    code = '''\
async def fetch_data():
    """Async function docstring"""
    return "data"

class AsyncClass:
    async def async_method(self):
        return await fetch_data()
'''
    test_file = create_temp_file(tmp_path, code, "async_funcs.py")
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
    
    # Check async function exists
    assert "fetch_data" in ast_dict["module"]
    async_func = ast_dict["module"]["fetch_data"]
    
    # Verify that async keyword is preserved in function definition
    assert "async def fetch_data" in async_func["functionDefinition"]
    
    # Check AsyncClass exists and has async method
    assert "AsyncClass" in ast_dict["module"]
    async_class = ast_dict["module"]["AsyncClass"]
    assert any("async def async_method" in func["functionDefinition"] 
               for func in async_class["functions"])


def test_module_docstring(tmp_path):
    # Test handling of module-level docstrings
    code = '''"""
This is a module-level docstring.
It spans multiple lines.
"""

def example_function():
    pass
'''
    test_file = create_temp_file(tmp_path, code, "module_docstring.py")
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
    
    # Verify that round-trip preserves the docstring
    json_str = ExtractASTDefinitions.get_ast_as_json(str(test_file))
    output_file = tmp_path / "rebuilt_with_docstring.py"
    rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(json.loads(json_str), str(output_file))
    
    # The rebuilt code should contain the original docstring
    assert '"""' in rebuilt_code
    assert "This is a module-level docstring." in rebuilt_code
    assert "It spans multiple lines." in rebuilt_code

def test_save_and_load_ast(tmp_path):
    # Test saving and loading AST definitions to/from JSON files
    code = '''\
def example():
    return "Hello, world!"
'''
    test_file = create_temp_file(tmp_path, code, "save_load.py")
    
    # Save AST to JSON
    json_file = tmp_path / "saved_ast.json"
    ExtractASTDefinitions.save_ast_as_json(str(test_file), str(json_file))
    
    # Verify JSON file was created
    assert json_file.exists()
    
    # Load AST from JSON
    loaded_ast = DefinitionRebuilder.load_ast_from_json(str(json_file))
    
    # Verify loaded AST contains expected data
    assert "module" in loaded_ast
    assert "example" in loaded_ast["module"]
    
    # Rebuild from loaded AST
    output_file = tmp_path / "loaded_rebuilt.py"
    rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(loaded_ast, str(output_file))
    
    # Compare original with rebuilt
    assert "def example" in rebuilt_code
    assert "return \"Hello, world!\"" in rebuilt_code

def test_syntax_error_handling():
    # Test handling of Python files with syntax errors
    with pytest.raises(SyntaxError):
        # Create an in-memory file-like object with invalid syntax
        import io
        invalid_code = io.StringIO("def broken_function(:\n    print('missing parenthesis')")
        invalid_code.name = "invalid.py"  # Mock a filename
        
        # This should raise a SyntaxError
        module = ast.parse(invalid_code.read(), filename=invalid_code.name)

def test_modern_python_syntax(tmp_path):
    # Test handling of modern Python syntax like f-strings, walrus operator
    code = '''\
def modern_features(items):
    # f-strings
    greeting = f"Hello, {name}!"
    
    # list comprehension with conditional
    result = [x for x in items if x > 0]
    
    # walrus operator (Python 3.8+)
    if (n := len(items)) > 10:
        return f"List is long: {n} items"
        
    return result
'''
    test_file = create_temp_file(tmp_path, code, "modern_syntax.py")
    
    try:
        ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
        # If parsing succeeds, check that function was captured
        assert "modern_features" in ast_dict["module"]
        
        # Test roundtrip to ensure modern syntax is preserved
        json_str = ExtractASTDefinitions.get_ast_as_json(str(test_file))
        output_file = tmp_path / "rebuilt_modern.py"
        rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(json.loads(json_str), str(output_file))
        
        # Check for specific syntax elements in the rebuilt code
        assert "f\"Hello, {name}!\"" in rebuilt_code
        assert "[x for x in items if x > 0]" in rebuilt_code
        assert "(n := len(items))" in rebuilt_code
    except SyntaxError:
        pytest.skip("This test requires Python 3.8+ for walrus operator support")

def test_deeply_nested_structures(tmp_path):
    # Test handling of deeply nested classes and functions (5 levels deep)
    code = '''\
class LevelOne:
    """Level 1 class docstring"""
    
    def level_one_method(self):
        """Level 1 method docstring"""
        
        class LevelTwo:
            """Level 2 class docstring"""
            
            def level_two_method(self):
                """Level 2 method docstring"""
                
                def level_three_function():
                    """Level 3 function docstring"""
                    
                    class LevelFour:
                        """Level 4 class docstring"""
                        
                        def level_four_method(self):
                            """Level 4 method docstring"""
                            
                            def level_five_function():
                                """Level 5 function docstring"""
                                return "Deepest level!"
                            
                            return level_five_function()
                    
                    return LevelFour()
                
                return level_three_function()
        
        return LevelTwo()
'''
    test_file = create_temp_file(tmp_path, code, "deeply_nested.py")
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
    
    # Check level 1 class exists
    assert "LevelOne" in ast_dict["module"]
    level_one = ast_dict["module"]["LevelOne"]
    assert level_one["docstring"] == "Level 1 class docstring"
    
    # Check level 1 method exists
    level_one_method = next(func for func in level_one["functions"] 
                           if "level_one_method" in func["functionDefinition"])
    assert "Level 1 method docstring" in level_one_method["docstring"]
    
    # Check level 2 class exists inside level 1 method
    level_two = next(cls for cls in level_one_method["classes"] 
                    if "LevelTwo" in cls["functionDefinition"])
    assert "Level 2 class docstring" in level_two["docstring"]
    
    # Check level 2 method exists
    level_two_method = next(func for func in level_two["functions"] 
                           if "level_two_method" in func["functionDefinition"])
    assert "Level 2 method docstring" in level_two_method["docstring"]
    
    # Check level 3 function exists inside level 2 method
    level_three_function = next(func for func in level_two_method["functions"] 
                               if "level_three_function" in func["functionDefinition"])
    assert "Level 3 function docstring" in level_three_function["docstring"]
    
    # Check level 4 class exists inside level 3 function
    level_four = next(cls for cls in level_three_function["classes"] 
                     if "LevelFour" in cls["functionDefinition"])
    assert "Level 4 class docstring" in level_four["docstring"]
    
    # Check level 4 method exists
    level_four_method = next(func for func in level_four["functions"] 
                            if "level_four_method" in func["functionDefinition"])
    assert "Level 4 method docstring" in level_four_method["docstring"]
    
    # Check level 5 function exists inside level 4 method
    level_five_function = next(func for func in level_four_method["functions"] 
                              if "level_five_function" in func["functionDefinition"])
    assert "Level 5 function docstring" in level_five_function["docstring"]
    
    # Test round-trip preservation
    json_str = ExtractASTDefinitions.get_ast_as_json(str(test_file))
    output_file = tmp_path / "rebuilt_nested.py"
    rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(json.loads(json_str), str(output_file))
    
    # Verify the deepest level function is preserved in the rebuilt code
    assert "def level_five_function" in rebuilt_code
    assert "Deepest level!" in rebuilt_code

def test_dataclasses(tmp_path):
    # Test handling of Python dataclasses
    code = '''\
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SimpleDataClass:
    """A simple dataclass"""
    name: str
    age: int

@dataclass
class DataClassWithDefaults:
    """Dataclass with default values"""
    name: str
    age: int = 25
    tags: List[str] = field(default_factory=list)
    
@dataclass(frozen=True)
class FrozenDataClass:
    """Immutable dataclass"""
    id: str
    value: float
    
@dataclass
class ChildDataClass(SimpleDataClass):
    """Dataclass inheritance example"""
    email: Optional[str] = None
'''
    test_file = create_temp_file(tmp_path, code, "dataclasses_test.py")
    ast_dict = ExtractASTDefinitions.get_ast_as_dict(str(test_file))
    
    # Check all dataclasses exist in the module
    assert "SimpleDataClass" in ast_dict["module"]
    assert "DataClassWithDefaults" in ast_dict["module"]
    assert "FrozenDataClass" in ast_dict["module"]
    assert "ChildDataClass" in ast_dict["module"]
    
    # Check SimpleDataClass details
    simple_dc = ast_dict["module"]["SimpleDataClass"]
    assert simple_dc["docstring"] == "A simple dataclass"
    assert "@dataclass" in simple_dc["functionDefinition"]
    
    # Check DataClassWithDefaults details
    default_dc = ast_dict["module"]["DataClassWithDefaults"]
    assert "default_factory=list" in default_dc["functionDefinition"]
    
    # Check FrozenDataClass details
    frozen_dc = ast_dict["module"]["FrozenDataClass"]
    assert "@dataclass(frozen=True)" in frozen_dc["functionDefinition"]
    
    # Check ChildDataClass (inheritance) details
    child_dc = ast_dict["module"]["ChildDataClass"]
    assert "class ChildDataClass(SimpleDataClass)" in child_dc["functionDefinition"]
    
    # Test round-trip preservation
    json_str = ExtractASTDefinitions.get_ast_as_json(str(test_file))
    output_file = tmp_path / "rebuilt_dataclasses.py"
    rebuilt_code = DefinitionRebuilder.rebuild_from_dict_or_json(json.loads(json_str), str(output_file))
    
    # Verify dataclass decorators and type hints are preserved
    assert "@dataclass" in rebuilt_code
    assert "@dataclass(frozen=True)" in rebuilt_code
    assert "name: str" in rebuilt_code
    assert "tags: List[str] = field(default_factory=list)" in rebuilt_code
    assert "class ChildDataClass(SimpleDataClass)" in rebuilt_code
    
    # Execute the rebuilt code to ensure it's valid Python
    namespace = {}
    try:
        exec(rebuilt_code, namespace)
        # Test instantiation of rebuilt dataclasses
        simple = namespace["SimpleDataClass"]("John", 30)
        assert simple.name == "John"
        assert simple.age == 30
    except Exception as e:
        pytest.fail(f"Failed to execute rebuilt dataclass code: {e}")

