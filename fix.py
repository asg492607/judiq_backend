with open('response_builder.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        final_weaknesses = structured_weaknesses
        final_issues = [r for r in structured_weaknesses if r['severity'] in ['FATAL', 'CRITICAL', 'HIGH']]"""

replacement = """        for r in structured_weaknesses:
            r['text'] = r.get('risk', '')
        final_weaknesses = structured_weaknesses
        final_issues = [r for r in structured_weaknesses if r.get('severity') in ['FATAL', 'CRITICAL', 'HIGH']]"""

if target in content:
    with open('response_builder.py', 'w', encoding='utf-8') as f:
        f.write(content.replace(target, replacement))
    print('Success')
else:
    print('Target not found')
