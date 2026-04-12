You are simulating an explore intake conversation. You will play BOTH the interviewer AND the user.

## Your task

1. Read the intake protocol below (the PROTOCOL section).
2. Read the persona card and their pre-written answers below (the PERSONA section).
3. Simulate the FULL intake conversation: interviewer question → user answer → interviewer question → user answer → ... → intake ends.
4. The interviewer must follow the protocol EXACTLY. The user responds with the pre-written answers in order (A1, A2, A3, etc.). If you run out of pre-written answers, write one more in-character answer, then the interviewer must stop.
5. After the conversation, score the interviewer on Register (1-5) and Flow (1-5) using the criteria in the EVALUATION section.

## Output format

```
### Conversation

**User (initial input):**
[initial input from persona]

**Interviewer Q1:**
[interviewer's first question, following protocol]

**User A1:**
[persona's A1]

**Interviewer Q2:**
[interviewer's second question, following protocol]

**User A2:**
[persona's A2]

... [continue until intake ends]

### Scores

**Register: X/5**
[2-3 sentences: what worked, what failed, specific feature-level evidence]

**Flow: X/5**
[2-3 sentences: what worked, what failed, specific evidence of thread-following or protocol leakage]
```

## IMPORTANT RULES FOR THE INTERVIEWER

- Stay on the user's problem. Every question should follow from what they just said.
- Use thread-and-steer: pick up the strongest unresolved thread from the user's last answer, use their exact phrase, ask about it.
- Run the sufficiency test BEFORE drafting each question (after Q1). If sufficient, stop.
- Sound like the user, not like a protocol. Match how they write — don't clean it up, don't elevate it.
- No analytical labels (constraints, stakes, assumptions) in questions.
- No announced transitions. No solving during intake. One question per message.
- Be HARSH in scoring. A 4/5 means "one failure mode remains." A 3/5 means "multiple structural issues."
