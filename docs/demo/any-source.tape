# Records docs/images/any-source.gif. Run from the repo root with the [all] extra installed:
#   vhs docs/demo/any-source.tape
# HOME points at a fresh directory so the index cache starts empty and your own cache is untouched.
Output docs/images/any-source.gif

Set Shell "bash"
Set FontSize 16
Set Width 1200
Set Height 720
Set Padding 24
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 30ms

Hide
Type `export PS1='$ ' HOME=$(mktemp -d) && cd docs/demo && rm -f /tmp/shop.db && sqlite3 /tmp/shop.db "create table products (sku text, name text, description text); insert into products values ('LC-100', 'Desk lamp', 'Warm LED lamp with a dimmer'), ('LC-200', 'Standing desk', 'Electric sit stand desk with memory presets'), ('LC-300', 'Monitor arm', 'Gas spring arm for one 32 inch monitor');" && clear`
Enter
Show

Type "ls sample-docs"
Enter
Wait /^\$\s*$/
Sleep 1.5s

Type `recall_engine search "refund within 14 days" --dataset sample-docs --top-k 3`
Enter
Wait@60s /^\$\s*$/
Sleep 3s

Type `recall_engine search "encrypted backups" --dataset sample-docs --top-k 2`
Enter
Wait@60s /^\$\s*$/
Sleep 3s

Type `recall_engine search "desk" --dataset /tmp/shop.db --table products --top-k 2`
Enter
Wait@60s /^\$\s*$/
Sleep 4s
