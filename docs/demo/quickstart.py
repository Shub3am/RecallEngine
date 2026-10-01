"""Library usage shown in the walkthrough video. Run from docs/demo after mvp-demo.tape creates /tmp/shop.db.
Must not need ANTHROPIC_API_KEY, so it never calls ask."""
from recall_engine import SearchEngine
from recall_engine.api import create_app
from recall_engine.sources import load_documents

passages = load_documents("sample-docs")
print(len(passages), "passages from", len({passage["source"] for passage in passages}), "files")

docs = SearchEngine.from_source("sample-docs")
for hit in docs.search("refund within 14 days", mode="bm25", top_k=2):
    print("bm25  ", hit["rank"], hit["passage_id"])

print("bool  ", [hit["passage_id"] for hit in docs.search("backups AND encrypted")])

for hit in docs.search("how do I get my money back", mode="hybrid", top_k=2):
    print("hybrid", hit["rank"], hit["passage_id"])

shop = SearchEngine.from_source("/tmp/shop.db", table="products")
print("sqlite", shop.search("desk", mode="bm25", top_k=1)[0]["name"])

app = create_app(docs, api_key="demo-key")
print("routes", [route.path for route in app.routes if route.path in ("/health", "/search", "/ask")])
