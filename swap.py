import re
with open('site/app.js', 'r', encoding='utf-8') as f:
    text = f.read()
s_match = re.search(r'page\("segments".*?^\}\);', text, re.MULTILINE|re.DOTALL)
o_match = re.search(r'page\("opportunities".*?^\}\);', text, re.MULTILINE|re.DOTALL)
text = text.replace(s_match.group(0), 'SWAP_O').replace(o_match.group(0), 'SWAP_S')
text = text.replace('SWAP_O', o_match.group(0)).replace('SWAP_S', s_match.group(0))
with open('site/app.js', 'w', encoding='utf-8') as f:
    f.write(text)
print("Swap successful")
