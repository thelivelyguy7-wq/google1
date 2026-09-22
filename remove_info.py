import re

with open('site/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove the Opportunity column from the Decomposition table
new_text = re.sub(
    r'(\$\{table\(\[\"Node\", \"Case question\", \"User behaviour\", \"Product outcome\"), \"Opportunity\"\]',
    r'\1]',
    text
)
new_text = re.sub(
    r'(esc\(v\.product_outcome\)), esc\(v\.opportunity\)\]\)\)\}',
    r'\1]))}',
    new_text
)

# 2. Remove the Evidence per node and the card
evidence_regex = r'<h2>Evidence per node \$\{OBS\}</h2>.*?</p>\s*</div>'
new_text = re.sub(evidence_regex, '', new_text, flags=re.MULTILINE|re.DOTALL)

with open('site/app.js', 'w', encoding='utf-8') as f:
    f.write(new_text)

print('Done removing info')
