# Research: Effective Questioning Techniques for AI Intake

**Purpose:** Evidence base for designing the explore mode's 3-5 intake questions.
**Date:** 2026-04-11

---

## 1. Socratic Questioning

### The Six Types (Richard Paul taxonomy)

1. **Clarification** -- "Why do you say that?" / "Could you explain further?" / "What do you mean by X?"
2. **Probing assumptions** -- "What are you assuming here?" / "Is this always the case?" / "Why do you think that assumption holds?"
3. **Probing evidence/reasons** -- "What evidence supports this?" / "Is there reason to doubt that?" / "How do you know?"
4. **Exploring viewpoints/perspectives** -- "What's the counter-argument?" / "Could someone see this differently?" / "What would [person] say?"
5. **Probing implications/consequences** -- "If that happened, what else would result?" / "How does that affect X?"
6. **Meta-questions (questions about the question)** -- "Why is this question important?" / "Which of our questions was most useful?"

### What the evidence says

- **CBT outcome data:** A one standard deviation increase in therapist Socratic questioning predicted a 1.51-point decrease in depression scores (BDI-II) session-to-session (Braun et al., PMC4449800). Effect was independent of therapeutic alliance quality -- the questioning itself was the active ingredient.
- **Educational outcomes:** Students strongly prefer Socratic to didactic instruction (93.3% in one medical education study). Linked to better critical thinking and higher-order reasoning.
- **Mechanism:** Works by activating metacognition -- making people think about *how* they think, not just *what* they think. Questions about the "deep structure" of problems transfer knowledge across contexts.

### When it fails

- **Without foundational knowledge:** Students/users can't engage with Socratic questions if they lack domain context. "One cannot think critically about an issue in which they have no point of reference." (PMC4174386)
- **"Pimping" failure mode:** Rapid-fire difficult questions without safety become adversarial interrogation, not inquiry. Creates shame/defensiveness.
- **Predictability:** Over-reliance on Socratic questions becomes robotic and formulaic.
- **Scale:** Designed for 1:1 dialogue. Loses effectiveness in groups.
- **No empirical validation of sequencing:** Research shows Socratic questioning predicts outcomes, but there's surprisingly little evidence on optimal *sequencing* of question types.

### Transferable principles for AI intake

- **Type 1 (clarification) should come first.** It's lowest cognitive load and establishes shared vocabulary.
- **Type 2 (assumptions) is the highest-value question type for intake.** It surfaces the gap between what users say and what they actually mean.
- **Type 4 (alternative perspectives) is the reframing engine.** "What would someone who disagrees with you say?" breaks default framing.
- **Type 6 (meta-questions) is surprisingly powerful as a closing question.** "What question should I have asked you?" (echoes Steve Blank's technique).
- **Wait time matters:** Research suggests 20 seconds to 2 minutes of processing time depending on question complexity. An AI chat interface should not rush -- give explicit permission to think.

**Sources:**
- [Socratic Questioning - Wikipedia](https://en.wikipedia.org/wiki/Socratic_questioning)
- [Therapist Use of Socratic Questioning Predicts Symptom Change - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4449800/)
- [The Fact of Ignorance: Revisiting the Socratic Method - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4174386/)
- [Socratic Questioning in Psychology - Positive Psychology](https://positivepsychology.com/socratic-questioning/)
- [Evaluating the Socratic Method - Philosophy Institute](https://philosophy.institute/western-philosophy/evaluating-socratic-method-benefits-limitations/)

---

## 2. Motivational Interviewing (MI)

### OARS Framework

- **Open questions** -- At least 70% of questions should be open-ended. "What worries you about X?" not "Are you worried about X?"
- **Affirmations** -- Validate the person's experience and effort. "You've clearly thought about this a lot."
- **Reflections** -- Mirror back what was said, often adding inferred meaning. At least 2 reflections per question asked. At least 50% should be "complex reflections" that go beyond simple paraphrase.
- **Summaries** -- Collect and restate key points. Different types: collecting (narrative), linking (connecting statements), transitional (moving forward), ambivalence (acknowledging both sides).

### The Four Processes of MI

1. **Engaging** -- Build trust. Open questions, affirmations, reflective listening. Avoid premature focus.
2. **Focusing** -- Collaboratively identify what to work on. Agenda mapping when multiple issues exist.
3. **Evoking** -- Draw out the person's own motivations. This is the MI differentiator.
4. **Planning** -- Convert insight to action. Elicit-Provide-Elicit pattern.

### How MI surfaces real intent vs. stated intent

**The Columbo Approach:** Practitioner expresses understanding but appears unable to see how the person's goals align with their behavior. This creates productive confusion that prompts the person to articulate the real discrepancy themselves.

**Double-Sided Reflections:** Pair what someone says they want with their actual behavior. Example: "You want your baby to be healthy, AND you're worried you can't quit smoking." The "and" (not "but") holds both truths simultaneously, forcing the person to sit with the tension.

**Developing Discrepancy:** Surface the gap between current behavior and stated values. Use values clarification ("What's important to you?") then contrast with current reality. The cognitive dissonance becomes the motivation engine.

**Importance/Confidence Rulers (Scaling Questions):**
- "On a scale from 0-10, how important is it for you to [change X]?"
- Follow-up: "Why not a lower number?" (This is critical -- asking "why not higher?" elicits reasons NOT to change. Asking "why not lower?" elicits reasons TO change.)
- "What would it take to move from a 6 to a 9?"

**Change Talk vs. Sustain Talk:**
- DARN (preparatory): Desire, Ability, Reasons, Need
- CAT (mobilizing): Commitment, Activation, Taking steps
- Good questioning evokes change talk; bad questioning evokes sustain talk (reasons to stay the same)

### The Righting Reflex (critical failure mode)

The natural impulse to immediately "fix" the person's problem. When practitioners jump to solutions, people defend the status quo. MI's core insight: **the person who argues for change is the one who changes.** If the helper argues for change, the person argues against it.

### Seven Traps That Create Discord

1. **Expert Trap** -- Acting like you know better
2. **Labeling Trap** -- Forcing categories ("So your real problem is...")
3. **Question-and-Answer Trap** -- Rapid-fire closed questions create interrogation
4. **Premature Focus Trap** -- Pushing an agenda the person isn't ready for
5. **Blaming Trap** -- Focusing on causes rather than understanding

### Evidence base

- Meta-analysis: OR = 1.55 (95% CI: 1.40-1.71) comparing MI to standard treatment
- Strongest effects for substance use, physical activity, treatment adherence
- Technical hypothesis has strongest empirical support: effectiveness occurs through selective reinforcement of self-motivational utterances via OARS skills
- Reflection-to-question ratio predicts outcomes: 2:1 minimum, higher is better

### Transferable principles for AI intake

- **The 2:1 reflection-to-question ratio is directly applicable.** For every question asked, the AI should reflect back what it heard before asking the next question. This prevents the Question-and-Answer Trap.
- **"Why not lower?" is a specific, replicable technique.** After any self-assessment, ask why the situation isn't worse -- this surfaces the positive forces already at work.
- **The Righting Reflex is the #1 risk for an AI system.** LLMs are trained to be helpful, which means they default to fixing. The intake phase must resist solving.
- **Elicit-Provide-Elicit pattern:** Ask what they know -> offer a framing -> ask for their reaction. Never just provide information.
- **Sustain talk detection:** If the user starts defending their current approach or explaining why change is hard, the AI's questions are probably pushing too hard on a direction the user hasn't chosen.

**Sources:**
- [MI: Evidence-Based Approach in Medical Practice - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8200683/)
- [Chapter 3: MI as Counseling Style - NCBI Bookshelf](https://www.ncbi.nlm.nih.gov/books/NBK571068/)
- [OARS in Motivational Interviewing - Relias](https://www.relias.com/blog/oars-motivational-interviewing)
- [MI Importance Ruler - UNC CFAR](https://www.med.unc.edu/cfar/2025/11/conversations-about-change-using-the-importance-ruler/)
- [Developing Discrepancy in MI](https://miinlondon.org/developing-discrepancy-in-motivational-interviewing)

---

## 3. Design Thinking / User Research Interviews

### The Funnel Technique (Nielsen Norman Group)

Three-stage progression from broad to narrow:

1. **Stage 1: Broad exploration** -- "Tell me about the last time you ordered movie tickets." No direction, no framing. Collect organic, unprimed responses.
2. **Stage 2: Targeted open-ended followup** -- "Can you expand on that?" / "Why do you think that?" Probe the threads that emerged naturally.
3. **Stage 3: Specific closed questions** -- "When did you see this movie?" / "Did you go alone?" Only after you've collected unbiased data.

**Key principle:** Early specificity introduces bias and misses critical unbiased information. The funnel preserves validity by collecting organic feedback first.

### d.school Empathy Interviews (Stanford)

Core practices:
- **Pursue tangents** -- Don't steer back to your script. Emotionally-charged digressions reveal genuine insights.
- **Beginner's mindset** -- "Never assume you know the answer. Always ask why."
- **Ask neutral questions** -- Not "What frustrations do you have?" but "What do you think about...?"
- **Encourage storytelling** -- Not "Do you like your car?" but "Tell me about the last time you drove your car."
- **Embrace silence** -- Let the participant break the pause. They're reflecting.
- **Avoid binary questions** -- Move beyond yes/no to enable deeper exploration.

### Jobs-to-be-Done (JTBD) Interview Methodology

**Core insight:** People don't buy products, they "hire" them for a job. The interview traces the switching timeline.

**The Four Forces of Progress:**
1. **Push** -- What's wrong with the current situation? What pain triggered the search?
2. **Pull** -- What attracted them to the new solution? What did they imagine it would be like?
3. **Anxiety** -- What fears do they have about the new approach? What could go wrong?
4. **Habit** -- What keeps them doing things the old way? What's comfortable about the status quo?

**Key technique: The Timeline.** Walk backward through the decision:
- First thought ("When did you first realize you needed something different?")
- Passive looking ("What did you notice? What caught your attention?")
- Active looking ("What did you compare? What criteria did you use?")
- Deciding ("What tipped the balance?")

**Interview mechanics:**
- One opening question, then follow threads: "Tell me about how you came to [use/decide/buy] ___"
- Use sensory anchors: "Where were you? What time of day? Who was with you?" -- details trigger associated memories and emotions
- Embrace 10-20 seconds of silence. People are often reconstructing memories.
- Be non-linear: bounce between topics and circle back. Each return unlocks new details.

### Five Whys (Toyota)

- Iterative "why?" to trace from symptom to root cause
- Not literally 5 -- sometimes 3 is enough, sometimes you need more
- **Critical rule:** Never identify a person as root cause. Only systemic/structural causes.
- **Limitation:** Too shallow for complex multi-causal problems. Arbitrary depth. Requires participants with actual knowledge.
- **When it works:** Simple causal chains with a single root. When you have the right people in the room.

### Transferable principles for AI intake

- **The funnel sequence is the backbone:** Start broad ("What are you trying to figure out?"), then targeted followups, then specific closed questions only after understanding the landscape.
- **"Tell me about the last time..." is the single most powerful question opening.** It forces concrete narrative instead of abstract opinions.
- **The Four Forces framework maps directly to explore intake:** Push (what's wrong now), Pull (what would good look like), Anxiety (what could go wrong), Habit (what have you already tried). These four dimensions fully characterize a decision context.
- **Sensory/contextual anchoring retrieves richer information.** "What specifically happened that made you think about this?" beats "Why do you want this?"
- **Silence is a feature, not a bug.** The AI should explicitly invite reflection: "Take a moment to think about this -- there's no rush."

**Sources:**
- [The Funnel Technique in Qualitative User Research - NNg](https://www.nngroup.com/articles/the-funnel-technique-in-qualitative-user-research/)
- [JTBD Interviewing Style - Dscout](https://dscout.com/people-nerds/the-jobs-to-be-done-interviewing-style-understanding-who-users-are-trying-to-become)
- [How to Conduct Empathy Interviews - Zion & Zion](https://www.zionandzion.com/how-to-conduct-empathy-interviews/)
- [6 Tips from IDEO Designers - IDEO U](https://www.ideou.com/blogs/inspiration/6-tips-from-ideo-designers-on-how-to-unlock-insightful-conversation)
- [Five Whys - Wikipedia](https://en.wikipedia.org/wiki/Five_whys)
- [d.school Empathy Interview Guide](https://practices.learningaccelerator.org/artifacts/stanford-d-school-empathy-interview-guide)

---

## 4. Coaching Methodology

### GROW Model (Whitmore)

Four stages, each with distinct question functions:

**Goal** -- Activate motivation and direction
- "What would make this conversation feel successful for you?"
- "If progress happened, what would it look or feel like?"
- "Why does this matter to you now?"
- "Is this within your control?"

**Reality** -- Surface honest assessment through specificity
- "What's actually happening right now?"
- "What have you already tried?"
- "Where do you feel stuck?"
- "What assumptions might be influencing your thinking?"
- "What might you be avoiding?"

**Options** -- Expand thinking without constraint
- "What are all the ways you could approach this?"
- "If nothing were off the table, what might you try?"
- "What advice would you give someone else in this situation?"
- "Which options feel exciting versus forced?"

**Will** -- Convert insight to commitment
- "What will you actually do?"
- "What's your first step?"
- "When will you do it?"
- "What if you hit a roadblock?"

**Evidence:** Kang, Lee & Joung (2021) found GROW with nursing students showed stronger motivation and clearer planning. Scoular & Linley (2006) found coach presence and relationship quality matter more than the model itself.

### ICF Powerful Questions

The International Coach Federation defines powerful questions as those that:
- Reflect active listening and understanding of the client's perspective
- Evoke discovery, insight, commitment, or action
- Challenge assumptions
- Are open-ended, creating possibility or creative learning
- Move toward what the client desires (not dwelling in the past or justifying)

**Key distinction:** The most powerful questions are customized and contextual, not from a script. Generic "What do you want?" is weak. "You mentioned wanting to feel less reactive in meetings -- what would responsive look like instead?" is powerful because it uses the person's own language.

### Solution-Focused Techniques

**The Miracle Question:** "Suppose tonight while you sleep, a miracle happens and the problem vanishes -- but you don't know it happened because you were asleep. When you wake up tomorrow, what's the first thing that tells you the miracle happened?"

Why it works: It bypasses the problem-analysis loop entirely and forces the person to articulate their desired end state in concrete, behavioral terms. The therapist then works backward from that vision.

**Scaling Questions:** "On a scale of 0-10, where are you now?" followed by "What would one number higher look like?" Forces precision and reveals the person's own theory of progress.

### Transferable principles for AI intake

- **GROW's stage sequence maps well to 3-5 questions:** Q1 = Goal (what success looks like), Q2 = Reality (what's actually happening), Q3 = Options/constraints (what you've tried, what's blocking you). Will is the AI's output phase, not an intake question.
- **"What advice would you give someone else?" is a decentering technique** that bypasses emotional attachment to the problem. Directly applicable.
- **The Miracle Question's mechanism is reusable:** "If this problem were completely solved tomorrow, what would be different?" reveals the actual desired outcome, which is often different from the stated goal.
- **Use the person's own language.** Don't rephrase into your terminology. This is the Clean Language principle and ICF powerful questions principle combined.
- **"What might you be avoiding?"** is a high-risk/high-reward question. Powerful when trust is established, alienating when it isn't. Save for later in the sequence.

**Sources:**
- [GROW Coaching Model Explained - Simply.Coach](https://simply.coach/learn-coaching-models/grow-coaching-model-explained-with-tips-and-real-examples/)
- [ICF Powerful Coaching Questions](https://www.lifecoachcertification.com/files/2814/4782/0036/ICF-Powerful-Coaching-Questions.pdf)
- [100 Coaching Questions - Bailey Balfour](https://baileybalfour.com/100-powerful-coaching-questions-for-your-toolkit/)
- [The Miracle Question - Positive Psychology](https://positivepsychology.com/miracle-question/)
- [Solution-Focused Questions - Universal Coach Institute](https://www.universalcoachinstitute.com/solution-focused-questions/)

---

## 5. CBT Intake / Clinical Assessment

### The Downward Arrow Technique

The core method for getting from the "presenting problem" to the "real problem":

**Procedure:**
1. Identify a surface-level thought or concern
2. Ask: "If that were true, what would it mean?"
3. Client answers with a deeper belief
4. Ask: "And if THAT were true, what would it mean about you/the situation?"
5. Repeat until you hit a core belief (simple, powerful, emotionally charged)

**Example chain:**
- "I don't think my boss liked my presentation" (surface)
- -> "What would that mean?" -> "I'm not good at my job" (intermediate)
- -> "What would that mean?" -> "I'll probably get fired" (intermediate)
- -> "What would that mean?" -> "Everyone will see I'm a failure" (core belief)

**Key mechanics:**
- Focus on MEANING, not content. Don't analyze the presentation -- ask what it means.
- The phrasing must come from the patient/user, not the therapist. Don't put words in their mouth.
- Monitor emotional shifts -- increasing emotion indicates proximity to core beliefs.
- Common core beliefs cluster around: helplessness ("I'm incompetent"), unlovability ("I'm unworthy"), worthlessness ("I'm a failure").

### CBT Three-Level Belief Structure

1. **Automatic thoughts** -- Quick, surface reactions to situations
2. **Intermediate beliefs** -- Rules, expectations, conditional assumptions ("If I fail, then...")
3. **Core beliefs** -- Deep convictions about self, others, world

The intake challenge is that people present automatic thoughts but the real problem lives at the core belief level.

### Transferable principles for AI intake

- **The Downward Arrow is directly implementable as a follow-up pattern.** After any statement of the problem, ask "And if that happened, what would that mean for you?" This drills toward what actually matters.
- **Three levels map to AI intake:** Users present a surface question (automatic thought), which masks an intermediate concern (what they're actually trying to do), which masks a core need (why it matters). The intake should traverse all three.
- **"What would it mean?" is the skeleton key question.** It works in almost any context to go one level deeper.
- **Watch for emotional markers.** In text, this might be: longer responses, more personal language, qualifications ("well, actually..."), or hedging. These indicate proximity to the real issue.

**Sources:**
- [Downward Arrow Technique - Therapist Aid](https://www.therapistaid.com/therapy-guide/downward-arrow-technique)
- [CBT Case Conceptualization - Psychology Town](https://psychology.town/rehabilitation-assessment-counseling/how-case-conceptualization-shapes-cbt/)
- [Case Conceptualization - Counseling.org](https://www.counseling.org/publications/counseling-today-magazine/article-archive/article/legacy/case-conceptualization-key-to-highly-effective-counseling)

---

## 6. Journalism / Investigative Questioning

### The Funnel Technique (Journalism Variant)

Same principle as UX research funnel but with additional tactical layers:

1. **Wide open:** Let the source tell their story uninterrupted
2. **Probing:** Follow threads with "Tell me more about..."
3. **Specific:** Pin down details: who, what, when, where
4. **Closed:** Confirm specific facts

**Key journalism principle:** Long, rambling questions get long, rambling answers (or allow evasion). Questions should be short and precise.

### Intelligence Elicitation Techniques (FBI/CIA)

Professional elicitors use these principles to get information without the subject realizing they're being questioned:

**Psychological levers:**
- **Need to be polite** -- People dislike shutting down questions
- **Desire to appear knowledgeable** -- People enjoy demonstrating expertise
- **Urge to correct mistakes** -- Humans feel compelled to "set the record straight" when someone is wrong
- **Comfort of shared experience** -- People open up when they feel understood

**Specific techniques (from FBI training):**
- **Deliberate false statements** -- State something slightly wrong; the person corrects you with the real information. (Not directly applicable to AI, but the principle is: sometimes a wrong assumption surfaces the right answer faster than a question.)
- **Progressive topic escalation** -- Start with harmless topics, gradually move toward sensitive ones, then retreat back to safety. Circle back later.
- **Flattery/ego appeal** -- Complimenting someone's knowledge prompts them to demonstrate it.

**Key finding:** Rapport-based interviewing is 5x more effective at obtaining comprehensive accounts than confrontational approaches (HIG research). Empathy displays significantly increase information elicitation.

### Cognitive Interview Protocol (Fisher & Geiselman)

Originally developed for eyewitness testimony, but principles transfer:

**Four techniques:**
1. **Context reinstatement** -- Mentally recreate the environment. "Think back to when this was happening -- where were you? What was going on around you?"
2. **Report everything** -- Even partial/uncertain information. "Don't edit yourself -- include details even if you're not sure they matter."
3. **Change order** -- Recall events in different sequences to trigger different memory paths.
4. **Change perspective** -- "How would someone else in that situation describe what happened?"

**Evidence:** 35-50% more correct information recalled vs. standard interview. Some studies show 100% improvement. The combination of "report everything" + "context reinstatement" outperformed any single technique.

### Transferable principles for AI intake

- **Short, precise questions.** The journalism rule transfers directly. Long questions with multiple clauses let users answer only the easy part.
- **The "deliberate wrong statement" principle:** In AI context, this becomes "offer a tentative frame and invite correction." "It sounds like you're trying to [X] -- is that right, or am I misreading this?" People correct wrong framings more readily than they generate accurate framings from scratch.
- **Context reinstatement works for problem recall.** "Think back to when you first started thinking about this -- what was happening?" triggers richer, more specific responses than "What's the problem?"
- **"Don't edit yourself"** is a valuable meta-instruction. Users self-censor because they think some details aren't relevant. Explicitly inviting "messy" thinking yields better signal.
- **Progressive escalation:** Start with safe, low-stakes questions. Build toward the harder ones.

**Sources:**
- [Introduction to Investigative Journalism: Interview Techniques - GIJN](https://gijn.org/resource/introduction-investigative-journalism-interview-techniques/)
- [The Funnel Technique - Fiveable](https://library.fiveable.me/key-terms/hs-journalism/funnel-technique)
- [Accidental Conversations: Elicitation Techniques - CDSE](https://www.cdse.edu/Portals/124/Documents/jobaids/ci/Accidental-Conversations.pdf)
- [Motivational Interviewing - FBI Law Enforcement Bulletin](https://leb.fbi.gov/articles/featured-articles/motivational-interviewing)
- [Cognitive Interview Technique - Simply Psychology](https://www.simplypsychology.org/cognitive-interview.html)

---

## 7. Academic Research on Question Effectiveness

### The Question-Behavior Effect (QBE)

**Core finding:** Simply asking people about a behavior changes the probability they'll perform that behavior.

**Effect size:** Small but reliable. Meta-analysis: g = 0.14 (p < .001) across 116 studies. Larger effect (d = 0.24) when specifically asking about intentions/predictions.

**Mechanism:** Primarily attitude accessibility. Asking about a behavior makes existing attitudes toward it more salient, which then guides behavior. This is automatic, not effortful.

**Implication for AI intake:** The questions themselves are an intervention. Asking "What would success look like?" doesn't just gather information -- it activates the user's mental model of success, making it more accessible during the subsequent exploration. Question selection is design.

### Open-Ended vs. Closed Questions (Research)

- Open-ended questions reduce framing effects because they let respondents frame responses themselves
- Closed questions are less cognitively demanding but can bias responses by suggesting a range of "reasonable" answers
- Evidence that open- and closed-ended responses are supported by different cognitive/memory processes
- Open-ended questions cause higher dropout rates and more cognitive effort
- Best practice: combine both -- open-ended for exploration, closed for confirmation

### Question Framing Effects

- Response options implicitly communicate the researcher's expectations and suggest a range of reasonable responses
- People anchor to whatever frame is offered in the question
- Neutral framing ("What do you think about X?") vs. loaded framing ("What frustrations do you have with X?") dramatically changes response content

### Cognitive Load Considerations

- Memory performance is inversely proportional to cognitive load
- When users are unfamiliar with a domain, direct questions about attributes are impractical -- they may not recognize key attributes
- Implication: questions should scaffold from what users know toward what they don't know, not the reverse

### LLM-Specific Research

**Thinking Assistants (2023, arXiv):** Study of LLMs that ask rather than answer.
- "Informed inquiry" (questions grounded in domain expertise + guidance) significantly outperformed both pure questioning and pure advice-giving
- Questioning alone was insufficient -- balance of probing plus expert insights produced superior reflection
- 67% of users tried to use the "thinking assistant" as an information retrieval tool despite instructions -- deeply ingrained mental model of chatbots as answer machines
- Users frustrated when system maintained open-ended inquiry instead of giving yes/no answers
- Positive outcomes correlated with self-focused dialogue (p = .01)

**Clarifying Questions for Preference Elicitation (Google Research, 2025):**
- Models trained with RLHF prefer "complete but presumptuous answers" over clarifying questions
- Multi-turn evaluation (judging questions by their downstream outcomes) is necessary to train good questioning behavior
- Key finding: clarifying questions helped even on unambiguous queries -- suggesting that AI clarification recovers correct answers beyond just handling ambiguity
- "Unnecessary clarifying questions" reduce satisfaction -- clarification should be context-dependent

**Teaching LLMs to Ask Clarifying Questions (2024, arXiv):**
- Current LLMs default to "presupposing a single interpretation" rather than asking
- Effective clarifying questions disambiguate across multiple interpretations
- Models should learn judicious clarification, not default clarification
- 4-5% F1 improvement from double-turn preference training

### Transferable principles for AI intake

- **Questions ARE the intervention.** Every question shapes the user's thinking, not just the AI's understanding. Choose questions that activate the right mental models.
- **Fight the RLHF bias toward answering.** The AI's training pushes it toward premature answering. The intake protocol must structurally resist this.
- **Judicious, not default, clarification.** Ask fewer, better questions rather than asking about everything. The user's tolerance for questions is limited.
- **Scaffold from known to unknown.** Start with what users can easily articulate, then use their language to probe what they can't.
- **Informed inquiry > pure inquiry.** Questions work better when they demonstrate domain understanding. "I notice you're weighing X vs. Y -- what would tip the balance?" beats "What are you thinking about?"

**Sources:**
- [Question-Behavior Effect: Review and Meta-Analysis](https://www.tandfonline.com/doi/full/10.1080/10463283.2016.1245940)
- [Thinking Assistants: LLM-Based Conversational Assistants - arXiv](https://arxiv.org/html/2312.06024v4)
- [Asking Clarifying Questions for Preference Elicitation - Google Research](https://research.google/pubs/asking-clarifying-questions-for-preference-elicitation-with-large-language-models/)
- [Teaching LLMs to Ask Clarifying Questions - arXiv](https://arxiv.org/abs/2410.13788)
- [Open-Ended Probes on Closed Survey Questions - SAGE](https://journals.sagepub.com/doi/10.1177/00491241231176846)
- [Framing Effects in Surveys](http://www.communicationcache.com/uploads/1/0/8/8/10887248/framing_effects_in_surveys-how_respondents_make_sense_of_the_questions_we_ask.pdf)
- [Intent Disambiguation - Microsoft Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/cux-disambiguate-intent)

---

## 8. Product/Startup Methodology

### The Mom Test (Rob Fitzpatrick)

**Three rules:**
1. Talk about their life, not your idea
2. Ask about specifics in the past, not generics about the future
3. Talk less, listen more (80/20 rule)

**Three types of bad data:**
1. **Compliments** -- "That's a great idea!" (worthless -- no information content)
2. **Fluff** -- Vague statements, hypotheticals, future promises ("I would definitely...")
3. **Ideas** -- User-suggested features without understanding underlying motivations

**Deflecting technique:** When someone gives you a compliment or fluff, redirect to specifics: "Thanks -- so the last time you encountered this problem, what exactly happened?"

**Anchoring technique:** When someone says "usually" or "always," follow up with: "When was the last time you specifically did this?" Forces concrete narrative.

**The most revealing questions:**
- "Why do you bother?" -- Strikes at motivation
- "Talk me through the last time that happened" -- Forces specific narrative
- "What else have you tried?" -- Reveals effort invested and problem severity
- "How much does this problem currently cost you?" (time/money) -- Tests whether the problem actually matters
- "Who else should I talk to?" -- Follows the network, not your assumptions

**Commitment test:** Real interest = sacrifice (time, money, reputation). "I'd definitely buy it" without a deposit is fluff.

### Steve Blank Customer Development

**Key technique: Forced prioritization.** Present a list of problems and ask: "Do you agree these are problems? Could you rank them?" This forces discussion and reveals what actually matters vs. what merely sounds reasonable.

**The exit question:** "What else should I have asked you?" -- often unlocks the most important information in the conversation.

**Anti-pattern:** Reading questions from a list is a conversation-killer. Insert questions naturally into conversation flow.

### Transferable principles for AI intake

- **Ban hypotheticals.** Don't ask "What would you do if...?" Ask "What did you do when...?" Past behavior is the only reliable predictor.
- **Ban opinion questions.** Don't ask "Do you think X is a good approach?" Ask "What approaches have you already tried?"
- **The "Why do you bother?" question is essential.** In AI terms: "Why is this worth thinking about right now? What happened that made you want to explore this?" This surfaces the trigger event and true urgency.
- **The exit question ("What should I have asked?") works perfectly as Q5.** It catches everything the structured questions missed.
- **Forced prioritization is a power move for multi-faceted problems.** "You've mentioned A, B, and C. If you could only solve one of these, which would it be?" reveals the actual priority.
- **Commitment signals translate to AI context:** If the user puts effort into their answers (long responses, specific examples), the problem is real. Short, vague answers suggest the problem isn't felt strongly enough to warrant deep exploration.

**Sources:**
- [The Mom Test Summary - TianPan.co](https://tianpan.co/notes/2025-04-29-the-mom-test)
- [The Mom Test Summary - ReadingGraphics](https://readingraphics.com/book-summary-the-mom-test/)
- [Steve Blank Customer Development](https://steveblank.com/category/customer-development/)
- [B2B Customer Discovery Questions - Lean B2B](https://leanb2bbook.com/blog/b2b-customer-discovery-interview-questions-the-master-list/)
- [Customer Development Interviews - Medium](https://medium.com/the-launch-path/doing-customer-development-interviews-for-your-startup-venture-ab25f034d1ca)

---

## 9. Bonus: Clean Language (David Grove)

### Core principle
Keep the questioner's assumptions, metaphors, and framing out of the conversation entirely. Use only the speaker's own words.

### The 8-12 basic questions (used ~80% of the time)

Format: "And [client's words] ... and when [client's words] ... [clean question]?"

Typical clean questions on a statement like "I feel strange":
- "And where do you feel strange?" (location)
- "And what kind of strange?" (attributes)
- "And that's strange like what?" (metaphor)
- "And is there anything else about that 'feels strange'?" (expand)
- "And what happens just before you feel strange?" (sequence)
- "And when you feel strange, what would you like to have happen?" (desired outcome)

### Why it matters for AI

Most questioning techniques inadvertently reframe the user's problem into the questioner's vocabulary. Clean Language is the antidote: use the user's exact words in follow-up questions. When a user says "I feel stuck," don't rephrase to "You're experiencing a blocker" -- ask "And what kind of stuck?"

**Sources:**
- [Clean Language - Wikipedia](https://en.wikipedia.org/wiki/Clean_language)
- [Clean Language - Businessballs](https://www.businessballs.com/communication-skills/clean-language-david-grove-questioning-method/)

---

## Synthesis: Principles That Transfer to AI Chat Intake

### The 12 highest-confidence principles for 3-5 intake questions

These principles have evidence from multiple independent domains:

**1. Funnel structure: broad -> narrow** (UX research, journalism, MI, coaching)
Start with the broadest possible question. Each subsequent question narrows based on what was revealed. Never start specific.

**2. Past behavior, not future hypotheticals** (Mom Test, JTBD, MI, journalism)
"Tell me about the last time..." not "What would you do if..." Past is reliable; future is fiction.

**3. Reflect before asking the next question** (MI, coaching, Clean Language)
The 2:1 reflection-to-question ratio. Between each question, mirror back what was heard. This builds trust, confirms understanding, and surfaces corrections.

**4. Use the person's own language** (Clean Language, MI, ICF coaching)
Don't rephrase into AI vocabulary. When they say "stuck," ask about "stuck." When they say "messy," ask about "messy." Reframing is premature during intake.

**5. Drill for meaning, not content** (CBT Downward Arrow, Socratic Type 2, Five Whys)
"What would that mean?" / "Why does that matter?" / "If that happened, then what?" This traverses from surface problem to core need.

**6. Resist the Righting Reflex** (MI, Mom Test, Thinking Assistants research)
The AI's strongest bias is toward answering. The intake phase must structurally prevent premature solving. Each question should deepen understanding, not offer solutions.

**7. Offer a frame and invite correction** (journalism elicitation, MI double-sided reflection)
"It sounds like you're trying to [X] -- is that right?" People correct wrong framings more readily than they generate accurate ones from scratch.

**8. Surface assumptions and constraints explicitly** (Socratic Type 2, coaching Reality phase, JTBD Anxiety force)
"What are you assuming has to be true for this to work?" / "What constraints are you working within?" Hidden assumptions are the #1 source of misaligned AI output.

**9. Ask about what's been tried** (Mom Test, GROW Reality, JTBD)
"What have you already tried?" / "What approaches have you considered?" This prevents the AI from suggesting what was already rejected and reveals the user's theory of the problem.

**10. End with the meta-question** (Steve Blank, Socratic Type 6)
"What should I have asked you?" / "What's the most important thing I haven't asked about?" This catches everything structured questions missed.

**11. Questions are interventions, not just information gathering** (QBE, MI, Solution-Focused)
The act of asking "What would success look like?" doesn't just inform the AI -- it activates the user's mental model of success. Choose questions that prime productive thinking.

**12. Judicious, not comprehensive** (LLM research, Microsoft intent design)
3-5 questions maximum. Each question must earn its place. The best clarifying question is "the smallest intervention that prevents the largest mistake." Users have limited patience for pre-work.

### Recommended 5-Question Intake Sequence

Based on the research synthesis:

**Q1: Broad opening (Funnel Stage 1 + JTBD Push)**
"What are you trying to figure out, and what prompted you to think about it now?"
*Rationale: Surfaces both the topic and the trigger event. Past-anchored ("what prompted") prevents hypothetical drift.*

**Q2: Reflection + Meaning drill (MI Reflection + Downward Arrow)**
[Reflect back Q1 answer in user's own words] + "And if you got that right, what would it change or make possible?"
*Rationale: Reflects to confirm understanding, then drills one level deeper. Surfaces the real stakes behind the stated problem.*

**Q3: Constraints and attempts (GROW Reality + Mom Test)**
"What have you already tried or considered, and what's keeping you from being further along?"
*Rationale: Reveals the user's existing theory, surfaces constraints, and prevents the AI from re-treading old ground.*

**Q4: Assumption challenge + reframe (Socratic Type 2 + MI Discrepancy)**
[Offer a tentative framing] + "What am I getting wrong about how you see this?"
*Rationale: Tests the AI's understanding and invites correction. The "deliberate wrong statement" principle -- easier to correct than to generate.*

**Q5: Meta-question (Steve Blank + Socratic Type 6)**
"What's the most important thing about this situation that I haven't asked about?"
*Rationale: Catches blind spots in both the AI's model and the user's initial framing. Consistently cited across domains as the highest-signal closing question.*

### Failure Modes to Guard Against

1. **The Question-and-Answer Trap** (MI) -- Rapid-fire questions without reflection = interrogation
2. **The Righting Reflex** (MI) -- Jumping to solutions before understanding = misaligned output
3. **The Expert Trap** (MI) -- AI demonstrates knowledge instead of curiosity = user defers to AI framing
4. **Hypothetical drift** (Mom Test) -- Asking about imagined futures instead of real experiences = unreliable answers
5. **Premature specificity** (Funnel) -- Starting with detailed questions before broad exploration = missed context
6. **Reframing the user's language** (Clean Language) -- Translating user words into AI vocabulary = lost nuance
7. **Too many questions** (LLM research) -- More than 5 questions = user frustration and abandonment
8. **Lack of domain grounding** (Thinking Assistants) -- Generic questions without expertise = perceived as unhelpful
