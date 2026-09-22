import pandas as pd
from engine import coders

df = pd.read_csv('google_photos_raw_dataset.csv')
text = df['text'].iloc[0]

coder = coders.LLMCoder()
print("Starting coding...")
res = coder.code(text)
if res:
    print("Success!", res.relevance)
else:
    print("Failed to code.")
    print("Stats:", coder.stats)
