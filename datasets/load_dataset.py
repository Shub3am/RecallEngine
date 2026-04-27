import json
from pathlib import Path
from datasets import load_dataset

MAX_ROWS = 30000
MAX_PASSAGES_PER_QUERY = 5

ds = load_dataset("ms_marco", "v1.1", split=f"train[:{MAX_ROWS}]")

docs = []
seen = set()
doc_id = 0

for row in ds:
	passages = row.get("passages", {})
	texts = passages.get("passage_text", [])
	for text in texts[:MAX_PASSAGES_PER_QUERY]:
		t = (text or "").strip()
		if not t:
			continue
		if t in seen:
			continue
		seen.add(t)
		doc_id += 1
		docs.append({
			"id": str(doc_id),
			"title": "",
			"text": t
		})
output_path = Path("datasets") / "msmarco_passages.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as f:
	json.dump({"docs": docs}, f)

print("saved_docs", len(docs))
print("output", output_path)
