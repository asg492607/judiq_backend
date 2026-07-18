import re

with open('pdf_generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if line.strip().startswith('from reportlab') or line.strip() == 'import re' or line.strip() == 'import hashlib':
        if i > 20:
            continue
    new_lines.append(line)

with open('pdf_generator.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)