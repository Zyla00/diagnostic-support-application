import os
import json

folder_path = "choroby"

output_file = "choroby_wszystkie_30.json"

all_data = []

for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_data.extend(data)

output_path = os.path.join(folder_path, output_file)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f"Scalono {len(all_data)} rekordów do pliku: {output_path}")
