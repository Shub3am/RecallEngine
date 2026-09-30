# Records docs/images/http-api.gif. Run from the repo root with the [all] extra installed:
#   vhs docs/demo/http-api.tape
Output docs/images/http-api.gif

Set Shell "bash"
Set FontSize 16
Set Width 1200
Set Height 680
Set Padding 24
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 30ms

Hide
Type "export PS1='$ '; RECALL_ENGINE_API_KEY=demo-key recall_engine serve --dataset datasets/movies.json >/dev/null 2>&1 &"
Enter
Type `until curl -s localhost:8000/health >/dev/null; do sleep 0.5; done; curl -s localhost:8000/search -H 'X-API-Key: demo-key' --json '{"query": "warm up", "mode": "semantic", "top_k": 1}' >/dev/null; clear`
Enter
# The server loads the index, then the embedding model on the first semantic query; both happen off camera.
Wait@600s /^\$\s*$/
Show

Type `curl -s -w '\n' localhost:8000/health`
Enter
Sleep 1s
Sleep 1.5s

Type `curl -s -w '\n' localhost:8000/search -d '{"query": "heist"}'`
Enter
Sleep 1s
Sleep 2s

Type `curl -s localhost:8000/search -H 'X-API-Key: demo-key' --json '{"query": "robots rebel", "mode": "hybrid", "top_k": 3}' | jq -c '.results[] | {rank, title}'`
Enter
Wait@120s /^\$\s*$/
Sleep 4s

Hide
Type "kill %1"
Enter
