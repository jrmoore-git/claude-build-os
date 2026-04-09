---
name: qa
description: "Domain-specific QA validation. Go/no-go gate before /ship."
user-invocable: true
---

# /qa — Quality Assurance Check

Domain-specific validation beyond automated tests. Produces a go/no-go report.

## Procedure

### Step 1: Detect scope

Find the most recent topic artifact:
```bash
ls -t tasks/*-plan.md tasks/*-review.md 2>/dev/null | head -5
```

Extract the topic from the newest file. If unclear, ask the user.

### Step 2: Load context

Read the plan (if exists):
```bash
cat tasks/<topic>-plan.md 2>/dev/null
```

Read the review (if exists):
```bash
cat tasks/<topic>-review.md 2>/dev/null
```

Get the diff:
```bash
git diff HEAD --stat && git diff HEAD
```

### Step 3: Evaluate 5 dimensions

Work through each dimension. For each, note PASS or FAIL with a one-line reason.

**1. Test coverage:**
- For each changed `.py` or `.sh` file, check if a corresponding test file exists:
  ```bash
  ls tests/test_*.py
  ```
- New scripts without tests = FAIL.

**2. Regression risk:**
- Check for changed function signatures. Are all callers updated?
- Check for changed imports. Are all importers updated?
  ```bash
  git diff HEAD -- '*.py' | grep -E '^\+.*def |^\-.*def '
  ```

**3. Plan compliance:**
- If a plan exists: does the actual diff match the plan's `surfaces_affected`?
- Files changed but not in the plan? Files in the plan but not changed?

**4. Negative tests:**
- Are error paths covered? (bad input, missing files, timeouts)
- Check test files for assertions on error cases.

**5. Integration:**
- If imports or interfaces changed, are downstream consumers updated?
- If new scripts were added, are they referenced correctly (shebangs, paths)?

### Step 4: Run tests

```bash
bash tests/run_all.sh
```

If tests fail, note which ones.

### Step 5: Produce report

Determine overall result: `go` if all 5 dimensions PASS and tests pass. `no-go` otherwise.

Write `tasks/<topic>-qa.md`:
```yaml
---
topic: <topic>
qa_result: <go|no-go>
git_head: <current short SHA>
producer: claude-opus
created_at: <ISO datetime>
---
```

Below frontmatter, write the 5-dimension results as a checklist:
```
- [x] Test coverage: <reason>
- [x] Regression risk: <reason>
- [ ] Plan compliance: <reason for fail>
- [x] Negative tests: <reason>
- [x] Integration: <reason>

Tests: PASS (N passed) / FAIL (N failed)
```

### Step 6: Handoff

If `go`:
- "QA passed. Run `/review` then `/ship`."

If `no-go`:
- List the failing dimensions with specific fix suggestions.
- "Fix these, then `/qa` again."

## Important Notes

- QA is a SOFT gate in `/ship` — advisory, not blocking. But a `no-go` is a strong signal.
- This checks domain-specific quality that automated tests can't catch (plan compliance, signature changes, integration).
- Don't re-run the full test suite if the user just ran it — check the output timestamp.
