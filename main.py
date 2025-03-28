import os
import importlib.util
import argparse

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
        if hasattr(rule, 'evaluate'):
            total_confidence += rule.evaluate(line)
    return total_confidence

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

def process_file(file_path, rules):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            confidence_ratings = [0.0] * len(lines)  # Initialize to zeros

            # Apply file-level rules first
            for rule in rules:
                if hasattr(rule, 'evaluate'):
                    if rule.__name__ == 'cyclomatic_complexity_call' or rule.__name__ =='long_function_rule' or rule.__name__ =='deep_nesting_rule':
                        line_confidences = rule.evaluate(file_path)
                        for line_number, confidence_increase in line_confidences.items():
                            confidence_ratings[line_number - 1] = min(confidence_ratings[line_number - 1] + confidence_increase, 100.0)
                    else:
                        # Apply non-cyclomatic rules to the entire file
                        line_confidences = rule.evaluate(file_path)
                        if isinstance(line_confidences, dict): # if the rule returns a dict, it is a file level rule.
                            for line_number, confidence_increase in line_confidences.items():
                                confidence_ratings[line_number - 1] = min(confidence_ratings[line_number - 1] + confidence_increase, 100.0)
                        else: # if the rule returns a float, it is a line by line rule.
                            for i, line in enumerate(lines):
                                confidence_ratings[i] = min(confidence_ratings[i] + rule.evaluate(line), 100.0)

            adjusted_confidences = adjust_confidence(confidence_ratings)

            max_confidence_width = max(len(f"{conf:.2f}%") for conf in adjusted_confidences)

            for line, confidence in zip(lines, adjusted_confidences):
                confidence_str = f"{confidence:.2f}%".rjust(max_confidence_width)
                print(f"{confidence_str}\t{line}", end="")

        print("\n" + "-" * 40 + "\n")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        print("\n" + "-" * 40 + "\n")

def scan_directory(path_to_scan, rules):
    for root, _, files in os.walk(path_to_scan):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                process_file(file_path, rules)

def main():
    parser = argparse.ArgumentParser(description="Analyze Python code for generative AI confidence.")
    parser.add_argument("directory", help="The directory to scan.")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist.")
        return

    rules = load_rules('rules/') # Ensure 'rules' directory exists
    scan_directory(args.directory, rules)

if __name__ == "__main__":
    main()