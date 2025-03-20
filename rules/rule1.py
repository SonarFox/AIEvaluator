import re

# Define the rule for code style and consistency

def evaluate(line):
    # Regular expression patterns for consistent indentation, spacing, and coding conventions
    patterns = [
        re.compile(r'^[ ]{4}'),  # 4 spaces indentation
        re.compile(r';\s*'),  # Semicolon usage with different spacing
        re.compile(r'\b([a-zA-Z_]+)\b'),  # Variable naming conventions
    ]

    consistency_threshold = 2  # Number of patterns to indicate high consistency
    match_count = 0

    for pattern in patterns:
        if pattern.search(line):
            match_count += 1

    # Calculate confidence score based on matches
    confidence = 0.0
    if match_count >= consistency_threshold:
        confidence = 10.0 + (match_count - consistency_threshold)
    else:
        confidence = match_count

    return confidence