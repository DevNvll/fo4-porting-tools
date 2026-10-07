"""The shared part of the port tools: paths and local settings (paths.py) and the ./port command.

A program that imports this package shows an error of a file (a wrong name on the command
line, a missing file) as one line. FO4PORTS_TRACEBACK=1 shows the full traceback.
"""
import os
import sys


def _file_error_in_one_line(kind, error, trace):
    if issubclass(kind, OSError) and not os.environ.get('FO4PORTS_TRACEBACK'):
        program = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else 'port'
        print('%s: %s  (FO4PORTS_TRACEBACK=1 shows the place in the program)' % (program, error), file=sys.stderr)
    else:
        sys.__excepthook__(kind, error, trace)


sys.excepthook = _file_error_in_one_line
