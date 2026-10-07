"""The command line of d2x as a program file, for `./port` and for a start with no `./port`:

    data/destiny/extract/venv/bin/python destiny/extract/d2x_cli.py COMMAND [ARGUMENTS]

It does the same as `python -m d2x COMMAND` with `destiny/extract` in PYTHONPATH.
The folder of this file is the first import folder, thus `import d2x` needs no PYTHONPATH here.
"""
import sys

sys.dont_write_bytecode = True      # no __pycache__ in the source tree

from d2x.__main__ import main       # noqa: E402

sys.exit(main())
