# Search

A user searches titles case-insensitively and sees an empty array for no matches.

Run `python3 -m unittest discover -s tests -p test_search.py -v` from the
project root. The test creates its own disposable state and exercises the CLI
in fresh processes. Retain the runner result.
