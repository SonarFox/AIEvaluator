import ast
import lizard

def evaluate(file_path):
    """
    Analyzes a Python file for high cyclomatic complexity functions and tags all lines within them.

    Args:
        file_path: The path to the Python file.

    Returns:
        A dictionary where keys are line numbers and values are confidence scores (floats).
    """

    line_confidences = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        functions = lizard.analyze_file.analyze_source_code(file_path, code).function_list

        high_complexity_functions = {
            func.name: func.cyclomatic_complexity
            for func in functions
            if func.cyclomatic_complexity > 25
        }

        if not high_complexity_functions:
            return line_confidences

        tree = ast.parse(code)

        class FunctionLineVisitor(ast.NodeVisitor):
            def __init__(self, high_complexity_functions, line_confidences):
                self.high_complexity_functions = high_complexity_functions
                self.line_confidences = line_confidences
                self.current_function = None
                self.current_function_lines = set()

            def visit_FunctionDef(self, node):
                self.current_function = node.name
                self.current_function_lines = set(range(node.lineno, node.end_lineno + 1))
                self.generic_visit(node)
                if self.current_function and self.current_function in self.high_complexity_functions:
                    for line_number in self.current_function_lines:
                        self.line_confidences[line_number] = min(self.line_confidences.get(line_number, 0) + 10.0, 100.0) # Cap at 100
                self.current_function = None
                self.current_function_lines = set()

        visitor = FunctionLineVisitor(high_complexity_functions, line_confidences)
        visitor.visit(tree)

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

    return line_confidences