---
name: "test-mode-split"
description: "Spike test for skill mode splitting — DO NOT USE in production"
user_invocable: true
---

# Test Mode Split

This is a spike test. Two modes: `alpha` and `beta`.

## Routing

1. Parse the user's input for the mode keyword ("alpha" or "beta"). Default to "alpha" if unclear.
2. Read the corresponding mode file from this skill's directory:
   - Alpha: Read `.claude/skills/test-mode-split/mode-alpha.md` and follow its procedure exactly.
   - Beta: Read `.claude/skills/test-mode-split/mode-beta.md` and follow its procedure exactly.
3. After reading the mode file, execute its procedure step by step. Do not deviate.
