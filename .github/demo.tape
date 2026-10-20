# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Rendered with `make demo` (VHS, https://github.com/charmbracelet/vhs)
# from a virtual environment where the package is installed. Runs the
# repository's own example against the MT940 text it ships; no network.

Output .github/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 640
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms

Hide
Type "export PS1='$ ' && clear"
Enter
Show

Type `sed -n '/^MT940 = /,/^"""$/p' examples/01_minimal_parse.py`
Enter
Sleep 3s

Type "python examples/01_minimal_parse.py"
Enter
Sleep 4s

Type "printf ':20:NO-ACCOUNT\n:60F:C260620EUR1,00\n' | python -c 'import sys; from camt053_loader_mt940 import parse_mt940; parse_mt940(sys.stdin.read())' 2>&1 | tail -1 | fold -w 110"
Enter
Sleep 5s
