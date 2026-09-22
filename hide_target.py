import re

with open('site/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'(page\(\"target\".*?^\}\);)'
new_text = re.sub(pattern, r'/*\n\1\n*/', text, flags=re.MULTILINE|re.DOTALL)

with open('site/app.js', 'w', encoding='utf-8') as f:
    f.write(new_text)

print('Done hiding target page')
