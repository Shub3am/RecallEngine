# Records docs/demo/recallengine-demo.mp4, the end-to-end product walkthrough.
# Run from the repo root with the [all] extra installed:
#   vhs docs/demo/mvp-demo.tape
# HOME points at a fresh directory so the index cache starts empty and your own cache is untouched.
Output docs/demo/recallengine-demo.mp4

Set Shell "bash"
Set FontSize 18
Set Width 1280
Set Height 760
Set Padding 28
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 35ms
# 15 fps keeps frame capture in step with the sleeps on a loaded machine; at 50 fps vhs drops frames and pauses shrink.
Set Framerate 15

Hide
Type `export PS1='$ ' HOME=$(mktemp -d) && cd docs/demo && rm -f /tmp/shop.db && sqlite3 /tmp/shop.db "create table products (sku text, name text, description text); insert into products values ('LC-100', 'Desk lamp', 'Warm LED lamp with a dimmer'), ('LC-200', 'Standing desk', 'Electric sit stand desk with memory presets'), ('LC-300', 'Monitor arm', 'Gas spring arm for one 32 inch monitor');" && clear`
Enter
# A bare vim keeps the reader's vimrc out of the recording.
Type `alias vim="vim -Nu NONE -R -c 'syntax on | set number'" && clear`
Enter
Show

Type "# RecallEngine: search and cited answers over files, folders and databases"
Enter
Sleep 1s
Type "# A folder of mixed formats: Markdown, PDF, CSV, Word, HTML, JSONL, Excel"
Enter
Type "ls sample-docs"
Enter
Wait /^\$\s*$/
Sleep 2.5s
Type "clear"
Enter

Type "# As a library: the engine, the source loader and the HTTP app"
Enter
Type "vim quickstart.py"
Enter
Sleep 10s
Type ":q"
Enter
Type "python quickstart.py"
Enter
# Indexing and the first hybrid query take minutes on a busy machine, so the wait is cut out.
Hide
Wait+Screen@600s /routes \[/
Show
Sleep 6s
Type "clear"
Enter

Type "# The same from the CLI. Every file is parsed, split into passages and indexed"
Enter
Type `recall_engine search "refund within 14 days" --dataset sample-docs --top-k 3`
Enter
Wait@90s /^\$\s*$/
Sleep 4s

Type "# Boolean queries with AND, OR, NOT and parentheses"
Enter
Type `recall_engine search "backups AND encrypted" --dataset sample-docs --mode boolean`
Enter
Wait@90s /^\$\s*$/
Sleep 4s
Type "clear"
Enter

Type "# A SQLite file works the same way: one document per row"
Enter
Type "sqlite3 /tmp/shop.db 'select * from products'"
Enter
Wait /^\$\s*$/
Sleep 2s
Type `recall_engine search "desk" --dataset /tmp/shop.db --table products --top-k 2`
Enter
Wait@90s /^\$\s*$/
Sleep 4s
Type "clear"
Enter

Type "# Serve the folder over HTTP with an API key"
Enter
Type "export RECALL_ENGINE_API_KEY=demo-key"
Enter
Type "recall_engine serve --dataset sample-docs --port 8765 >/dev/null 2>&1 &"
Enter
Sleep 1s
Hide
# The first semantic query loads the embedding model; that wait happens off camera.
Type `until curl -s localhost:8765/health >/dev/null; do sleep 0.5; done; curl -s localhost:8765/search -H 'X-API-Key: demo-key' --json '{"query": "warm up", "mode": "semantic", "top_k": 1}' >/dev/null; clear`
Enter
Wait@600s /^\$\s*$/
Show
Type `curl -s -w '\n' localhost:8765/health`
Enter
Wait /^\$\s*$/
Sleep 2s

Type "# Without the key: 401"
Enter
Type `curl -s -w '\n' localhost:8765/search --json '{"query": "refund"}'`
Enter
Wait /^\$\s*$/
Sleep 2.5s

Type "# Hybrid search: BM25 plus embeddings, so meaning matches without the exact words"
Enter
Type `curl -s localhost:8765/search -H 'X-API-Key: demo-key' --json '{"query": "how do I get my money back", "mode": "hybrid", "top_k": 3}' | jq -c '.results[] | {rank, passage_id, source}'`
Enter
# The prompt regex can match before a slow hybrid query answers, so wait for the third result itself.
Wait+Screen@180s /"rank":3/
Sleep 5s
Type "clear"
Enter

Type "# With ANTHROPIC_API_KEY set, ask answers from these passages with numbered citations:"
Enter
Type `# recall_engine ask "How long do customers have to ask for a refund?" --dataset sample-docs`
Enter
Type "# POST /ask does the same over HTTP. Interactive docs live at /docs"
Enter
Sleep 5s

Hide
Type "kill %1"
Enter
