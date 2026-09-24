import json
with open('site/site_data.js', 'r', encoding='utf-8') as f:
    text = f.read()
    
start = text.find('{')
end = text.rfind('}') + 1
data = text[start:end]
d = json.loads(data)

print("--- Keys in stage1 ---")
print(d['stage1'].keys())

print("\n--- Object Classes / Scenarios ---")
# Let's check what distributions exist that might answer "What kinds of old photos"
if 'object_class' in d['stage1']:
    print("object_class:", list(d['stage1']['object_class'].items())[:5])
elif 'scenario' in d['stage1']:
    print("scenario:", list(d['stage1']['scenario'].items())[:5])
else:
    # Look for any key that might be relevant
    for k, v in d['stage1'].items():
        if isinstance(v, dict):
            print(f"{k} keys:", list(v.keys())[:3])

print("\n--- Behaviors (How they formulate) ---")
if 'behavior_code' in d['stage1']:
    print("behavior_code:", list(d['stage1']['behavior_code'].items())[:5])

print("\n--- Decomposition Nodes ---")
for k, v in d['decomposition'].items():
    print(k, v['name'])
