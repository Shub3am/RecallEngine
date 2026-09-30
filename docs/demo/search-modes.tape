# Records docs/images/search-modes.gif. Run from the repo root with the [all] extra installed:
#   vhs docs/demo/search-modes.tape
Output docs/images/search-modes.gif

Set Shell "bash"
Set FontSize 16
Set Width 1200
Set Height 640
Set Padding 24
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 30ms

Hide
Type "export PS1='$ ' && clear"
Enter
Show

Type `recall_engine search "bank heist" --dataset datasets/movies.json --top-k 3`
Enter
Wait@60s /^\$\s*$/
Sleep 2.5s

Type `recall_engine search "space AND (alien OR robot) AND NOT comedy" --mode boolean | head -6`
Enter
Wait@60s /^\$\s*$/
Sleep 2.5s

Type `recall_engine search "robots rebel against their creators" --mode hybrid --top-k 3`
Enter
Wait@90s /^\$\s*$/
Sleep 4s
