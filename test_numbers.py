#!/usr/bin/env python3
"""Test number normalization"""
import re

pattern = r'-?(?:\d{1,3}[.,])+\d+(?:[.,]\d+)?|-?\d+[.,]\d+'

test_cases = [
    ('10.403.059', '10403059'),
    ('-56.127.780,12', '-56127780.12'),
    ('41,5', '41.5'),
    ('1234567', '1234567'),
]

print("Testing pattern:", pattern)
print()

for input_val, expected in test_cases:
    matches = re.findall(pattern, input_val)
    print(f"Input: {input_val}")
    print(f"  Matches: {matches}")
    print(f"  Expected: {expected}")
    
    if matches:
        match = matches[0]
        if ',' in match and '.' in match:
            result = match.replace('.', '').replace(',', '.')
        elif ',' in match and '.' not in match:
            result = match.replace(',', '.')
        else:
            result = match
        print(f"  Got:      {result}")
        print(f"  Status:   {'✓' if result == expected else '✗'}")
    else:
        print(f"  NO MATCH!")
    print()
