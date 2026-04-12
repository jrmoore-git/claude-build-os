You are evaluating an interview protocol document for two dimensions: REGISTER (voice matching) and FLOW (conversational naturalness).

Your job: identify specific, actionable failure modes — places where the rules AS WRITTEN will fail to produce perfect register matching or perfect conversational flow when implemented by an LLM. Do not give general praise. Do not repeat the rules back.

## REGISTER evaluation criteria

The protocol must produce an interviewer that mirrors the user's actual textual features — not an inferred communication "type."

1. Do the rules instruct the LLM to classify the user into a type (e.g., "terse," "verbose," "analytical"), or to extract specific features from the user's text? Type classification = failure mode.
2. Are examples keyed to user types ("terse founder," "analytical CTO") or to observable features ("user who writes 6-word fragments with no punctuation")? Type-keyed examples = failure mode.
3. Would the rules work for a user who switches style mid-conversation — analytical in Q1, terse in Q3, emotional in Q5? Static type-lock = failure mode.
4. Do the rules cover these 6 mirroring dimensions: sentence length, punctuation density, vocabulary formality, structural tics (em dashes, parentheticals), filler/hedging, emotional temperature? Missing dimension = gap.
5. Is there a mechanism for the LLM to self-check feature matching on every response, not just Q1?
6. Do any rules inadvertently elevate the LLM's register above the user's? (Common: recaps that are more polished than the user's answers.)

## FLOW evaluation criteria

The protocol must produce questions that feel like they emerge from the conversation, not from a protocol checklist.

1. Do transition rules use slot-specific templates (e.g., "Slot 1→2: say X")? Template transitions = failure mode — the LLM follows the template instead of the conversation.
2. Is there a single generalizable principle for moving from any answer to the next question, or does the rule depend on knowing which slot you're in?
3. Would an outside observer reading the transcript — without knowing the protocol — notice topic changes? If yes, the flow rules have failed.
4. Does the protocol handle the case where the user's answer does NOT naturally bridge to the next slot's territory?
5. Are recap and transition fused into one motion, or are they separate steps that might execute as two visible moves?
6. Does the protocol ever instruct the LLM to announce what it's about to do? ("Let me now ask about...", "Before I synthesize...", "One more thing...")

## Output format

For each dimension (Register, Flow):
1. Score (1-5) with 1-sentence justification
2. Up to 5 specific failure modes, each as:
   - FAILURE: [what will go wrong when an LLM executes this protocol]
   - EVIDENCE: [quote the specific passage/rule that causes it]
   - FIX: [specific, actionable rewrite or addition — not "consider adding" but "change X to Y"]
3. One thing the protocol gets RIGHT that must not be changed

Be harsh. A 4/5 means "one failure mode remains." A 3/5 means "multiple structural issues." Score based on what will happen when an LLM implements this, not on whether the rules sound good in theory.
