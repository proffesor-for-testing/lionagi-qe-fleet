"""Code analysis tools for test generation with ReAct reasoning"""

import ast
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CodeStructure(BaseModel):
    """Structure information extracted from code"""

    functions: List[Dict[str, Any]] = Field(default_factory=list, description="List of functions found")
    classes: List[Dict[str, Any]] = Field(default_factory=list, description="List of classes found")
    complexity: Dict[str, int] = Field(default_factory=dict, description="Complexity metrics")
    dependencies: List[str] = Field(default_factory=list, description="External dependencies")
    lines_of_code: int = Field(default=0, description="Total lines of code")


class CodeAnalyzerTool:
    """Tool for analyzing Python code structure to inform test generation

    This tool parses code files and extracts:
    - Functions and their signatures
    - Classes and methods
    - Complexity metrics
    - Import dependencies

    Used by TestGeneratorAgent during ReAct reasoning to understand
    what needs to be tested.
    """

    @staticmethod
    def analyze_code(file_path: Optional[str] = None, code_content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze code structure and return detailed information

        Args:
            file_path: Path to Python file to analyze (optional if code_content provided)
            code_content: Raw Python code to analyze (optional if file_path provided)

        Returns:
            Dictionary containing:
                - functions: List of function definitions with args, returns, docstrings
                - classes: List of class definitions with methods
                - complexity: Cyclomatic complexity estimates
                - dependencies: List of imported modules
                - lines_of_code: Total LOC

        Example:
            >>> tool = CodeAnalyzerTool()
            >>> result = tool.analyze_code(code_content="def add(a, b): return a + b")
            >>> print(result['functions'])
            [{'name': 'add', 'args': ['a', 'b'], 'returns': True, ...}]
        """
        # Get code content
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                code = f.read()
        elif code_content:
            code = code_content
        else:
            return {
                "error": "Must provide either file_path or code_content",
                "functions": [],
                "classes": [],
                "complexity": {},
                "dependencies": [],
                "lines_of_code": 0
            }

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "error": f"Syntax error in code: {str(e)}",
                "functions": [],
                "classes": [],
                "complexity": {},
                "dependencies": [],
                "lines_of_code": len(code.split('\n'))
            }

        functions = []
        classes = []
        dependencies = []
        complexity = {}

        # Extract functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "defaults": len(node.args.defaults),
                    "returns": node.returns is not None,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                    "docstring": ast.get_docstring(node),
                    "line_number": node.lineno,
                    "num_statements": len(node.body)
                }

                # Simple complexity estimate (number of branches)
                num_branches = sum(1 for n in ast.walk(node) if isinstance(n, (ast.If, ast.While, ast.For, ast.ExceptHandler)))
                complexity[node.name] = num_branches + 1

                functions.append(func_info)

            # Extract classes
            elif isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            "name": item.name,
                            "args": [arg.arg for arg in item.args.args],
                            "is_property": any(d.id == 'property' if isinstance(d, ast.Name) else False for d in item.decorator_list),
                            "is_staticmethod": any(d.id == 'staticmethod' if isinstance(d, ast.Name) else False for d in item.decorator_list),
                            "is_classmethod": any(d.id == 'classmethod' if isinstance(d, ast.Name) else False for d in item.decorator_list),
                        })

                class_info = {
                    "name": node.name,
                    "bases": [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                    "methods": methods,
                    "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                    "docstring": ast.get_docstring(node),
                    "line_number": node.lineno
                }
                classes.append(class_info)

            # Extract imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)

        return {
            "functions": functions,
            "classes": classes,
            "complexity": complexity,
            "dependencies": list(set(dependencies)),  # Remove duplicates
            "lines_of_code": len(code.split('\n')),
            "total_functions": len(functions),
            "total_classes": len(classes),
            "average_complexity": sum(complexity.values()) / len(complexity) if complexity else 0
        }

    @classmethod
    def get_callable(cls):
        """Get the callable function for use as a tool in ReAct"""
        return cls.analyze_code


class ASTParserTool:
    """Advanced AST analysis for complex code patterns

    This tool provides deeper analysis including:
    - Control flow analysis
    - Data flow patterns
    - Security vulnerability patterns
    - Performance bottleneck detection
    """

    @staticmethod
    def analyze_control_flow(code_content: str) -> Dict[str, Any]:
        """Analyze control flow patterns

        Args:
            code_content: Raw Python code to analyze

        Returns:
            Dictionary containing control flow analysis:
                - loops: List of loop structures
                - conditionals: List of if/elif/else patterns
                - exception_handlers: List of try/except blocks
                - complexity_hotspots: Functions with high complexity
        """
        try:
            tree = ast.parse(code_content)
        except SyntaxError as e:
            return {"error": f"Syntax error: {str(e)}"}

        loops = []
        conditionals = []
        exception_handlers = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                loop_type = "for" if isinstance(node, ast.For) else "while"
                loops.append({
                    "type": loop_type,
                    "line": node.lineno,
                    "nested_depth": sum(1 for n in ast.walk(node) if isinstance(n, (ast.For, ast.While)))
                })

            if isinstance(node, ast.If):
                conditionals.append({
                    "line": node.lineno,
                    "has_elif": len(node.orelse) > 0 and isinstance(node.orelse[0], ast.If),
                    "has_else": len(node.orelse) > 0 and not isinstance(node.orelse[0], ast.If)
                })

            if isinstance(node, ast.Try):
                exception_handlers.append({
                    "line": node.lineno,
                    "num_except": len(node.handlers),
                    "has_finally": len(node.finalbody) > 0,
                    "has_else": len(node.orelse) > 0
                })

        return {
            "loops": loops,
            "total_loops": len(loops),
            "conditionals": conditionals,
            "total_conditionals": len(conditionals),
            "exception_handlers": exception_handlers,
            "total_exception_handlers": len(exception_handlers)
        }

    @staticmethod
    def detect_edge_cases(code_content: str) -> Dict[str, Any]:
        """Detect potential edge cases that need testing

        Args:
            code_content: Raw Python code to analyze

        Returns:
            Dictionary containing detected edge cases:
                - boundary_checks: Division, indexing operations
                - null_checks: None comparisons
                - type_checks: isinstance() calls
                - resource_handling: File/network operations
        """
        try:
            tree = ast.parse(code_content)
        except SyntaxError as e:
            return {"error": f"Syntax error: {str(e)}"}

        boundary_checks = []
        null_checks = []
        type_checks = []
        resource_ops = []

        for node in ast.walk(tree):
            # Detect division (zero division edge case)
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                boundary_checks.append({
                    "type": "division",
                    "line": node.lineno,
                    "edge_case": "Division by zero"
                })

            # Detect subscript operations (index out of bounds)
            if isinstance(node, ast.Subscript):
                boundary_checks.append({
                    "type": "indexing",
                    "line": node.lineno,
                    "edge_case": "Index out of bounds"
                })

            # Detect None comparisons
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, (ast.Is, ast.IsNot)):
                        null_checks.append({
                            "line": node.lineno,
                            "edge_case": "None/null handling"
                        })

            # Detect isinstance calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "isinstance":
                    type_checks.append({
                        "line": node.lineno,
                        "edge_case": "Type validation"
                    })

                # Detect file operations
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    resource_ops.append({
                        "type": "file",
                        "line": node.lineno,
                        "edge_case": "File not found, permission errors"
                    })

        return {
            "boundary_checks": boundary_checks,
            "null_checks": null_checks,
            "type_checks": type_checks,
            "resource_operations": resource_ops,
            "total_edge_cases": len(boundary_checks) + len(null_checks) + len(type_checks) + len(resource_ops),
            "recommendations": [
                "Test division by zero scenarios" if boundary_checks else None,
                "Test None/null input handling" if null_checks else None,
                "Test with invalid types" if type_checks else None,
                "Test file/resource error handling" if resource_ops else None
            ]
        }

    @classmethod
    def get_callable(cls):
        """Get the callable function for use as a tool in ReAct"""
        return cls.detect_edge_cases
