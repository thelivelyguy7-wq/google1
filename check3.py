import json
with open('site/site_data.js', 'r', encoding='utf-8') as f:
    text = f.read()
    
start = text.find('{')
end = text.rfind('}') + 1
data = text[start:end]
d = json.loads(data)

print("behavior_code:", sorted(d['stage1']['behavior_code'].items(), key=lambda x: x[1], reverse=True)[:5])
print("object_class:", sorted(d['stage1']['object_class'].items(), key=lambda x: x[1], reverse=True)[:5])
print("retrieval_state:", sorted(d['stage1']['retrieval_state'].items(), key=lambda x: x[1], reverse=True)[:5])
