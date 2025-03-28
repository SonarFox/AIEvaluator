import ast

def evaluate(file_path):
    """
    Analyzes a Python file for functions with deeply nested loops, conditionals, or calls.

    Args:
        file_path: The path to the Python file.

    Returns:
        A dictionary where keys are line numbers and values are confidence scores (floats).
    """

    line_confidences = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        tree = ast.parse(code)

        class NestingVisitor(ast.NodeVisitor):
            def __init__(self, line_confidences):
                self.line_confidences = line_confidences
                self.current_function_lines = set()
                self.nesting_depth = 0
                self.deeply_nested = False

            def visit_FunctionDef(self, node):
                self.current_function_lines = set(range(node.lineno, node.end_lineno + 1))
                self.nesting_depth = 0
                self.deeply_nested = False
                self.generic_visit(node)
                if self.deeply_nested:
                    for line_number in self.current_function_lines:
                        self.line_confidences[line_number] = self.line_confidences.get(line_number, 0) + 10.0
                self.current_function_lines = set()

            def generic_visit(self, node):
                self.nesting_depth += 1
                if self.nesting_depth > 3 and isinstance(node, (ast.For, ast.While, ast.If, ast.Call)):
                    self.deeply_nested = True
                super().generic_visit(node)
                self.nesting_depth -= 1

        visitor = NestingVisitor(line_confidences)
        visitor.visit(tree)

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

    return line_confidences