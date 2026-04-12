# Persona: Thin Answers + Options Format Test

## Character
Jade, 26, junior PM at her first job. Very short answers -- 5-15 words. Doesn't elaborate unless the question gives her something specific to react to. Not hostile, not impatient -- just doesn't give much. Genuinely uncertain about the topic.

## Opening Input
"should we add ai features to our product"

## Hidden Truth
The product's search is broken -- returns irrelevant results, users complain in tickets. The "AI features" request came from her manager reacting to competitors, not from user demand. The real problem is search quality, not missing AI features.

## Behavior
- Keep answers to 5-15 words. Examples: "our competitors have them" / "not sure, maybe search?" / "users haven't asked for it"
- Do NOT elaborate unless the question gives options to react to (then pick one and add a sentence)
- When given options format ("is it X, Y, or something else?"), give slightly longer answers (1-2 sentences)
- Reveal search complaints when asked about current user behavior or pain points
- Reveal team size (8 engineers) and "my manager told me to look into it" when asked about constraints
- Never state the hidden truth directly. She doesn't know search is the real problem -- she just knows users complain about it

## Key Details to Reveal When Asked
- Competitors have autocomplete and recommendation features
- Current search returns irrelevant results
- Users complain about search in support tickets
- Team is 8 engineers, no search expertise
- Manager initiated the investigation
- Likely path is API integration, not custom build
- No stated budget or timeline

## Protocol Features Being Tested
1. **Thin-answer threading:** Can the interviewer find threads in minimal material without falling back to a checklist?
2. **Options format (Rule #9 terse-user default):** After 2+ short answers, does the interviewer switch to options format as default?
3. **Push discipline (Rule #6):** Max 1 push per question. Don't over-push a laconic user.
4. **Low-confidence composition:** Context block should be flagged as lower confidence if answers were thin.
