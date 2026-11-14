# Exam questions

Open `/tree/`, expand **Exam questions**, import reviewed JSON and turn the mode on.
Click **Exam marks** on a node for contributing papers and question parts.
Student results and confidence remain separate. Exam mode temporarily shows the full tree,
ignoring the student timeline; turning it off restores the student time view.

Counts cover only imported papers and reviewed allocations, not predicted exam weighting.
Select SL/HL papers; specimens are excluded unless enabled. An empty bank displays a dash.
Papers shared between SL/HL are separate exam opportunities when both are selected.

Import replaces the bank saved in this browser. Keep the source JSON for backup or another computer.
No exams or question text are bundled. Upload papers with markschemes to prepare mappings.
For older syllabuses, map only questions applicable to current nodes; leave others unallocated.

```json
{
  "schemaVersion": "1.0",
  "papers": [{
    "id": "unique-session-level-paper-zone",
    "title": "Paper title",
    "year": 2025,
    "level": "SL",
    "kind": "exam",
    "questions": [{
      "number": "2(a)",
      "marks": 3,
      "allocations": []
    }]
  }]
}
```

Use `kind: "specimen"` for specimens. Each allocation is
`{"nodeId": "exact registry node ID", "marks": 2}`. Use IDs from
`tree/local-package/curriculum.json` after building locally. Split a multi-topic part's
marks between nodes; allocated marks must not exceed that part's available marks.
Empty allocations keep a question pending review. Do not give every topic the full question marks.
