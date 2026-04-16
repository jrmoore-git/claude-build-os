# Handoff — 2026-04-15

## Session Focus
Validated D22 critique loop mechanism (spike proved directive injection degrades quality), tested /simulate smoke-test value (0 real issues), shelved entire sim ecosystem to archive/sim/.

## Decided
- D22 critique loop: wrong mechanism — runtime directive injection doesn't work; eval_intake improved by editing skill prompts directly (L32)
- /simulate smoke-test: no standalone value (0/23 real issues found, 29 false positives)
- Shelve all sim-related work: /simulate skill, 7 scripts, 5 test files, 40+ task artifacts → archive/sim/
- Skill count reduced 23→22

## Implemented
- 3v3 directive injection spike (critique_spike.py) — baseline 2.50 avg vs critique 1.78 avg
- 3-model pre-mortem on critique loop plan (all converged on "wrong mechanism")
- /simulate smoke-test against all 23 skills (simulate_value_test.py)
- Full sim archival to archive/sim/ (96 files moved)
- Doc cleanup: CLAUDE.md, README, cheat-sheet, routing rules, intent router — all /simulate references removed
- D9 read-before-edit hook committed (from session 16)
- .gitignore updated for .claude/projects/

## NOT Finished
- Nothing outstanding
- Context-packet-anchors has challenge+judgment on disk (now in archive/sim/tasks/)

## Next Session Should
1. Choose next product work — context-packet-anchors or something new
2. Push to GitHub if not done

## Key Files Changed
- archive/sim/ (new — 96 files archived)
- CLAUDE.md, README.md, docs/cheat-sheet.md (skill count + references)
- .claude/rules/natural-language-routing.md (removed simulate entries)
- hooks/hook-intent-router.py (removed simulate pattern)
- tasks/lessons.md (added L32)

## Doc Hygiene Warnings
- None
