# rules/ai_comment_rule.py

import re

def evaluate(code_line):
    """
    Evaluates a single line of code for AI generation indicators based on comments.

    Args:
        code_line: A string representing a single line of code.

    Returns:
        A confidence score (float) between 0.0 and 100.0.
    """

    if re.search(r"#\s*generated\s*by\s*ai", code_line, re.IGNORECASE) or \
       re.search(r"//\s*generated\s*by\s*ai", code_line, re.IGNORECASE) or \
       re.search(r"/\*\s*generated\s*by\s*ai\s*\*/", code_line, re.IGNORECASE):
        return 75.0  # 75% confidence if explicitly stated
    else:
        return 0.0