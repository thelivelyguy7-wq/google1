import json
with open('site/site_data.js', 'r', encoding='utf-8') as f:
    text = f.read()
    
start = text.find('{')
end = text.rfind('}') + 1
data = text[start:end]
d = json.loads(data)

print("--- Segments ---")
for k, v in d['segments'].items():
    print(k, v['n'])

print("\n--- Segment Definitions ---")
for k, v in d['narrative']['segment_defs'].items():
    print(k, ":", v)
