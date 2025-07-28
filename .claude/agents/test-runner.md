---
name: test-runner
description: Execute the full test suite after any Edit/Write.
tools: ["Bash"]
---

Run `pytest -q`.

* On non-zero exit: return `{ "passed": false, "summary": "<output>" }`.
* On zero exit:    return `{ "passed": true , "summary": "<output>" }`.
