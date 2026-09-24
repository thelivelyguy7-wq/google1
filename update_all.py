import os
import glob

replacements = {
    "Opportunity hypotheses": "Opportunity hypotheses",
    "opportunity hypotheses": "opportunity hypotheses",
    "Opportunity hypothesis": "Opportunity hypothesis",
    "opportunity hypothesis": "opportunity hypothesis",
    "Opportunity Areas": "Opportunity Areas",
    "opportunity areas": "opportunity areas",
    "Context-to-Query Translation": "Context-to-Query Translation",
    "context-to-query translation": "context-to-query translation",
    "Vague Query Interpretation": "Vague Query Interpretation",
    "Search Recovery Guidance": "Search Recovery Guidance",
    "REMEMBER": "REMEMBER",
    "Remember": "Remember",
    "remember": "remember",
    "The Combined Ecosystem of Opportunities": "The Combined Ecosystem of Opportunities",
    "Keyword Requirements": "Keyword Requirements"
}

# Add all relevant text file extensions
extensions = ["**/*.txt", "**/*.json", "**/*.csv", "**/*.py", "**/*.js", "**/*.html", "**/*.md"]
all_files = []
for ext in extensions:
    all_files.extend(glob.glob(ext, recursive=True))

for filepath in all_files:
    if ".git" in filepath or "node_modules" in filepath or "__pycache__" in filepath:
        continue
    
    # We will try to read as utf-8, skip if it's binary or weird encoding
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        continue
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")
