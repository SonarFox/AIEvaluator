import os
import importlib.util
import pathlib


#
#
#
#

def load_rules(rules_dir):
    rule_modules = []
    for filename in os.listdir(rules_dir):
        if filename.endswith('.py'):
            module_name = filename[:-3]  # Remove '.py' extension
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
        if confidence_ratings[i] > 70.0:
            if i > 0:
                adjusted_confidences[i - 1] += 10.0
            if i < len(confidence_ratings) - 1:
                adjusted_confidences[i + 1] += 10.0
    return [min(max(0.0, cr), 100.0) for cr in adjusted_confidences]


def process_file(file_path, rules):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        confidence_ratings = []
        for i, line in enumerate(lines):
            confidence = evaluate_line(line, rules)
            confidence = min(confidence, 100.0)  # Ensure confidence is within 0-100
            confidence_ratings.append(confidence)

        adjusted_confidences = adjust_confidence(confidence_ratings)

        for line, confidence in zip(lines, adjusted_confidences):
            print(f"Line: {line.strip()} - Confidence: {confidence}%")


def scan_repository(path_to_scan, rules):
    print(path_to_scan)
    # Convert the repo_path to a Path object
    for root, dirs, files in os.walk(path_to_scan):
        for file in files:
            if file.endswith(".java"):
                process_file(os.path.join(root, file), rules)

if __name__ == '__main__':
    target_repo_path = '/Users/lee.fox/IdeaProjects/demo-java-security/'  # Replace with your target repository path
    rules = {}  # Add your rules here
    scan_repository(target_repo_path, load_rules('rules/'))

