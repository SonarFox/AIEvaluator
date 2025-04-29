import ast

def evaluate(file_path):
    """
    Analyzes a Python file for methods with a low comment-to-code ratio.

    Args:
        file_path: The path to the Python file.

    Returns:
        A dictionary where keys are line numbers and values are confidence scores (floats).
    """

    line_confidences = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_lines = len(lines)
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            code_lines = total_lines - comment_lines

            if code_lines == 0:
                return line_confidences  # Avoid division by zero

            comment_ratio = comment_lines / code_lines if code_lines > 0 else 0

            tree = ast.parse("".join(lines))

            class CommentRatioVisitor(ast.NodeVisitor):
                def __init__(self, line_confidences, comment_ratio):
                    self.line_confidences = line_confidences
                    self.current_function_lines = set()
                    self.comment_ratio_threshold = 0.1  # Adjust this threshold as needed
                    self.low_comment_ratio_function = False
                    self.file_lines = lines

                def visit_FunctionDef(self, node):
                    self.current_function_lines = set(range(node.lineno, node.end_lineno + 1))
                    function_code_lines = 0
                    function_comment_lines = 0

                    for line_num in self.current_function_lines:
                        line = self.file_lines[line_num - 1].strip()
                        if line.startswith('#'):
                            function_comment_lines += 1
                        elif line:  # Consider non-empty, non-comment lines as code
                            function_code_lines += 1

                    if function_code_lines > 0 and function_comment_lines / function_code_lines < self.comment_ratio_threshold:
                        self.low_comment_ratio_function = True
                        for line_number in self.current_function_lines:
                            self.line_confidences[line_number] = self.line_confidences.get(line_number, 0) + 5.0
                    else:
                        self.low_comment_ratio_function = False

                    self.generic_visit(node)
                    self.current_function_lines = set()

            visitor = CommentRatioVisitor(line_confidences, comment_ratio)
            visitor.visit(tree)

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

    return line_confidences