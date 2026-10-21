# Preserved legacy application

`legacy/` contains the complete previous Studentdash application and its original
documentation, tests, examples, games/practice tools, question banks, exit tickets
and submission simulations. No legacy application source has been removed.
The new active application does not import this archive.

To use an older normalized workbook or an existing `.sdclass` workflow, install
`archive/legacy/requirements.txt` in a separate virtual environment, change into
`archive/legacy`, and run its `teacher.py`. It also binds to 127.0.0.1:5000, so stop
the active server first. Original setup instructions are in `legacy/README.md`.
Copy private workbooks/databases into the legacy data directory separately if needed;
archiving source does not migrate or alter private data.

Legacy regression tests run from that directory with its directory on PYTHONPATH.
Some legacy tests require optional Playwright and access to `file://` URLs, which
the managed cloud browser may block. They are separate from the active assessment
application tests in the root `tests/` directory.
