import os
import sys
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from engine.coders import LLMCoder

def main():
    df = pd.read_csv("google_photos_raw_dataset.csv")
    unique_texts = df["text"].dropna().unique().tolist()
    
    cache_path = "output/llm_cache.json"
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
            
    coder = LLMCoder()
    to_process = [t for t in unique_texts if t not in cache]
    
    print(f"Total unique texts: {len(unique_texts)}")
    print(f"Already in cache: {len(cache)}")
    print(f"To process: {len(to_process)}")
    
    def process_text(text):
        try:
            res = coder.code(text)
            if res:
                return text, res.model_dump()
            return text, None
        except Exception as e:
            print(f"Error processing text: {e}")
            return text, None

    if to_process:
        with ThreadPoolExecutor(max_workers=10) as executor:
            for idx, (text, result) in enumerate(executor.map(process_text, to_process)):
                if result is not None:
                    cache[text] = result
                if (idx + 1) % 10 == 0:
                    print(f"Processed {idx + 1}/{len(to_process)}")
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(cache, f, indent=2)

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
            
    print("Done populating cache.")

if __name__ == "__main__":
    main()
