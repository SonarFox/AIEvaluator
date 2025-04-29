import os
import importlib.util
import argparse
import ast
import lizard

def load_rules(rules_dir):
    rule_modules = []
    for filename in os.listdir(rules_dir):
        if filename.endswith('.py'):
            module_name = filename[:-3]
            file_path = os.path.join(rules_dir, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            rule_modules.append(module)
    return rule_modules

def evaluate_line(line, rules):
    total_confidence = 0.0
    for rule in rules:
        if hasattr(rule, 'evaluate') and not hasattr(rule, 'evaluate_file'):
            total_confidence += rule.evaluate(line)
    return total_confidence

def evaluate_file(file_path, rules):
    file_confidences = {}
    for rule in rules:
        if hasattr(rule, 'evaluate_file'):
            result = rule.evaluate_file(file_path)
            if isinstance(result, dict):
                for line_number, confidence_increase in result.items():
                    file_confidences[line_number] = file_confidences.get(line_number, 0) + confidence_increase
    return file_confidences

def adjust_confidence(confidence_ratings):
    adjusted_confidences = confidence_ratings[:]
    for i in range(len(confidence_ratings)):
        if confidence_ratings[i] >= 40.0:
            if i > 0:
                adjusted_confidences[i - 1] = min(adjusted_confidences[i - 1] + 10.0, 100.0)
            if i < len(confidence_ratings) - 1:
                adjusted_confidences[i + 1] = min(adjusted_confidences[i + 1] + 10.0, 100.0)
            if i > 1:
                adjusted_confidences[i - 2] = min(adjusted_confidences[i - 2] + 5.0, 100.0)
            if i < len(confidence_ratings) - 2:
                adjusted_confidences[i + 2] = min(adjusted_confidences[i + 2] + 5.0, 100.0)
    return [min(max(0.0, cr), 100.0) for cr in adjusted_confidences]

def get_function_name_at_line(file_path, line_number):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        tree = ast.parse(code)

        class FunctionFinder(ast.NodeVisitor):
            def __init__(self, target_line):
                self.target_line = target_line
                self.current_function = None

            def visit_FunctionDef(self, node):
                if node.lineno <= self.target_line <= node.end_lineno:
                    self.current_function = node.name
                self.generic_visit(node)

            def visit_Call(self, node):
                if node.lineno == self.target_line:
                    if isinstance(node.func, ast.Name):
                        self.current_function = f"Function Call: {node.func.id}()"
                    elif isinstance(node.func, ast.Attribute):
                        self.current_function = f"Method Call: {node.func.attr}()"
                self.generic_visit(node)

        finder = FunctionFinder(target_line)
        finder.visit(tree)
        return finder.current_function
    except Exception:
        return None

def process_file(file_path, rules, report):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            confidence_ratings = [0.0] * len(lines)

            for rule in rules:
                if hasattr(rule, 'evaluate'):
                    result = rule.evaluate(file_path)
                    if isinstance(result, dict):
                        for line_number, confidence_increase in result.items():
                            if 1 <= line_number <= len(confidence_ratings):
                                confidence_ratings[line_number - 1] = min(confidence_ratings[line_number - 1] + confidence_increase, 100.0)
                    elif isinstance(result, (int, float)):
                        for i in range(len(confidence_ratings)):
                            confidence_ratings[i] = min(confidence_ratings[i] + result, 100.0)
                    elif hasattr(rule, 'evaluate_line'):
                        for i, line in enumerate(lines):
                            confidence_ratings[i] = min(confidence_ratings[i] + rule.evaluate_line(line), 100.0)

            adjusted_confidences = adjust_confidence(confidence_ratings)

            max_confidence = 0.0
            most_likely_line = None
            most_likely_context = None

            for i, confidence in enumerate(adjusted_confidences):
                if confidence > max_confidence:
                    max_confidence = confidence
                    most_likely_line_index = i  # Store the index
                    most_likely_context = get_function_name_at_line(file_path, i + 1)

            if max_confidence > 90.0:  # Only add to report if > 90%
                report[file_path] = {
                    "highest_confidence": f"{max_confidence:.2f}%",
                    "most_likely_line": lines[most_likely_line_index].strip() if most_likely_line_index is not None else None,  # Access line using index
                    "most_likely_context": most_likely_context if most_likely_context else "Top Level",
                }

            max_confidence_width = max(len(f"{conf:.2f}%") for conf in adjusted_confidences)

            for line, confidence in zip(lines, adjusted_confidences):
                confidence_str = f"{confidence:.2f}%".rjust(max_confidence_width)
                print(f"{confidence_str}\t{line}", end="")

            print("\n" + "-" * 40 + "\n")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        report[file_path] = {"error": str(e)}
        print("\n" + "-" * 40 + "\n")

def scan_directory(path_to_scan, rules, report):
    for root, _, files in os.walk(path_to_scan):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                process_file(file_path, rules, report)

def main():
    parser = argparse.ArgumentParser(description="Analyze Python code for generative AI confidence.")
    parser.add_argument("directory", help="The directory to scan.")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist.")
        return

    rules = load_rules('rules/')
    report = {}
    scan_directory(args.directory, rules, report)

    print("\n" + "=" * 40 + "\n")
    print("AI Generation Confidence Report (> 90%):\n")
    if not report:
        print("No files found with confidence > 90%.")
    else:
        for file_path, analysis in report.items():
            if not "error" in analysis:
                print(f"{analysis['highest_confidence']}: {file_path}")

if __name__ == "__main__":
    main()