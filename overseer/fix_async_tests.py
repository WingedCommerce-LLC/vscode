#!/usr/bin/env python3
"""
Script to add @pytest.mark.asyncio decorators to all async test methods
"""

import re

def fix_async_tests():
    file_path = "tests/integration/test_agent_api.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Pattern to match async def test methods that don't already have @pytest.mark.asyncio
    pattern = r'(\n    )async def (test_[^(]+\([^)]*\):)'

    def replacement(match):
        indent = match.group(1)
        method_def = match.group(2)
        return f'{indent}@pytest.mark.asyncio{indent}async def {method_def}'

    # Replace all occurrences
    new_content = re.sub(pattern, replacement, content)

    with open(file_path, 'w') as f:
        f.write(new_content)

    print("Fixed async test decorators")

if __name__ == "__main__":
    fix_async_tests()
