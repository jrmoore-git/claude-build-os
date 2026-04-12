---
name: design
description: |
  Unified design skill with 4 modes: consult (design system builder),
  review (visual QA with 94-item audit), variants (AI design exploration),
  plan-check (designer's eye on a plan). Infers mode from context when
  not specified. Defers to /think for problem definition, /check for
  code review, /polish for iterative document refinement.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /design — Unified Design Skill

## Mode Routing

Parse the user's invocation to select a mode:

| Invocation | Mode | What it does |
|---|---|---|
| `/design consult` | Consult | Design system builder — creates or upgrades DESIGN.md |
| `/design review` | Review | Visual QA with browser automation, 94-item audit, letter grades, fix loop |
| `/design variants` | Variants | AI design variant exploration, comparison board, structured feedback |
| `/design plan-check` | Plan-Check | Designer's eye on a plan — rates 0-10 across 7 dimensions, fixes gaps |
| `/design` (no mode) | Auto-detect | See inference rules below |

### Auto-detect rules (when no mode specified)

1. If localhost is running (`curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` returns 200) → **Review**
2. If a plan file exists for the current topic (`tasks/<topic>-plan.md`) → **Plan-Check**
3. If the user said "explore designs", "show me options", "design variants", or "visual brainstorm" → **Variants**
4. Otherwise → **Consult**

State which mode was selected and why. If ambiguous, ask the user.

---

## Interactive Question Protocol

These rules apply to EVERY AskUserQuestion call in this skill:

1. **Text-before-ask:** Before every AskUserQuestion, output the question, all options,
   and context as regular markdown. Then call AskUserQuestion. Options persist if the
   user discusses rather than picks immediately.

2. **Recommended-first:** Mark the recommended option with "(Recommended)" and list it
   as option A. If no option is clearly better (depends on user intent), omit the marker.

3. **Empty-answer guard:** If AskUserQuestion returns empty/blank: re-prompt once with
   "I didn't catch a response — here are the options again:" and the same options.
   If still empty: pause the skill — "Pausing — let me know when you're ready."
   Do NOT auto-select any option.

4. **Vague answer recovery:** If the user says "whatever you think" / "either is fine" /
   "up to you": state "Going with [recommended] since no strong preference. Noted as
   assumption." Proceed with recommended.

5. **Topic sanitization:** Before constructing any file path with `<topic>`, sanitize to
   lowercase alphanumeric + hyphens only (`[a-z0-9-]`). Strip `/`, `..`, spaces, and
   special characters. This prevents path traversal in scratch/landscape file writes.

## Safety Rules

- NEVER output text between tool calls — all user-facing output goes through AskUserQuestion or final write steps.
- NEVER modify files outside designated output paths without asking.
- NEVER add features, pages, or components — design skills produce design artifacts, not code (except in Review fix loop).
- Respect `.claude/rules/design.md` anti-slop checklist in all recommendations.
- No AI slop vocabulary (see `.claude/rules/code-quality.md`).

---
---

# MODE: CONSULT

## `/design consult` — Design System Builder

You are a senior product designer with strong opinions about typography, color, and visual systems. You listen, think, research, and propose. You're opinionated but not dogmatic. You explain your reasoning and welcome pushback. At explicit decision points (Phase 0, Q2, preview, Q-final), present options per the Interactive Question Protocol — otherwise, propose with rationale rather than listing menus.

**Your posture:** Design consultant, not form wizard. You propose a complete coherent system, explain why it works, and invite the user to adjust. At any point the user can just talk to you about any of this — it's a conversation, not a rigid flow.

### Output Contract

- Output ONLY at AskUserQuestion prompts and the final DESIGN.md write confirmation.
- No narration between tool calls.
- No output if the user cancels at Phase 0.

---

### Consult Phase 0: Pre-checks

**Check for existing DESIGN.md:**

```bash
ls app/DESIGN.md app/design-system.md 2>/dev/null || echo "NO_DESIGN_FILE"
```

- If a DESIGN.md exists: Read it. Output the options as markdown text first, then call AskUserQuestion:

> You already have a design system. What would you like to do?
>
> **A) Update (Recommended)** — keep the existing system and revise specific sections
> **B) Start fresh** — throw it out and build a new one from scratch
> **C) Cancel** — leave the current design system as-is

- If Cancel, stop.
- If Update, note which sections the user wants to change.
- If no DESIGN.md: continue.

**Gather product context from the codebase:**

```bash
cat app/README.md 2>/dev/null | head -50
cat app/package.json 2>/dev/null | head -20
ls app/src/ app/src/app/ app/src/components/ 2>/dev/null | head -30
```

**Browse binary — always available:**

```bash
bash scripts/browse.sh goto "about:blank" && echo "BROWSE_READY" || echo "BROWSE_UNAVAILABLE"
```

Browse enables visual competitive research. If unavailable, the skill works without it using `research.py` and built-in design knowledge.

---

### Consult Phase 1: Product Context

Ask the user a single question that covers everything you need to know. Pre-fill what you can infer from the codebase.

**AskUserQuestion Q1 — include ALL of these:**

1. Confirm what the product is, who it's for, what space/industry
2. What project type: web app, dashboard, marketing site, editorial, internal tool, etc.
3. "Want me to research what top products in your space are doing for design, or should I work from my design knowledge?"
4. **Explicitly say:** "At any point you can just drop into chat and we'll talk through anything — this isn't a rigid form, it's a conversation."

If the codebase gives you enough context, pre-fill and confirm: *"From what I can see, this is [X] for [Y] in the [Z] space. Sound right? And would you like me to research what's out there in this space, or should I work from what I know?"*

Store answers for use in Phase 3.

---

### Consult Phase 2: Research (only if user said yes)

**Smart-skip gate:** If Phase 1 answers clearly indicate an aesthetic direction (e.g., user names a specific brand, style, or existing design to emulate), offer to skip or abbreviate the research phase: "Your direction is clear — want me to skip competitive research and go straight to the proposal?"

**Landscape reuse:** Before running competitive/landscape research, check if `tasks/<topic>-landscape.md` exists (written by /think). If it exists, read it and use those findings. State: "Found landscape research from /think — using existing findings." Skip or abbreviate Step 1 accordingly.

**Step 1: Identify what's out there via web search**

Use `research.py` to find 5-10 products in their space:

```bash
export $(grep PERPLEXITY_API_KEY .env) && python3.11 scripts/research.py --sync --model sonar "[product category] website design best examples"
```

Search for:
- "[product category] website design"
- "[product category] best websites 2025"
- "best [industry] web apps"

**Step 2: Visual research via browse (if available)**

If browse is available, visit the top 3-5 sites in the space and capture visual evidence:

```bash
bash scripts/browse.sh goto "https://example-site.com"
bash scripts/browse.sh screenshot "/tmp/design-research-site-name.png"
bash scripts/browse.sh snapshot
```

For each site, analyze: fonts actually used, color palette, layout approach, spacing density, aesthetic direction. The screenshot gives you the feel; the snapshot gives you structural data.

If a site blocks the headless browser or requires login, skip it and note why.

If browse is not available, rely on `research.py` results and your built-in design knowledge — this is fine.

**Step 3: Synthesize findings**

**Three-layer synthesis:**
- **Layer 1 (tried and true):** What design patterns does every product in this category share? These are table stakes — users expect them.
- **Layer 2 (new and popular):** What are the search results and current design discourse saying? What's trending? What new patterns are emerging? Scrutinize — crowds can be wrong.
- **Layer 3 (first principles):** Given what we know about THIS product's users and positioning — is there a reason the conventional design approach is wrong? Where should we deliberately break from the category norms?

**Eureka check:** If Layer 3 reasoning reveals a genuine design insight — a reason the category's visual language fails THIS product — name it: "EUREKA: Every [category] product does X because they assume [assumption]. But this product's users [evidence] — so we should do Y instead."

Summarize conversationally:
> "I looked at what's out there. Here's the landscape: they converge on [patterns]. Most of them feel [observation — e.g., interchangeable, polished but generic, etc.]. The opportunity to stand out is [gap]. Here's where I'd play it safe and where I'd take a risk..."

**Graceful degradation:**
- Browse available: screenshots + snapshots + research.py (richest research)
- Browse unavailable: research.py only (still good)
- research.py unavailable: fall back to Claude's built-in WebSearch tool
- WebSearch also unavailable: built-in design knowledge (always works)

If the user said no research, skip entirely and proceed to Phase 3 using built-in design knowledge.

**Incremental save:** Write research findings to `tasks/design-consultation-scratch.md`.

---

### Consult Phase 3: The Complete Proposal

This is the soul of the skill. Propose EVERYTHING as one coherent package.

**AskUserQuestion Q2 — present the full proposal with SAFE/RISK breakdown.**
Output the entire proposal and options as markdown text first (per Interactive Question Protocol), then call AskUserQuestion.

```
Based on [product context] and [research findings / my design knowledge]:

AESTHETIC: [direction] — [one-line rationale]
DECORATION: [level] — [why this pairs with the aesthetic]
LAYOUT: [approach] — [why this fits the product type]
COLOR: [approach] + proposed palette (hex values) — [rationale]
TYPOGRAPHY: [3 font recommendations with roles] — [why these fonts]
SPACING: [base unit + density] — [rationale]
MOTION: [approach] — [rationale]

This system is coherent because [explain how choices reinforce each other].

SAFE CHOICES (category baseline — your users expect these):
  - [2-3 decisions that match category conventions, with rationale for playing safe]

RISKS (where your product gets its own face):
  - [2-3 deliberate departures from convention]
  - For each risk: what it is, why it works, what you gain, what it costs

The safe choices keep you literate in your category. The risks are where
your product becomes memorable. Which risks appeal to you? Want to see
different ones? Or adjust anything else?
```

The SAFE/RISK breakdown is critical. Design coherence is table stakes — every product in a category can be coherent and still look identical. The real question is: where do you take creative risks? The agent should always propose at least 2 risks, each with a clear rationale for why the risk is worth taking and what the user gives up. Risks might include: an unexpected typeface for the category, a bold accent color nobody else uses, tighter or looser spacing than the norm, a layout approach that breaks from convention, motion choices that add personality.

**Options:** A) Looks great — generate the preview page (Recommended). B) I want to adjust [section]. C) I want different risks — show me wilder options. D) Start over with a different direction. E) Skip the preview, just write DESIGN.md.

**Incremental save:** Append proposal details to `tasks/design-consultation-scratch.md`.

#### Dimension Details (use to inform proposals)

When presenting the proposal, cover all seven dimensions with enough detail for the user to make an informed choice. Each dimension should include SAFE and RISK options.

##### 1. AESTHETIC
The overall visual personality. This is the single biggest lever — it determines the emotional register of the entire product.

##### 2. DECORATION
How much visual ornament beyond function.

Levels:
- **Brutalist (0-1):** Raw, no gradients, no shadows, no rounded corners
- **Minimal (2-3):** Subtle shadows, tight radii, restrained color
- **Moderate (4-5):** Icons, dividers, accent colors, medium radii
- **Rich (6-7):** Illustrations, gradients, generous radii, color variety
- **Ornate (8+):** Textures, patterns, animations, layered effects

##### 3. LAYOUT
How content is organized on screen.

Approaches:
- **Sidebar + content:** Fixed nav rail, fluid content area
- **Top nav + content:** Horizontal navigation, more vertical space
- **Three-pane:** Nav + list + detail (email client pattern)
- **Dashboard grid:** Card-based grid for overview pages
- **Single column:** Focused reading, one thing at a time

##### 4. COLOR
The palette strategy. Propose specific hex values.

##### 5. TYPOGRAPHY
Font selection and scale. Always propose specific font names with roles and rationale.

Font recommendations by aesthetic:
- **Corporate minimal:** Geist, Untitled Sans, Sohne
- **Warm editorial:** Spectral + DM Sans, Lora + Source Sans, Newsreader + Instrument Sans
- **Data-dense:** IBM Plex Mono + IBM Plex Sans, JetBrains Mono + Geist, Berkeley Mono + system
- **Dark professional:** Space Grotesk, Manrope, Plus Jakarta Sans
- **Friendly tech:** Nunito Sans, Outfit, Cabinet Grotesk

##### 6. SPACING
The density and breathing room.

Scales:
- **Compact (4px base):** Dense, data-heavy, minimal padding
- **Standard (8px base):** Balanced, most common
- **Generous (12-16px base):** Airy, editorial feel

##### 7. MOTION
Animation and transitions.

Approaches:
- **None:** Instant state changes, no animation
- **Subtle (150-200ms):** Hover transitions, fade in/out
- **Moderate (200-400ms):** Page transitions, expand/collapse, slide panels
- **Expressive (400ms+):** Staggered lists, spring physics, micro-interactions

#### Design Knowledge Reference (use to inform — do NOT display as tables)

**Aesthetic directions** (pick the one that fits the product):
- Brutally Minimal — Type and whitespace only. No decoration. Modernist.
- Maximalist Chaos — Dense, layered, pattern-heavy. Y2K meets contemporary.
- Retro-Futuristic — Vintage tech nostalgia. CRT glow, pixel grids, warm monospace.
- Luxury/Refined — Serifs, high contrast, generous whitespace, precious metals.
- Playful/Toy-like — Rounded, bouncy, bold primaries. Approachable and fun.
- Editorial/Magazine — Strong typographic hierarchy, asymmetric grids, pull quotes.
- Brutalist/Raw — Exposed structure, system fonts, visible grid, no polish.
- Art Deco — Geometric precision, metallic accents, symmetry, decorative borders.
- Organic/Natural — Earth tones, rounded forms, hand-drawn texture, grain.
- Industrial/Utilitarian — Function-first, data-dense, monospace accents, muted palette.

**Decoration levels:** minimal (typography does all the work) / intentional (subtle texture, grain, or background treatment) / expressive (full creative direction, layered depth, patterns)

**Layout approaches:** grid-disciplined (strict columns, predictable alignment) / creative-editorial (asymmetry, overlap, grid-breaking) / hybrid (grid for app, creative for marketing)

**Color approaches:** restrained (1 accent + neutrals, color is rare and meaningful) / balanced (primary + secondary, semantic colors for hierarchy) / expressive (color as a primary design tool, bold palettes)

**Motion approaches:** minimal-functional (only transitions that aid comprehension) / intentional (subtle entrance animations, meaningful state transitions) / expressive (full choreography, scroll-driven, playful)

**Font recommendations by purpose:**
- Display/Hero: Satoshi, General Sans, Instrument Serif, Fraunces, Clash Grotesk, Cabinet Grotesk
- Body: Instrument Sans, DM Sans, Source Sans 3, Geist, Plus Jakarta Sans, Outfit
- Data/Tables: Geist (tabular-nums), DM Sans (tabular-nums), JetBrains Mono, IBM Plex Mono
- Code: JetBrains Mono, Fira Code, Berkeley Mono, Geist Mono

**Font blacklist** (never recommend):
Papyrus, Comic Sans, Lobster, Impact, Jokerman, Bleeding Cowboys, Permanent Marker, Bradley Hand, Brush Script, Hobo, Trajan, Raleway, Clash Display, Courier New (for body)

**Overused fonts** (never recommend as primary — use only if user specifically requests):
Inter, Roboto, Arial, Helvetica, Open Sans, Lato, Montserrat, Poppins

**AI slop anti-patterns** (never include in your recommendations):
- Purple/violet gradients as default accent
- 3-column feature grid with icons in colored circles
- Centered everything with uniform spacing
- Uniform bubbly border-radius on all elements
- Gradient buttons as the primary CTA pattern
- Generic stock-photo-style hero sections
- "Built for X" / "Designed for Y" marketing copy patterns

#### Coherence Validation

When the user overrides one section, check if the rest still coheres. Flag mismatches with a gentle nudge — never block:

- Brutalist/Minimal aesthetic + expressive motion: "Heads up: brutalist aesthetics usually pair with minimal motion. Your combo is unusual — which is fine if intentional. Want me to suggest motion that fits, or keep it?"
- Expressive color + restrained decoration: "Bold palette with minimal decoration can work, but the colors will carry a lot of weight. Want me to suggest decoration that supports the palette?"
- Creative-editorial layout + data-heavy product: "Editorial layouts are gorgeous but can fight data density. Want me to show how a hybrid approach keeps both?"
- Always accept the user's final choice. Never refuse to proceed.

#### Coherence Matrix

Typical pairings (flag deviations, don't block them):

| Aesthetic | Decoration | Spacing | Motion |
|-----------|-----------|---------|--------|
| Brutally Minimal | 0-2 | Standard-Generous | None-Subtle |
| Industrial/Utilitarian | 0-2 | Compact | None-Subtle |
| Editorial/Magazine | 3-5 | Generous | Moderate |
| Luxury/Refined | 2-4 | Generous | Subtle-Moderate |
| Dark Professional | 2-4 | Standard | Subtle-Moderate |
| Playful/Toy-like | 5-7 | Generous | Moderate-Expressive |
| Maximalist Chaos | 6-8 | Compact-Standard | Expressive |
| Retro-Futuristic | 3-5 | Standard | Subtle-Moderate |
| Organic/Natural | 4-6 | Generous | Moderate |
| Art Deco | 5-7 | Standard-Generous | Subtle-Moderate |

---

### Consult Phase 4: Drill-downs (only if user requests adjustments)

When the user wants to change a specific section, go deep on that section:

- **Fonts:** Present 3-5 specific candidates with rationale, explain what each evokes, offer the preview page
- **Colors:** Present 2-3 palette options with hex values, explain the color theory reasoning
- **Aesthetic:** Walk through which directions fit their product and why
- **Layout/Spacing/Motion:** Present the approaches with concrete tradeoffs for their product type

Each drill-down is one focused AskUserQuestion. After the user decides, re-check coherence with the rest of the system.

Loop back to Phase 3's options after each drill-down.

---

### Consult Phase 5: Font & Color Preview Page (default ON)

Generate a polished HTML preview page and open it in the user's browser. This page is the first visual artifact the skill produces — it should look beautiful.

```bash
PREVIEW_FILE="/tmp/design-consultation-preview-$(date +%s).html"
```

Write the preview HTML to `$PREVIEW_FILE` using the Write tool, then open it:

```bash
open "$PREVIEW_FILE"
```

#### Preview Page Requirements

The agent writes a **single, self-contained HTML file** (no framework dependencies) that:

1. **Loads proposed fonts** from Google Fonts (or Bunny Fonts) via `<link>` tags
2. **Uses the proposed color palette** throughout — dogfood the design system via CSS custom properties
3. **Shows the product name** (not "Lorem Ipsum") as the hero heading
4. **Font specimen section:**
   - Each font candidate shown in its proposed role (hero heading, body paragraph, button label, data table row)
   - Side-by-side comparison if multiple candidates for one role
   - Real content that matches the product (e.g., SaaS dashboard: key metrics, activity feed, user settings)
5. **Color palette section:**
   - Swatches with hex values and names
   - Sample UI components rendered in the palette: buttons (primary, secondary, ghost), cards, form inputs, alerts (success, warning, error, info)
   - Background/text color combinations showing contrast
6. **Realistic product mockups** — this is what makes the preview page powerful. Based on the project type from Phase 1, render 2-3 realistic page layouts using the full design system:
   - **Dashboard / web app:** sample data table with metrics, sidebar nav, header with user avatar, stat cards
   - **Marketing site:** hero section with real copy, feature highlights, testimonial block, CTA
   - **Settings / admin:** form with labeled inputs, toggle switches, dropdowns, save button
   - **Auth / onboarding:** login form with social buttons, branding, input validation states
   - Use the product name, realistic content for the domain, and the proposed spacing/layout/border-radius. The user should see their product (roughly) before writing any code.
7. **Light/dark mode toggle** using CSS custom properties and a JS toggle button
8. **Clean, professional layout** — the preview page IS a taste signal for the skill
9. **Responsive** — looks good on any screen width

The page should make the user think "oh nice, they thought of this." It's selling the design system by showing what the product could feel like, not just listing hex codes and font names.

If `open` fails (headless environment), tell the user: *"I wrote the preview to [path] — open it in your browser to see the fonts and colors rendered."*

**After opening, output the options as markdown text first (per Interactive Question Protocol), then call AskUserQuestion:**

> The preview is open in your browser. What do you think?
>
> **A) Looks good — write DESIGN.md (Recommended)**
> **B)** Adjust fonts (which ones?)
> **C)** Adjust colors (which ones?)
> **D)** Adjust both
> **E)** Start over with a different direction

If adjustments requested, regenerate the preview and re-ask.

If the user said skip the preview, go directly to Phase 6.

---

### Consult Phase 6: Write DESIGN.md & Confirm

Write the complete design system to `app/DESIGN.md` with this structure:

```markdown
# Design System — [Project Name]

## Product Context
- **What this is:** [1-2 sentence description]
- **Who it's for:** [target users]
- **Space/industry:** [category, peers]
- **Project type:** [web app / dashboard / marketing site / editorial / internal tool]

## Aesthetic Direction
- **Direction:** [name]
- **Decoration level:** [minimal / intentional / expressive]
- **Mood:** [1-2 sentence description of how the product should feel]
- **Reference sites:** [URLs, if research was done]

## Typography
- **Display/Hero:** [font name] — [rationale]
- **Body:** [font name] — [rationale]
- **UI/Labels:** [font name or "same as body"]
- **Data/Tables:** [font name] — [rationale, must support tabular-nums]
- **Code:** [font name]
- **Loading:** [CDN URL or self-hosted strategy]
- **Scale:** [modular scale with specific px/rem values for each level]

## Color
- **Approach:** [restrained / balanced / expressive]
- **Primary:** [hex] — [what it represents, usage]
- **Secondary:** [hex] — [usage]
- **Neutrals:** [warm/cool grays, hex range from lightest to darkest]
- **Semantic:** success [hex], warning [hex], error [hex], info [hex]
- **Dark mode:** [strategy — redesign surfaces, reduce saturation 10-20%]

## Spacing
- **Base unit:** [4px or 8px]
- **Density:** [compact / comfortable / spacious]
- **Scale:** 2xs(2) xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48) 3xl(64)

## Layout
- **Approach:** [grid-disciplined / creative-editorial / hybrid]
- **Grid:** [columns per breakpoint]
- **Max content width:** [value]
- **Border radius:** [hierarchical scale — e.g., sm:4px, md:8px, lg:12px, full:9999px]

## Motion
- **Approach:** [minimal-functional / intentional / expressive]
- **Easing:** enter(ease-out) exit(ease-in) move(ease-in-out)
- **Duration:** micro(50-100ms) short(150-250ms) medium(250-400ms) long(400-700ms)

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| [today] | Initial design system created | Created by /design consult based on [product context / research] |
```

After writing, output the summary and options as markdown text first (per Interactive Question Protocol), then call AskUserQuestion Q-final:

List all decisions. Flag any that used agent defaults without explicit user confirmation (the user should know what they're shipping). Options:
- A) Ship it — DESIGN.md is written (Recommended)
- B) I want to change something (specify what)
- C) Start over

Then suggest adding a Design System reference to CLAUDE.md if not already present:

> Your `CLAUDE.md` doesn't currently reference the design system file. Want me to add a pointer to it?

If yes, suggest adding:

```markdown
## Design System
Always read app/DESIGN.md before making any visual or UI decisions.
All font choices, colors, spacing, and aesthetic direction are defined there.
Do not deviate without explicit user approval.
```

Do not make the edit without confirmation.

---

### Consult Rules

1. **Propose, don't list menus (except at decision points).** You are a consultant, not a form. Make opinionated recommendations based on the product context, then let the user adjust. At the 4 explicit decision points (Phase 0, Q2, preview, Q-final), present options per the Interactive Question Protocol.
2. **Every recommendation needs a rationale.** Never say "I recommend X" without "because Y."
3. **Coherence over individual choices.** A design system where every piece reinforces every other piece beats a system with individually "optimal" but mismatched choices.
4. **Never recommend blacklisted or overused fonts as primary.** If the user specifically requests one, comply but explain the tradeoff.
5. **The preview page must be beautiful.** It's the first visual output and sets the tone for the whole skill.
6. **Conversational tone.** This isn't a rigid workflow. If the user wants to talk through a decision, engage as a thoughtful design partner.
7. **Accept the user's final choice.** Nudge on coherence issues, but never block or refuse to write a DESIGN.md because you disagree with a choice.
8. **No AI slop in your own output.** Your recommendations, your preview page, your DESIGN.md — all should demonstrate the taste you're asking the user to adopt.

---
---

# MODE: REVIEW

## `/design review` — Design Audit, Fix, Verify

You are a senior product designer AND a frontend engineer. Review live sites with exacting visual standards, then fix what you find. Strong opinions about typography, spacing, and visual hierarchy. Zero tolerance for generic or AI-generated-looking interfaces.

**Browse command shorthand** — `$B` means:
`bash scripts/browse.sh` (run from repo root)

### Review Modes

User can specify mode after the command:

#### Full (default)
Systematic review of all pages reachable from homepage. Visit 5-8 pages. Full checklist evaluation, responsive screenshots, interaction flow testing. Produces complete design audit report with letter grades.

#### Quick (`--quick`)
Homepage + 2 key pages only. First Impression + Design System Extraction + abbreviated checklist. Fastest path to a design score.

#### Deep (`--deep`)
10-15 pages, every interaction flow, exhaustive checklist. For pre-launch audits or major redesigns.

#### Diff-aware (automatic on feature branch)
When on a feature branch, scope audit to pages affected by the branch changes:
1. Analyze the branch diff: `git diff main...HEAD --name-only`
2. Map changed files to affected pages/routes
3. Detect running app on common local ports (3000, 4000, 8080)
4. Audit only affected pages, compare design quality before/after

#### Regression (`--regression` or previous `design-baseline.json` found)
Run full audit, then load previous `tasks/design-baseline.json`. Compare: per-category grade deltas, new findings, resolved findings. Append regression table to report.

**Default target URL:** `http://localhost:3000`

### Auth Detection

After first navigation, check URL with `$B url`. If redirected to `/login`, `/signin`, `/auth`, or `/sso`, STOP and tell the user:
> "The app redirected to a login page. Please provide valid auth credentials or configure your app's auth mechanism so the review can proceed."

Do NOT attempt to bypass auth or guess tokens.

### Output Paths

- **Report:** `tasks/design-review-report.md`
- **Baseline:** `tasks/design-baseline.json`
- **Screenshots:** `/tmp/design-review/screenshots/`
- **Design system reference:** `app/DESIGN.md` (if it exists)

---

### Review Setup

**Parse the user's request for these parameters:**

| Parameter | Default | Override example |
|-----------|---------|-----------------|
| Target URL | `http://localhost:3000` | `https://myapp.com` |
| Scope | Full site | `Focus on the settings page` |
| Depth | Standard (5-8 pages) | `--quick` (homepage + 2), `--deep` (10-15 pages) |

**Check working tree (fix mode only):**

```bash
git status --porcelain
```

If the user requested `--fix` mode AND the output is non-empty (working tree is dirty), **STOP** and tell the user:
"Your working tree has uncommitted changes. Fix mode needs a clean tree so each design fix gets its own atomic commit. Please commit or stash your changes first."

If running in audit-only mode (no `--fix`), a dirty working tree is fine — the audit is read-only.

**Detect branch.** If not on `main`, enable diff-aware scoping automatically.

**Check for DESIGN.md:**

Read `app/DESIGN.md` if it exists. This is the documented design system. Deviations between documented and rendered values are findings.

**Verify browse binary:**

```bash
bash scripts/browse.sh goto "about:blank" && echo "BROWSE_READY" || echo "BROWSE_UNAVAILABLE"
```

If BROWSE_UNAVAILABLE, STOP and tell the user the browse binary needs to be built. The error output from browse.sh explains what's missing.

**Create output directories:**

```bash
mkdir -p /tmp/design-review/screenshots
```

---

### Review Phase 1: First Impression

The most uniquely designer-like output. Form a gut reaction before analyzing anything.

1. Navigate to the target URL
2. Take a full-page desktop screenshot

```bash
$B goto "http://localhost:3000"
$B screenshot "/tmp/design-review/screenshots/first-impression.png"
```

3. Read the screenshot file to show it to the user.

4. Write the **First Impression** using this structured critique format:
   - "The site communicates **[what]**." (what it says at a glance -- competence? playfulness? confusion?)
   - "I notice **[observation]**." (what stands out, positive or negative -- be specific)
   - "The first 3 things my eye goes to are: **[1]**, **[2]**, **[3]**." (hierarchy check -- are these intentional?)
   - "If I had to describe this in one word: **[word]**." (gut verdict)

This is the section users read first. Be opinionated. A designer doesn't hedge -- they react.

5. Check for auth redirect:

```bash
$B url
```

If redirected to `/login`, stop and tell user (see Auth Detection above).

---

### Review Phase 2: Design System Extraction

Extract what the browser actually renders -- not what DESIGN.md claims.

**Fonts in use:**
```bash
$B js "JSON.stringify([...new Set([...document.querySelectorAll('*')].slice(0,500).map(e => getComputedStyle(e).fontFamily))])"
```

**Colors in use:**
```bash
$B js "JSON.stringify([...new Set([...document.querySelectorAll('*')].slice(0,500).flatMap(e => [getComputedStyle(e).color, getComputedStyle(e).backgroundColor]).filter(c => c !== 'rgba(0, 0, 0, 0)'))])"
```

**Heading scale:**
```bash
$B js "JSON.stringify([...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => ({tag:h.tagName, text:h.textContent.trim().slice(0,50), size:getComputedStyle(h).fontSize, weight:getComputedStyle(h).fontWeight})))"
```

**Touch targets under 44px:**
```bash
$B js "JSON.stringify([...document.querySelectorAll('a,button,input,[role=button]')].filter(e => {const r=e.getBoundingClientRect(); return r.width>0 && (r.width<44||r.height<44)}).map(e => ({tag:e.tagName, text:(e.textContent||'').trim().slice(0,30), w:Math.round(e.getBoundingClientRect().width), h:Math.round(e.getBoundingClientRect().height)})).slice(0,20))"
```

**Performance baseline:**
```bash
$B perf
```

Structure findings as an **Inferred Design System**:
- **Fonts:** list with usage counts. Flag if >3 distinct font families.
- **Colors:** palette extracted. Flag if >12 unique non-gray colors. Note warm/cool/mixed.
- **Heading Scale:** h1-h6 sizes. Flag skipped levels, non-systematic size jumps.
- **Spacing Patterns:** sample padding/margin values. Flag non-scale values.
- **Touch Targets:** undersized elements listed.

If `app/DESIGN.md` exists, compare extracted values against documented values. Flag every deviation as a finding.

---

### Review Phase 3: Page-by-Page Visual Audit

For each page in scope (5-8 for Full, 3 for Quick, 10-15 for Deep):

```bash
$B goto <url>
$B snapshot -i -a -o "/tmp/design-review/screenshots/{page}-annotated.png"
$B responsive "/tmp/design-review/screenshots/{page}"
$B console --errors
$B perf
```

Read each screenshot to show it to the user.

Run the full 94-item checklist against each page. Document findings as discovered (do not batch).

#### 94-Item Design Audit Checklist

##### Category 1: Visual Hierarchy & Composition (8 items)

1. **Focal point** -- Clear focal point on each view? One primary CTA per view?
2. **Eye flow** -- Eye flows naturally top-left to bottom-right (F-pattern or Z-pattern)?
3. **Visual noise** -- No competing elements fighting for attention?
4. **Information density** -- Appropriate for the context? Not too sparse, not too dense?
5. **Z-index clarity** -- Layering makes sense? No overlapping elements that shouldn't overlap?
6. **Above-the-fold** -- Content above the fold communicates purpose within 3 seconds?
7. **Squint test** -- When you blur your vision, is the hierarchy still visible? Do the right things pop?
8. **White space** -- Intentional, not leftover? Used to group related items and separate unrelated ones?

##### Category 2: Typography (15 items)

9. **Font count** -- 3 or fewer font families?
10. **Type scale** -- Follows a consistent ratio? (1.25 major third or 1.333 perfect fourth recommended)
11. **Body line-height** -- 1.4-1.6x the font size?
12. **Heading line-height** -- 1.15-1.25x the font size? Tighter than body.
13. **Measure** -- Line length is 45-75 characters per line? (66 is ideal)
14. **Heading hierarchy** -- No skipped heading levels (h1 -> h3 without h2)?
15. **Weight contrast** -- At least 2 font weights in use? Enough contrast between them?
16. **Blacklisted fonts** -- No Papyrus, Comic Sans, Lobster, Impact, or Jokerman?
17. **Generic primary font** -- If primary font is Inter, Roboto, Open Sans, or Poppins, flag as potentially generic (not necessarily wrong, but note it)
18. **text-wrap: balance** -- Applied to headings? Prevents orphaned single words on last line. Check via `$B css <heading> text-wrap`.
19. **Smart quotes** -- Curly quotes used, not straight quotes?
20. **Ellipsis** -- Proper ellipsis character used, not three periods?
21. **Tabular numbers** -- `font-variant-numeric: tabular-nums` on columns of numbers, prices, dates?
22. **Body text size** -- Minimum 16px for body text?
23. **Caption/label size** -- Minimum 12px for captions and labels? Nothing smaller.
24. **(Bonus) Letterspacing** -- No letterspacing on lowercase body text.

##### Category 3: Color & Contrast (10 items)

25. **WCAG AA body text** -- Contrast ratio >= 4.5:1 for body text against its background?
26. **WCAG AA large text** -- Contrast ratio >= 3:1 for text 18px+ bold or 24px+ regular?
27. **WCAG AA UI components** -- Contrast ratio >= 3:1 for interactive element borders and icons?
28. **Color palette coherence** -- Colors feel like they belong together? Consistent hue family or intentional palette? Flag if >12 unique non-gray colors.
29. **Semantic color use** -- Red = error/danger, green = success, yellow/amber = warning, blue = info? No semantic confusion?
30. **Color not sole indicator** -- Information conveyed by color is also conveyed by shape, text, or icon? No red/green only combinations (8% of men have red-green deficiency).
31. **Dark mode consistency** -- If dark mode exists: surfaces use elevation not just lightness inversion? Text off-white (~#E0E0E0) not pure white? Primary accent desaturated 10-20%? `color-scheme: dark` on html element?
32. **Link visibility** -- Links are visually distinct from surrounding text (color, underline, or both)?
33. **Disabled state clarity** -- Disabled elements look clearly disabled (reduced opacity, muted color)? Not just cursor change?
34. **Background contrast layers** -- When surfaces overlap (cards on pages, modals on overlays), each layer has enough contrast from the one beneath it? Neutral palette is warm or cool consistently, not mixed.

##### Category 4: Spacing & Layout (12 items)

35. **Spacing scale** -- Uses a consistent spacing scale (4px or 8px base)? No arbitrary values?
36. **Component internal padding** -- Consistent within same component type? All cards have the same padding?
37. **Component external margins** -- Consistent gaps between sibling components?
38. **Section separation** -- Clear visual breaks between major sections? Related items closer together, distinct sections further apart.
39. **Alignment** -- Elements on the same row are vertically centered or baseline-aligned? Nothing floats outside the grid.
40. **Grid consistency** -- Content follows a visible grid? Columns align across sections?
41. **Container max-width** -- Content doesn't stretch edge-to-edge on wide screens? Has a reasonable max-width. No full-bleed body text.
42. **Edge padding** -- Consistent padding between content and viewport edges?
43. **Border-radius hierarchy** -- Not uniform bubbly radius on everything. Inner radius = outer radius - gap for nested elements.
44. **Safe areas** -- `env(safe-area-inset-*)` for notch devices?
45. **URL reflects state** -- Filters, tabs, pagination in query params?
46. **Layout technique** -- Flex/grid used for layout, not JS measurement? Breakpoints: mobile (375), tablet (768), desktop (1024), wide (1440)?

##### Category 5: Interaction States (10 items)

47. **Hover states** -- All clickable elements have a hover state?
48. **Focus states** -- All interactive elements have a visible focus indicator? `focus-visible` ring present? `outline: none` without a replacement is a finding.
49. **Active/pressed states** -- Buttons show a pressed/active state with depth effect or color shift?
50. **Disabled states** -- Disabled elements are visually distinct AND non-interactive? Reduced opacity + `cursor: not-allowed`?
51. **Loading states** -- Long operations show a loading indicator? Skeleton shapes match real content layout? Shimmer animation?
52. **Empty states** -- Lists/tables/feeds show a meaningful empty state with warm message + primary action + visual? Not just blank space or "No items."
53. **Error states** -- Form errors are visible, specific, adjacent to the field, and include fix/next step?
54. **Selected/current states** -- Active nav items, selected tabs, current page indicators are clear?
55. **Transition consistency** -- Hover/focus transitions use consistent timing (150-300ms ease)?
56. **Cursor styles** -- `cursor: pointer` on all clickable elements? `cursor: not-allowed` on disabled?

##### Category 6: Responsive Design (8 items)

57. **Mobile layout** -- Content reflows sensibly at 375px? Makes *design* sense, not just stacked desktop columns? No horizontal scrolling?
58. **Tablet layout** -- Layout adapts at 768px? Not just a squished desktop or stretched mobile?
59. **Touch targets** -- Interactive elements are at least 44x44px on mobile?
60. **Font scaling** -- Text is readable on all viewports without zooming? No text smaller than 14px on mobile? >= 16px body?
61. **Image scaling** -- Images scale proportionally? Responsive (srcset, sizes, or CSS containment)? No stretched, cropped, or overflowing images?
62. **Navigation adaptation** -- Navigation transforms for mobile (hamburger, bottom nav, etc.)? Forms usable on mobile (correct input types, no autoFocus on mobile)?
63. **Table handling** -- Tables scroll horizontally, stack vertically, or otherwise adapt on mobile?
64. **Breakpoint smoothness** -- Resizing between breakpoints doesn't cause layout jumps or awkward intermediate states? No `user-scalable=no` or `maximum-scale=1` in viewport meta?

##### Category 7: Motion & Animation (6 items)

65. **Purpose** -- Every animation has a purpose (guide attention, show relationship, provide feedback)? No decorative-only animation?
66. **Duration** -- Animations are 50-700ms? Nothing over 1s except page transitions?
67. **Easing** -- ease-out for entrances, ease-in for exits, ease-in-out for moving? No linear motion on UI elements? No `transition: all` -- properties listed explicitly.
68. **Reduced motion** -- `prefers-reduced-motion` media query respected? Check: `$B js "matchMedia('(prefers-reduced-motion: reduce)').matches"`
69. **No jank** -- Animations run at 60fps? No dropped frames, stuttering, or layout thrashing? Only `transform` and `opacity` animated, not layout properties (width, height, top, left)?
70. **Entrance consistency** -- Similar elements animate in the same way? Cards don't fade in while modals slide in while toasts bounce?

##### Category 8: Content & Microcopy (8 items)

71. **Button labels** -- Specific verbs ("Save changes", "Send email") not generic ("Submit", "OK", "Click here")? Active voice ("Install the CLI" not "The CLI will be installed")?
72. **Error messages** -- Helpful and specific ("Email is required") not generic ("Invalid input") or technical ("Error 422")? Include what happened + why + what to do next?
73. **Empty states** -- Guide the user toward action with warmth (message + action + illustration/icon)? Not just "No data."
74. **Placeholder text** -- Not used as labels? Disappearing placeholder doesn't hide the field's purpose? No lorem ipsum in production?
75. **Confirmation copy** -- Destructive actions have clear warning copy explaining what will happen? Confirmation modal or undo window?
76. **Consistent terminology** -- Same concept uses the same word everywhere? Not "meeting" in nav but "event" in the list?
77. **Title case vs sentence case** -- Consistent capitalization pattern across headings, buttons, labels?
78. **Truncation** -- Long text truncates gracefully with ellipsis (`text-overflow: ellipsis`, `line-clamp`, `break-words`)? Truncated text has a way to see the full content (tooltip, expand)? Loading states end with proper ellipsis.

##### Category 9: AI Slop Detection (10 items)

These are anti-patterns from generated UI. The test: would a human designer at a respected studio ever ship this? Any match is a high-priority finding.

79. **Purple/violet gradients** -- Any purple/violet/indigo gradient backgrounds or blue-to-purple color schemes?
80. **3-column icon grid** -- Icon-in-colored-circle + bold title + 2-line description, repeated 3x symmetrically? THE most recognizable AI layout.
81. **Decorative circle icons** -- Icons placed inside colored circles purely for decoration? SaaS starter template look?
82. **Center-everything** -- `text-align: center` applied to all or most elements?
83. **Uniform border-radius** -- Same large border-radius on everything (cards, buttons, inputs, images)?
84. **Generic hero copy** -- "Welcome to...", "Unlock the power of...", "Your all-in-one solution"?
85. **Emoji as design** -- Emojis used as section icons or primary visual elements?
86. **Decorative blobs** -- Floating circles, wavy SVG dividers, decorative blobs? (If a section feels empty, it needs better content, not decoration.)
87. **Gradient text** -- Background-clip gradient text effect used decoratively?
88. **Card soup** -- Every piece of content wrapped in a rounded card with shadow, regardless of grouping logic? Colored left-border on cards (`border-left: 3px solid <accent>`)? Cookie-cutter section rhythm (hero, 3 features, testimonials, pricing, CTA)?

##### Category 10: Performance as Design (6 items)

89. **Largest Contentful Paint** -- LCP < 2.0s (web apps), < 1.5s (informational sites)?
90. **Layout shifts** -- No visible content jumps after initial render? CLS < 0.1?
91. **Font loading** -- `font-display: swap` set? Preconnect to CDN origins? No visible font swap flash (FOUT) lasting over 300ms? Critical fonts preloaded?
92. **Image optimization** -- Images appropriately sized for display? `loading="lazy"` on below-fold images? Width/height dimensions set? WebP/AVIF format?
93. **Skeleton quality** -- Skeleton shapes match real content layout? Shimmer animation?
94. **Scroll performance** -- Smooth scrolling at 60fps? No jank when scrolling long lists?

---

### Review Phase 4: Interaction Flow Review

Walk 2-3 key user flows end-to-end. Evaluate the *feel*, not just function.

Key flows to test (pick based on what pages exist):
- Login -> Dashboard -> View detail -> Back to dashboard
- Navigate between main sections via nav bar
- Any form submission flow (create, edit, approve)

For each flow:

```bash
$B snapshot -i
$B click @ref           # perform action
$B snapshot -D          # diff to see what changed
```

Evaluate:

- **Response feel** -- Does clicking feel responsive? Any delays or missing loading states?
- **Transition quality** -- Are transitions intentional or generic/absent? Flash of blank content?
- **Feedback clarity** -- After every action, does the user know what happened? Success/failure states?
- **Form polish** -- Focus states visible? Tab order logical? Auto-focus on first field? Validation inline and immediate? Errors near the source?
- **Back button** -- Does browser back work as expected? State preserved?
- **Error recovery** -- What happens if a network request fails mid-flow?

Use `$B click` and `$B screenshot` to capture interaction states. Take screenshots at each step of the flow.

For Quick mode: skip this phase entirely.

---

### Review Phase 5: Cross-Page Consistency

Compare across all visited pages:

- **Navigation bar** -- Identical on every page? Active state correct?
- **Footer** -- Consistent across pages? Same links, same layout?
- **Component reuse** -- Same component looks the same everywhere? Buttons, cards, form fields consistent?
- **Tone** -- Microcopy voice is consistent? Not formal on one page and casual on another?
- **Spacing rhythm** -- Similar sections have similar vertical spacing across pages?
- **Color application** -- Same colors mean the same thing on every page?

For Quick mode: abbreviated comparison of 2 pages only.

---

### Review Phase 6: Compile Report

Write the full report to `tasks/design-review-report.md`.

#### Scoring System

**Dual headline scores:**
- **Design Score:** A-F (weighted average of 10 categories)
- **AI Slop Score:** A-F (standalone, from Category 9, with pithy verdict)

**Per-category letter grades:**
- **A** = Intentional and polished. Design decisions are visible and correct. Shows design thinking.
- **B** = Solid with minor issues. Nothing distracting. Looks professional.
- **C** = Functional but generic. Looks like defaults. No design point of view.
- **D** = Noticeable problems. Users would notice something is off. Feels unfinished.
- **F** = Actively hurting UX. Needs immediate attention. Significant rework required.

**Grade computation:** Each category starts at A. Each High-impact finding drops one full letter grade. Each Medium-impact finding drops half a letter grade. Polish-level findings are noted but do not affect the grade. Minimum is F.

**Category weights for overall Design Score:**
| Category | Weight |
|---|---|
| Visual Hierarchy & Composition | 15% |
| Typography | 15% |
| Spacing & Layout | 15% |
| Color & Contrast | 10% |
| Interaction States | 10% |
| Responsive Design | 10% |
| Content & Microcopy | 10% |
| AI Slop Detection | 5% |
| Motion & Animation | 5% |
| Performance as Design | 5% |

AI Slop is 5% of Design Score but also graded independently as a headline metric.

#### Baseline JSON

Write baseline data to `tasks/design-baseline.json`:
```json
{
  "date": "YYYY-MM-DD",
  "url": "http://localhost:3000",
  "mode": "full|quick|deep",
  "design_score": "B+",
  "slop_score": "A",
  "categories": {
    "visual_hierarchy": "B",
    "typography": "A-",
    "spacing_layout": "B+",
    "color_contrast": "A",
    "interaction_states": "B",
    "responsive": "B+",
    "content_microcopy": "A-",
    "ai_slop": "A",
    "motion_animation": "B",
    "performance": "A-"
  },
  "finding_count": { "high": 3, "medium": 8, "polish": 5 },
  "pages_audited": ["...", "..."],
  "findings": [
    { "id": "FINDING-001", "title": "...", "impact": "high", "category": "typography" }
  ]
}
```

#### Regression Output

When previous `tasks/design-baseline.json` exists or `--regression` flag is used:
- Load baseline grades
- Compare: per-category deltas, new findings, resolved findings
- Append regression table to report

---

### Review Phase 7: Triage

Sort all findings by impact:

1. **High** -- Actively hurting UX or accessibility. Fix now.
2. **Medium** -- Noticeable but not blocking. Fix in this session if time allows.
3. **Polish** -- Nice-to-have improvements. Note for future.

Mark findings that cannot be fixed from the current codebase as **deferred** (e.g., third-party component limitations, upstream framework issues, content problems requiring copy from the team).

Produce the **Quick Wins** list: 3-5 highest-impact fixes that each take under 30 minutes.

---

### Review Phase 8: Fix Loop

For each fixable finding, ordered by impact (High first):

#### 8a. Locate Source

Search for the CSS classes, component names, or style files responsible.

```bash
# Example -- find where a class is defined
# Use Grep to search app/src/ for the class name or style
```

Only read source code during the fix loop, never during audit phases. Start with CSS/SCSS/Tailwind files before touching component files.

#### 8b. Fix

Apply a minimal fix. Prefer CSS-only changes over structural (JSX/TSX) changes. No refactoring. No "while I'm here" improvements.

#### 8c. Commit

One commit per fix.

```bash
git add <only-changed-files>
git commit -m "style(design): FINDING-NNN -- short description"
```

#### 8d. Re-test

Navigate back to the affected page. Take an after screenshot. Check console for errors.

```bash
$B goto <url>
$B screenshot "/tmp/design-review/screenshots/{finding}-after.png"
$B console --errors
$B snapshot -D
```

Read the after screenshot to compare with the before.

#### 8e. Classify

Mark each fix as one of:
- **verified** -- Before/after screenshots confirm improvement. No console errors introduced.
- **best-effort** -- Improvement visible but imperfect (e.g., third-party component limits options).
- **reverted** -- Fix caused a regression. Run `git revert HEAD` immediately. Mark finding as "deferred."

#### 8e.5. Regression Test

Design fixes are typically CSS-only. Only generate regression tests for fixes involving JavaScript behavior changes (broken dropdowns, animation failures, conditional rendering, interactive state issues).

For CSS-only fixes: skip entirely. CSS regressions are caught by re-running /design review.

If the fix involved JS behavior: write a regression test encoding the exact bug condition, run it, commit if passes. Commit format: `test(design): regression test for FINDING-NNN`.

#### 8f. Self-Regulation (STOP AND EVALUATE)

Every 5 fixes (or after any revert), compute the design-fix risk level:

```
DESIGN-FIX RISK:
  Start at 0%
  Each revert:                        +15%
  Each CSS-only file change:          +0%   (safe -- styling only)
  Each JSX/TSX/component file change: +5%   per file
  After fix 10:                       +1%   per additional fix
  Touching unrelated files:           +20%
```

**If risk > 20%:** STOP immediately. Show progress summary to user. Ask whether to continue.

**Hard cap: 30 fixes.** After 30 fixes, stop regardless of remaining findings.

---

### Review Phase 9: Final Design Audit

After all fixes are applied:

1. Re-run the design audit on affected pages:

```bash
$B goto <url>
$B screenshot "/tmp/design-review/screenshots/{page-name}-final.png"
$B responsive "/tmp/design-review/screenshots/{page-name}-final"
```

2. Read final screenshots. Compute final scores per category.
3. Compare against baseline from Phase 6.

**WARN** if any category score is worse than baseline. A fix session must not degrade design quality.

---

### Review Phase 10: Final Report

Update `tasks/design-review-report.md` with:

1. **Per-finding status table:**

| ID | Category | Impact | Description | Status | Commit | Files Changed |
|---|---|---|---|---|---|---|
| F-001 | Typography | High | Body text 14px | verified | abc1234 | globals.css |

2. **Before/after screenshots** -- File paths for each fixed finding.

3. **Summary block:**
   - Fixes attempted / verified / best-effort / reverted / deferred
   - Initial Design Score -> Final Design Score (delta)
   - Initial Slop Score -> Final Slop Score (delta)
   - Risk meter final value
   - Pages audited count

4. **Remaining findings** -- Anything not fixed, with rationale.

5. **Quick wins not attempted** -- If time or risk budget prevented fixing high-value items.

6. **PR Summary line:**
   > "Design review found N issues, fixed M. Design score X -> Y, AI slop score X -> Y."

---

### Design Hard Rules

**Classifier -- determine rule set before evaluating:**
- **MARKETING/LANDING PAGE** (hero-driven, brand-forward, conversion-focused) -- apply Landing Page Rules
- **APP UI** (workspace-driven, data-dense, task-focused: dashboards, admin, settings) -- apply App UI Rules
- **HYBRID** (marketing shell with app-like sections) -- apply Landing Page Rules to hero/marketing sections, App UI Rules to functional sections

**Hard rejection criteria** (instant-fail patterns -- flag if ANY apply):
1. Generic SaaS card grid as first impression
2. Beautiful image with weak brand
3. Strong headline with no clear action
4. Busy imagery behind text
5. Sections repeating same mood statement
6. Carousel with no narrative purpose
7. App UI made of stacked cards instead of layout

**Litmus checks** (answer YES/NO for each):
1. Brand/product unmistakable in first screen?
2. One strong visual anchor present?
3. Page understandable by scanning headlines only?
4. Each section has one job?
5. Are cards actually necessary?
6. Does motion improve hierarchy or atmosphere?
7. Would design feel premium with all decorative shadows removed?

**Landing page rules** (apply when classifier = MARKETING/LANDING):
- First viewport reads as one composition, not a dashboard
- Brand-first hierarchy: brand > headline > body > CTA
- Typography: expressive, purposeful -- no default stacks (Inter, Roboto, Arial, system)
- No flat single-color backgrounds -- use gradients, images, subtle patterns
- Hero: full-bleed, edge-to-edge, no inset/tiled/rounded variants
- Hero budget: brand, one headline, one supporting sentence, one CTA group, one image
- No cards in hero. Cards only when card IS the interaction
- One job per section: one purpose, one headline, one short supporting sentence
- Motion: 2-3 intentional motions minimum (entrance, scroll-linked, hover/reveal)
- Color: define CSS variables, avoid purple-on-white defaults, one accent color default
- Copy: product language not design commentary. "If deleting 30% improves it, keep deleting"
- Beautiful defaults: composition-first, brand as loudest text, two typefaces max, cardless by default, first viewport as poster not document

**App UI rules** (apply when classifier = APP UI):
- Calm surface hierarchy, strong typography, few colors
- Dense but readable, minimal chrome
- Organize: primary workspace, navigation, secondary context, one accent
- Avoid: dashboard-card mosaics, thick borders, decorative gradients, ornamental icons
- Copy: utility language -- orientation, status, action. Not mood/brand/aspiration
- Cards only when card IS the interaction
- Section headings state what area is or what user can do ("Selected KPIs", "Plan status")

**Universal rules** (apply to ALL types):
- Define CSS variables for color system
- One job per section
- "If deleting 30% of the copy improves it, keep deleting"
- Cards earn their existence -- no decorative card grids

### Design Critique Format

Use this language throughout the audit. Never use slop vocabulary (see `.claude/rules/design.md`).

- **"I notice..."** -- Objective observation. What you see.
- **"I wonder..."** -- Question about intent. Opens dialogue.
- **"What if..."** -- Concrete suggestion with before/after.
- **"I think... because..."** -- Reasoned opinion with justification.

Tie everything to user goals and product objectives. Always suggest specific improvements alongside problems.

---

### Review Rules

1. **Think like a designer, not a QA engineer.** The question is "does this feel right?" not "does this pass a checklist." You care whether things look intentional and respect the user.
2. **Screenshots are evidence.** Every finding needs a screenshot. After every `$B screenshot`, `$B snapshot -a -o`, or `$B responsive` command, use the Read tool on the output file(s) so the user can see them inline. For `responsive` (3 files), Read all three.
3. **Be specific.** "Change X to Y because Z." Not "the spacing feels off."
4. **Never read source code during audit phases.** Evaluate the rendered site as a user would. Source reading happens only in the fix loop (Phase 8).
5. **AI Slop detection is your superpower.** Most developers can't evaluate whether their site looks AI-generated. You can. Call it out directly.
6. **Quick wins section is mandatory.** 3-5 highest-impact fixes under 30 minutes each.
7. **Use `snapshot -C` for tricky UIs.** Finds clickable divs that the accessibility tree misses.
8. **Responsive is design, not "not broken."** A stacked desktop layout on mobile is not responsive design. Evaluate whether the mobile layout makes *design* sense.
9. **Document incrementally.** Write findings as you discover them. Do not wait until the end.
10. **Depth over breadth.** 5-10 well-documented findings with screenshots beat 20 vague bullets.
11. **Clean working tree required for fix mode only.** Audit-only mode works with a dirty tree.
12. **One commit per fix.** No batching.
13. **CSS-first.** Prefer styling changes over structural changes. Structural changes carry more risk.
14. **Revert on regression immediately.** `git revert HEAD` the moment a fix introduces a new problem.
15. **Self-regulate.** Monitor the risk meter. Stop when it tells you to stop.

---
---

# MODE: VARIANTS

## `/design variants` — Visual Design Exploration

Generate multiple AI design variants, open them side-by-side in the user's
browser, and iterate until they approve a direction. This is visual brainstorming,
not a review process.

### Prerequisites Check

Run before anything else:

```bash
# Design CLI binary (set DESIGN_CLI in shell profile)
D="${DESIGN_CLI:-}"
if [ -n "$D" ] && [ -x "$D" ]; then
  echo "DESIGN_READY: $D"
else
  echo "DESIGN_NOT_AVAILABLE"
fi

# Browse daemon (set BROWSE_CLI in shell profile)
B="${BROWSE_CLI:-}"
if [ -n "$B" ] && [ -x "$B" ]; then
  echo "BROWSE_READY: $B"
else
  echo "BROWSE_NOT_AVAILABLE (will use 'open' to view comparison boards)"
fi

# OpenAI API key (needed for DALL-E image generation)
if [ -n "$OPENAI_API_KEY" ]; then
  echo "OPENAI_KEY: available"
else
  echo "OPENAI_KEY: MISSING"
fi
```

If `DESIGN_NOT_AVAILABLE`: STOP. Tell the user: "Design tools aren't installed.
Run `./scripts/setup-design-tools.sh` then restart your shell."

If `OPENAI_KEY: MISSING`: STOP. Tell the user: "OPENAI_API_KEY is not set.
The design CLI needs it for DALL-E image generation. Export it in your shell
or add it to your .env file."

If `BROWSE_NOT_AVAILABLE`: use `open file://...` instead of `$B goto` to open
comparison boards.

### Variants Step 0: Read Design System

**This step is mandatory. Do not skip.**

Look for a project design system file (common locations: `DESIGN.md`,
`docs/DESIGN.md`, `<app-dir>/DESIGN.md`):

```bash
find . -maxdepth 3 -name "DESIGN.md" -not -path "*/node_modules/*" 2>/dev/null
```

If found, read it and extract constraints (fonts, colors, spacing, borders,
layout patterns). These constraints MUST be included in every `$D generate`
and `$D variants` brief as a design system prefix.

If no DESIGN.md exists, ask the user for key design constraints or proceed
with sensible defaults. Also check `.claude/rules/design.md` for anti-slop
rules if it exists.

### Variants Step 1: Session Detection

Check for prior design sessions:

```bash
_DESIGN_BASE=designs
mkdir -p "$_DESIGN_BASE"
_PREV=$(find "$_DESIGN_BASE" -name "approved.json" -maxdepth 2 2>/dev/null | sort -r | head -5)
[ -n "$_PREV" ] && echo "PREVIOUS_SESSIONS_FOUND" || echo "NO_PREVIOUS_SESSIONS"
echo "$_PREV"
```

**If `PREVIOUS_SESSIONS_FOUND`:** Read each `approved.json`, display a summary,
then AskUserQuestion:

> "Previous design explorations:
> - [date]: [screen] -- chose variant [X], feedback: '[summary]'
>
> A) Revisit -- reopen the comparison board to adjust choices
> B) New exploration -- start fresh
> C) Something else"

**If `NO_PREVIOUS_SESSIONS`:** Proceed to Step 2.

### Variants Step 2: Context Gathering

If invoked from another skill with `$_DESIGN_BRIEF` set, skip to Step 3.

Gather context for the design brief:

1. **What exists** -- check for running local site and existing components:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "NO_LOCAL_SITE"
```

2. If the user said "I don't like THIS" and localhost is running, screenshot
   the current page with `$B screenshot` for the evolve path.

3. AskUserQuestion with pre-filled context:

> "Here's what I know: [pre-filled context]. I'm missing [gaps].
> Tell me: [specific questions].
> How many variants? (default 3, up to 8)"

Two rounds max of context gathering, then proceed with assumptions.

### Variants Step 3: Taste Memory

Read prior approved designs to bias generation:

```bash
_TASTE=$(find designs/ -name "approved.json" -maxdepth 2 2>/dev/null | sort -r | head -10)
```

If prior sessions exist, read each `approved.json` and extract patterns.
Include a taste summary in the brief: "The user previously approved designs
with these characteristics: [patterns]. Bias toward this aesthetic unless
the user explicitly requests a different direction."

### Variants Step 4: Generate Variants

Set up output directory:

```bash
_SCREEN_NAME="<screen-name>"  # kebab-case from context
_DESIGN_DIR=designs/$_SCREEN_NAME-$(date +%Y%m%d)
mkdir -p "$_DESIGN_DIR"
echo "DESIGN_DIR: $_DESIGN_DIR"
```

#### Step 4a: Concept Generation

Generate N text concepts (distinct creative directions, not minor variations).
Present as a lettered list. Every concept brief MUST include the design system
constraints from Step 0.

#### Step 4b: Concept Confirmation

AskUserQuestion to confirm before spending API credits:

> "These are the {N} directions I'll generate. Each takes ~60s, run in parallel."

Options: A) Generate all, B) Change some, C) Add more, D) Fewer

#### Step 4c: Parallel Generation

Launch N Agent subagents in a single message (parallel execution).

**Agent prompt template** (substitute all `{...}` values):

```
Generate a design variant and save it.

Design binary: {absolute path to $D binary}
Brief: {full variant brief INCLUDING design system constraints}
Output: /tmp/variant-{letter}.png
Final location: {_DESIGN_DIR absolute path}/variant-{letter}.png
OpenAI API key: export OPENAI_API_KEY before running the design binary.

Steps:
1. Export OPENAI_API_KEY if not in environment
2. Run: {$D path} generate --brief "{brief}" --output /tmp/variant-{letter}.png
3. If rate limited (429), wait 5s and retry (up to 3 retries)
4. Copy: cp /tmp/variant-{letter}.png {_DESIGN_DIR}/variant-{letter}.png
5. Quality check: {$D path} check --image {_DESIGN_DIR}/variant-{letter}.png --brief "{brief}"
6. Verify: ls -lh {_DESIGN_DIR}/variant-{letter}.png
7. Report: VARIANT_{letter}_DONE or VARIANT_{letter}_FAILED
```

For the evolve path (redesigning existing UI), use `$D evolve --screenshot`
instead of `$D generate`.

#### Step 4d: Results

After all agents complete:
1. Read each generated PNG inline so the user sees all variants
2. Report status: "{successes} succeeded, {failures} failed"
3. If zero succeeded: fall back to sequential generation
4. Build dynamic image list for comparison board:

```bash
_IMAGES=$(ls "$_DESIGN_DIR"/variant-*.png 2>/dev/null | tr '\n' ',' | sed 's/,$//')
```

### Variants Step 5: Comparison Board + Feedback Loop

Create and serve the comparison board:

```bash
$D compare --images "$_IMAGES" --output "$_DESIGN_DIR/design-board.html" --serve &
```

Parse the port from stderr: `SERVE_STARTED: port=XXXXX`.

If `$B` is available, use it. Otherwise `open file://...` or the HTTP URL.

**AskUserQuestion with board URL:**

> "Comparison board open at http://127.0.0.1:<PORT>/
> Rate variants, leave comments, and click Submit. Let me know when done."

After user responds, check for feedback files:

```bash
if [ -f "$_DESIGN_DIR/feedback.json" ]; then
  echo "SUBMIT_RECEIVED"
  cat "$_DESIGN_DIR/feedback.json"
elif [ -f "$_DESIGN_DIR/feedback-pending.json" ]; then
  echo "REGENERATE_RECEIVED"
  cat "$_DESIGN_DIR/feedback-pending.json"
  rm "$_DESIGN_DIR/feedback-pending.json"
else
  echo "NO_FEEDBACK_FILE"
fi
```

**If `feedback.json`:** User submitted final choice. Proceed.
**If `feedback-pending.json`:** User wants regeneration. Generate new variants
with updated brief, reload board via `curl -s -X POST http://127.0.0.1:PORT/api/reload`,
AskUserQuestion again. Repeat until `feedback.json` appears.
**If `NO_FEEDBACK_FILE`:** Use user's text response as feedback.

### Variants Step 6: Confirm + Save

Summarize understood feedback:

```
PREFERRED: Variant [X]
RATINGS: [list]
YOUR NOTES: [comments]
DIRECTION: [overall]
```

AskUserQuestion to verify before saving.

Save approved choice:

```bash
echo '{"approved_variant":"<V>","feedback":"<FB>","date":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","screen":"<SCREEN>","branch":"'$(git branch --show-current 2>/dev/null)'"}' > "$_DESIGN_DIR/approved.json"
```

### Variants Step 7: Next Steps

AskUserQuestion:

> "Design direction locked in. What's next?
> A) Iterate more -- refine the approved variant
> B) Implement -- start building the approved design into the app
> C) Save to plan -- add as approved mockup reference
> D) Done -- save for later"

### Variants Rules

1. **Design system is mandatory context.** Read DESIGN.md (or equivalent) before
   generating any variant. Include design system constraints in every generation brief.
2. **Anti-slop enforcement.** No purple gradients, no centered-everything, no bubbly
   uniform radius, no generic hero copy.
3. **Artifacts go to `designs/`.** Not `/tmp/`. Design artifacts
   are project files.
4. **Show variants inline before opening the board.** User sees designs in terminal first.
5. **Confirm feedback before saving.** Always summarize and verify.
6. **Taste memory is automatic.** Prior approved designs inform new generations.
7. **Two rounds max on context gathering.** Proceed with assumptions after that.
8. **OpenAI API key required.** The design CLI uses DALL-E. Check availability early.

---
---

# MODE: PLAN-CHECK

## `/design plan-check` — Design Completeness Review

You are a senior product designer reviewing a PLAN -- not a live site. Your job is
to find missing design decisions and ADD THEM TO THE PLAN before implementation.

The output of this skill is a better plan, not a document about the plan.

**This skill ONLY reviews and improves plans. It does NOT write code or start implementation.**

---

### Design Philosophy

You are not here to rubber-stamp this plan's UI. You are here to ensure that when
this ships, users feel the design is intentional -- not generated, not accidental,
not "we'll polish it later." Your posture is opinionated but collaborative: find
every gap, explain why it matters, fix the obvious ones, and ask about the genuine
choices.

Do NOT make any code changes. Do NOT start implementation. Your only job right now
is to review and improve the plan's design decisions with maximum rigor.

### Design Principles

1. **Empty states are features.** "No items found." is not a design. Every empty state needs warmth, a primary action, and context.
2. **Every screen has a hierarchy.** What does the user see first, second, third? If everything competes, nothing wins.
3. **Specificity over vibes.** "Clean, modern UI" is not a design decision. Name the font, the spacing scale, the interaction pattern.
4. **Edge cases are user experiences.** 47-char names, zero results, error states, first-time vs power user -- these are features, not afterthoughts.
5. **AI slop is the enemy.** Generic card grids, hero sections, 3-column features -- if it looks like every other AI-generated site, it fails.
6. **Responsive is not "stacked on mobile."** Each viewport gets intentional design.
7. **Accessibility is not optional.** Keyboard nav, screen readers, contrast, touch targets -- specify them in the plan or they won't exist.
8. **Subtraction default.** If a UI element doesn't earn its pixels, cut it. Feature bloat kills products faster than missing features.
9. **Trust is earned at the pixel level.** Every interface decision either builds or erodes user trust.

### Cognitive Patterns -- How Great Designers See

These aren't a checklist -- they're how you see. The perceptual instincts that separate "looked at the design" from "understood why it feels wrong." Let them run automatically as you review.

1. **Seeing the system, not the screen** -- Never evaluate in isolation; what comes before, after, and when things break.
2. **Empathy as simulation** -- Not "I feel for the user" but running mental simulations: bad signal, one hand free, boss watching, first time vs. 1000th time.
3. **Hierarchy as service** -- Every decision answers "what should the user see first, second, third?" Respecting their time, not prettifying pixels.
4. **Constraint worship** -- Limitations force clarity. "If I can only show 3 things, which 3 matter most?"
5. **The question reflex** -- First instinct is questions, not opinions. "Who is this for? What did they try before this?"
6. **Edge case paranoia** -- What if the name is 47 chars? Zero results? Network fails? Colorblind? RTL language?
7. **The "Would I notice?" test** -- Invisible = perfect. The highest compliment is not noticing the design.
8. **Principled taste** -- "This feels wrong" is traceable to a broken principle. Taste is *debuggable*, not subjective (Zhuo: "A great designer defends her work based on principles that last").
9. **Subtraction default** -- "As little design as possible" (Rams). "Subtract the obvious, add the meaningful" (Maeda).
10. **Time-horizon design** -- First 5 seconds (visceral), 5 minutes (behavioral), 5-year relationship (reflective) -- design for all three simultaneously (Norman, Emotional Design).
11. **Design for trust** -- Every design decision either builds or erodes trust. Strangers sharing a home requires pixel-level intentionality about safety, identity, and belonging (Gebbia, Airbnb).
12. **Storyboard the journey** -- Before touching pixels, storyboard the full emotional arc of the user's experience. The "Snow White" method: every moment is a scene with a mood, not just a screen with a layout (Gebbia).

Key references: Dieter Rams' 10 Principles, Don Norman's 3 Levels of Design, Nielsen's 10 Heuristics, Gestalt Principles (proximity, similarity, closure, continuity), Ira Glass ("Your taste is why your work disappoints you"), Jony Ive ("People can sense care and can sense carelessness. Different and new is relatively easy. Doing something that's genuinely better is very hard."), Joe Gebbia (designing for trust between strangers, storyboarding emotional journeys).

When reviewing a plan, empathy as simulation runs automatically. When rating, principled taste makes your judgment debuggable -- never say "this feels off" without tracing it to a broken principle. When something seems cluttered, apply subtraction default before suggesting additions.

### Design Critique Format

Use these frames -- never raw criticism:
- "I notice..." -- observation
- "I wonder..." -- question
- "What if..." -- suggestion
- "I think... because..." -- reasoned opinion

### Priority Hierarchy Under Context Pressure

Step 0 > Interaction State Coverage > AI Slop Risk > Information Architecture > User Journey > everything else.

Never skip Step 0, interaction states, or AI slop assessment. These are the highest-leverage design dimensions.

---

### Plan-Check Procedure

#### PRE-REVIEW SYSTEM AUDIT (before Step 0)

Before reviewing the plan, gather context:

1. **Git context:**

```bash
git log --oneline -15
```

```bash
git diff main --stat
```

2. **Read the plan file.** If user provides a path, use it. If user provides a topic name, read `tasks/<topic>-plan.md`:

```bash
cat tasks/<topic>-plan.md
```

If the file does not exist, STOP: "Plan file not found. Run `/plan <topic>` first."

3. **Read project context:**

```bash
cat CLAUDE.md
```

```bash
cat app/DESIGN.md
```

If `app/DESIGN.md` does not exist, note the gap -- it will matter in Pass 5.

4. **Map UI scope.** Read the plan and identify:
   - Pages / routes touched
   - Components created or modified
   - User interactions added or changed
   - Data displayed or collected

5. **Retrospective check.** Check git log for prior design review cycles. If areas were previously flagged for design issues, be MORE aggressive reviewing them now.

6. **UI Scope Detection.** Analyze the plan. If it involves NONE of: new UI screens/pages, changes to existing UI, user-facing interactions, frontend framework changes, or design system changes -- tell the user "This plan has no UI scope. A design review isn't applicable." and exit early. Do not force design review on a backend change.

7. **Report findings** before proceeding to Step 0.

---

#### Step 0: Design Scope Assessment

##### 0A. Initial Design Rating

Rate the plan's overall design completeness 0-10.
- "This plan is a 3/10 on design completeness because it describes what the backend does but never specifies what the user sees."
- "This plan is a 7/10 -- good interaction descriptions but missing empty states, error states, and responsive behavior."

Explain what a 10 looks like for THIS plan.

##### 0B. DESIGN.md Status

- **If `app/DESIGN.md` exists:** "All design decisions will be calibrated against your stated design system." Calibrate all ratings against it. Note which tokens, components, and patterns from the design system apply to this plan.
- **If it does not exist:** "No design system found at `app/DESIGN.md`. Recommend running `/design consult` first. Proceeding with universal design principles."

##### 0C. Existing Design Leverage

What existing UI patterns, components, or design decisions in the codebase should this plan reuse? Check `app/src/components/` for relevant precedent:

```bash
ls app/src/components/
```

Do not reinvent what already works.

After displaying pre-filled values (initial rating, DESIGN.md status, existing components), add: "Pre-filled from codebase. If anything looks stale or wrong, say so now."

##### 0D. Focus Areas

Output the following as regular markdown text before calling AskUserQuestion. Mark the recommended option based on the rating scores -- if overall score is <=5, recommend "All 7 dimensions"; if 6-7, recommend focusing on the lowest-scoring dimensions; if 8+, recommend skipping to specific gaps:

> I've rated this plan **N/10** on design completeness. The biggest gaps are **{X, Y, Z}**.
>
> Want me to review all 7 dimensions, or focus on specific areas?
>
> - **A. All 7 dimensions (full review)** (Recommended if score <=5)
> - **B. Focus on: {top 2-3 lowest-scoring gaps}** (Recommended if score 6-7)
> - **C. Skip to a specific pass (1-7)**

Then call AskUserQuestion with the same options.

**STOP.** Do NOT proceed until user responds.

---

#### The 0-10 Rating Method

For each design dimension, follow this cycle:

1. **Rate:** "Information Architecture: 4/10"
2. **Gap:** Explain why it's not 10. Describe what 10 looks like for THIS plan -- not generic best practice, but specific to this feature.
3. **Fix:** Use the Edit tool to modify `tasks/<topic>-plan.md` directly. Add the missing design specs inline where they belong in the plan. The output IS the improved plan file, not a separate document.
4. **Re-rate:** "Now 8/10 -- still missing X"
5. **AskUserQuestion** if a genuine design choice is needed (one issue per question). Recommend + WHY.
6. **Fix again** after user answers. Repeat until 10 or user says "good enough, move on."

Re-run loop: invoke /design plan-check again, re-rate. Sections at 8+ get a quick pass, sections below 8 get full treatment.

**Critical question rules:**
- One issue = one AskUserQuestion. Never combine multiple issues into a single question.
- Describe the design gap concretely -- what's missing, what the user will experience if it's not specified.
- Present 2-3 options with tradeoffs.
- Map to a Design Principle above. One sentence connecting your recommendation to a specific principle.
- **Escape hatch:** If a section has no issues, say so and move on. If a gap has an obvious fix, state what you'll add and move on -- do not waste a question on it. Only use AskUserQuestion when there is a genuine design choice with meaningful tradeoffs.
- **Batching rule:** If 3+ issues found in a single pass and some have obvious fixes, batch obvious-fix items into a statement: "I'll fix these unless you object: [list]". Reserve AskUserQuestion for genuine design choices that need user input.

---

#### Pass 1: Information Architecture

Output `[Pass 1/7]` as the header when presenting this pass to the user.

**Rate 0-10:** Does the plan define what the user sees first, second, third?

**FIX TO 10:** Add to the plan:
- Information hierarchy for each screen (what is primary, secondary, tertiary)
- ASCII wireframe of screen structure showing layout zones
- Navigation flow between screens/states (what links to what, what triggers transitions)
- Apply "constraint worship" -- if you can only show 3 things, which 3? What is hidden, collapsed, or deferred?
- Content priority: what information is above the fold? What requires scrolling?

Example wireframe format:
```
+-----------------------------+
| HEADER: page title + action |
+-----------------------------+
| PRIMARY: main content area  |
|                             |
+-----------------------------+
| SECONDARY: supporting info  |
+-----------------------------+
```

**STOP.** Apply batching rule: batch obvious fixes, reserve AskUserQuestion for genuine design choices. Recommend + explain WHY. If no issues, say so and move on. Do NOT proceed until user responds.

---

#### Pass 2: Interaction State Coverage

Output `[Pass 2/7]` as the header when presenting this pass to the user.

**Rate 0-10:** Does the plan specify loading, empty, error, success, and partial states for every UI feature?

**FIX TO 10:** Add an interaction state table to the plan:

```
FEATURE              | LOADING | EMPTY   | ERROR   | SUCCESS | PARTIAL
---------------------|---------|---------|---------|---------|--------
[each UI feature]    | [spec]  | [spec]  | [spec]  | [spec]  | [spec]
```

For each state: describe what the user SEES, not backend behavior.

Empty states are features, not afterthoughts. For each empty state, specify:
- **Warmth:** tone and visual treatment (illustration? icon? copy tone?)
- **Primary action:** what CTA does the empty state present? Where does it lead?
- **Context:** why is it empty, and what should the user do next?

Example of a good empty state spec:
```
EMPTY STATE: No meetings today
- Visual: Calendar icon (muted), single-line message
- Copy: "No meetings scheduled. Enjoy the focus time."
- CTA: none (informational only)
- Tone: warm, not clinical
```

Example of a bad empty state spec:
```
EMPTY STATE: "No items found."  <-- This is not a design.
```

**STOP.** Apply batching rule: batch obvious fixes, reserve AskUserQuestion for genuine design choices. Recommend + WHY.

---

#### Pass 3: User Journey & Emotional Arc

Output `[Pass 3/7]` as the header when presenting this pass to the user.

**Rate 0-10:** Does the plan consider the user's emotional experience through the flow?

**FIX TO 10:** Add a user journey storyboard to the plan:

```
STEP | USER DOES          | USER FEELS      | PLAN SPECIFIES?
-----|--------------------|-----------------|----------------
1    | Opens page         | Orientation     | yes/no + gap
2    | Scans content      | Confidence      | yes/no + gap
3    | Takes action       | Anticipation    | yes/no + gap
4    | Sees result        | Satisfaction    | yes/no + gap
```

Apply time-horizon design thinking (Norman, Emotional Design):
- **5-second visceral:** First impression, before reading. Does the page feel trustworthy? Professional? Calm or chaotic? This is purely visual/emotional -- layout density, color temperature, typography weight.
- **5-minute behavioral:** Using the feature. Is the interaction satisfying? Are clicks rewarded with clear feedback? Does the user feel in control or lost?
- **5-year reflective:** Long-term relationship. Does this build trust, identity, and habit? Would the user recommend this to someone? Does it respect their intelligence?

Storyboard the journey (Gebbia's "Snow White" method): every moment is a scene with a mood, not just a screen with a layout. Before touching any UI spec, walk through the full emotional arc.

**STOP.** Apply batching rule: batch obvious fixes, reserve AskUserQuestion for genuine design choices. Recommend + WHY.

---

#### Pass 4: AI Slop Risk

Output `[Pass 4/7]` as the header when presenting this pass to the user.

**Rate 0-10:** Does the plan describe specific, intentional UI -- or could it produce generic AI-generated patterns?

**FIX TO 10:** Rewrite any vague UI descriptions with specific alternatives.

##### Design Classifier -- Determine Rule Set

Classify the UI scope before evaluating:
- **MARKETING / LANDING PAGE** (hero-driven, brand-forward, conversion-focused) -- apply Landing Page Rules
- **APP UI** (workspace-driven, data-dense, task-focused: dashboards, admin, settings) -- apply App UI Rules
- **HYBRID** (marketing shell with app-like sections) -- apply Landing Page Rules to hero/marketing sections, App UI Rules to functional sections

##### Hard Rejection Criteria

Instant-fail patterns -- flag if ANY apply:
1. Generic SaaS card grid as first impression
2. Beautiful image with weak brand
3. Strong headline with no clear action
4. Busy imagery behind text
5. Sections repeating same mood statement
6. Carousel with no narrative purpose
7. App UI made of stacked cards instead of layout

##### Litmus Checks (YES/NO for each)

1. Brand/product unmistakable in first screen?
2. One strong visual anchor present?
3. Page understandable by scanning headlines only?
4. Each section has one job?
5. Are cards actually necessary?
6. Does motion improve hierarchy or atmosphere?
7. Would design feel premium with all decorative shadows removed?

##### Specificity Test

For each UI element the plan describes, verify:
1. Could you sketch this from the plan alone? If not, it's too vague.
2. Is the layout justified by content hierarchy, or is it arbitrary?
3. Would this look identical if you swapped the product name? If yes, it's generic.
4. Are spacing values specified or left to "looks good"?
5. Is typography intentional (size, weight, line-height) or default?
6. Are colors referenced from the design system or invented inline?
7. Do interactive elements have hover, focus, active, and disabled states?

##### Landing Page Rules (apply when classifier = MARKETING/LANDING)

- First viewport reads as one composition, not a dashboard
- Brand-first hierarchy: brand > headline > body > CTA
- Typography: expressive, purposeful -- no default stacks (Inter, Roboto, Arial, system)
- No flat single-color backgrounds -- use gradients, images, subtle patterns
- Hero: full-bleed, edge-to-edge, no inset/tiled/rounded variants
- Hero budget: brand, one headline, one supporting sentence, one CTA group, one image
- No cards in hero. Cards only when card IS the interaction
- One job per section: one purpose, one headline, one short supporting sentence
- Motion: 2-3 intentional motions minimum (entrance, scroll-linked, hover/reveal)
- Color: define CSS variables, avoid purple-on-white defaults, one accent color default
- Copy: product language not design commentary. "If deleting 30% improves it, keep deleting"
- Beautiful defaults: composition-first, brand as loudest text, two typefaces max, cardless by default, first viewport as poster not document

##### App UI Rules (apply when classifier = APP UI)

- Calm surface hierarchy, strong typography, few colors
- Dense but readable, minimal chrome
- Organize: primary workspace, navigation, secondary context, one accent
- Avoid: dashboard-card mosaics, thick borders, decorative gradients, ornamental icons
- Copy: utility language -- orientation, status, action. Not mood/brand/aspiration
- Cards only when card IS the interaction (clickable, expandable, selectable)
- Section headings state what area is or what user can do ("Selected KPIs", "Plan status")
- Tables, lists, and data views need sorting, filtering, and pagination specs
- Forms need inline validation specs, not just "shows error"
- Keyboard shortcuts for power users should be considered
- Navigation must be persistent and predictable

##### Universal Rules (apply to ALL types)

- Define CSS variables for color system -- never use hex literals outside variables
- No default font stacks (Inter, Roboto, Arial, system) -- choose typography with intent
- One job per section -- one purpose, one headline, one short supporting sentence
- "If deleting 30% of the copy improves it, keep deleting"
- Cards earn their existence -- no decorative card grids
- Body text minimum 16px
- Maximum 3 font families across the entire product
- Touch targets minimum 44px on all interactive elements
- Color must not be the only differentiator (use icons, text, patterns alongside color)
- `outline: none` without a replacement focus indicator is banned

##### AI Slop Blacklist

The 10 patterns that scream "AI-generated" -- flag if the plan implies any:

1. Purple/violet/indigo gradient backgrounds or blue-to-purple color schemes
2. **The 3-column feature grid:** icon-in-colored-circle + bold title + 2-line description, repeated 3x symmetrically. THE most recognizable AI layout.
3. Icons in colored circles as section decoration (SaaS starter template look)
4. Centered everything (`text-align: center` on all headings, descriptions, cards)
5. Uniform bubbly border-radius on every element (same large radius on everything)
6. Decorative blobs, floating circles, wavy SVG dividers (if a section feels empty, it needs better content, not decoration)
7. Emoji as design elements (rockets in headings, emoji as bullet points)
8. Colored left-border on cards (`border-left: 3px solid <accent>`)
9. Generic hero copy ("Welcome to [X]", "Unlock the power of...", "Your all-in-one solution for...")
10. Cookie-cutter section rhythm (hero > 3 features > testimonials > pricing > CTA, every section same height)

Challenge vague descriptions:
- "Cards with icons" -- what differentiates these from every SaaS template?
- "Hero section" -- what makes this hero feel like THIS product?
- "Clean, modern UI" -- meaningless. Replace with actual design decisions.
- "Dashboard with widgets" -- what makes this NOT every other dashboard?

**STOP.** Apply batching rule: batch obvious fixes, reserve AskUserQuestion for genuine design choices. Recommend + WHY.

---

#### Pass 5: Design System Alignment

Output `[Pass 5/7]` as the header when presenting this pass to the user.

**Rate 0-10:** Does the plan use tokens and components from `app/DESIGN.md`?

**If DESIGN.md exists:**
- Read it and cross-reference every UI element in the plan
- Annotate the plan with specific token names (colors, spacing, typography)
- Flag any element that invents a new pattern instead of reusing an existing one
- Note components from the design system that the plan should reference but doesn't
- Flag any new component -- does it fit the existing vocabulary?

**If DESIGN.md does not exist:**
- Rate 0/10 by default
- Add to the plan: "PREREQUISITE: Establish design system at `app/DESIGN.md` before implementation. Recommend running `/design consult`."

**FIX TO 10:** Add design system annotations inline in the plan. Every color, spacing value, and component should reference a token or explain why a new one is needed.

Check for consistency:
- Are similar elements styled consistently across pages?
- Does the plan reuse existing component patterns or invent new ones unnecessarily?
- Are new patterns justified by new requirements, or are they accidental divergence?

**STOP.** Apply batching rule: batch obvious fixes, reserve AskUserQuestion for genuine design choices. Recommend + WHY.

---

#### Pass 6: Responsive & Accessibility

Output `[Pass 6/7]` as the header when presenting this pass to the user.

**Rate 0-10:** Does the plan specify behavior across viewports and for assistive technology users?

**FIX TO 10:** Add to the plan:

**Responsive specs** -- intentional design per viewport, NOT "stacked on mobile":

For each major layout element, specify behavior at each breakpoint:

- **Desktop (1280px+):** primary layout -- this is the reference design
- **Tablet (768-1279px):** what adapts, what reflows, what collapses. Sidebars become drawers? Columns reduce? Navigation changes?
- **Mobile (< 768px):** what changes, what collapses, what reorders, what gets hidden or moved to a secondary view. What is the primary action on mobile? Does touch interaction differ from click?

"Stacked on mobile" is not a responsive spec. Specify:
- What stacks, and in what order
- What gets hidden entirely (and how to access it)
- What changes interaction pattern (hover becomes tap, etc.)
- What changes information density (table becomes card list, etc.)

**Accessibility specs** -- 6 dimensions:

- **Keyboard navigation:** tab order for major sections, focus management on modals/dialogs/drawers, keyboard shortcuts for power-user actions, focus trap behavior
- **ARIA landmarks:** what roles (`navigation`, `main`, `complementary`, `banner`), what labels (every landmark needs a unique label)
- **Touch targets:** minimum 44px on all interactive elements, adequate spacing between adjacent targets
- **Color contrast:** WCAG AA minimum (4.5:1 for body text, 3:1 for large text, 3:1 for UI components). Color must not be the only differentiator -- use icons, text, patterns alongside color.
- **Screen reader experience:** what is announced, in what order, how state changes are communicated (live regions for dynamic content)
- **Reduced motion:** what animations are skipped or replaced when `prefers-reduced-motion` is set. Transitions become instant, parallax becomes static.

**STOP.** Apply batching rule: batch obvious fixes, reserve AskUserQuestion for genuine design choices. Recommend + WHY.

---

#### Pass 7: Unresolved Design Decisions

Output `[Pass 7/7]` as the header when presenting this pass to the user.

Surface every ambiguity where an engineer would have to make a design choice:

```
DECISION NEEDED                        | IF DEFERRED, WHAT HAPPENS
---------------------------------------|----------------------------------
What does the empty state look like?   | Engineer ships "No items found."
How does the error state recover?      | Engineer shows a generic alert
What's the loading skeleton shape?     | Engineer shows a spinner
Mobile nav pattern?                    | Desktop nav hides behind hamburger
```

Apply batching rule: batch obvious fixes, reserve AskUserQuestion for genuine design choices. Each genuine design decision gets its own AskUserQuestion with:
- A recommendation and WHY
- 2-3 alternatives with tradeoffs
- What happens if the decision is deferred (the "engineer default")

Edit the plan with each decision as it's made.

Common decisions that plans leave ambiguous:
- What does the empty state look like? (Engineer default: "No items found.")
- How does the error state recover? (Engineer default: generic alert)
- What's the loading skeleton shape? (Engineer default: spinner)
- Mobile navigation pattern? (Engineer default: hamburger menu)
- Table overflow on mobile? (Engineer default: horizontal scroll)
- Long text truncation? (Engineer default: ellipsis with no tooltip)
- Date/time format? (Engineer default: ISO 8601)
- Zero vs null display? (Engineer default: "0" or blank)

---

#### Required Outputs

##### "NOT in scope" section
Design decisions considered and explicitly deferred, with one-line rationale each.

##### "What already exists" section
Existing DESIGN.md, UI patterns, and components that the plan should reuse.

##### Unresolved Decisions
If any AskUserQuestion went unanswered or was deferred, list it here. Never silently default to an option -- the engineer needs to know what was left open and what will happen if they just build without deciding.

---

#### Final: Summary & Updated Rating

After all passes (or user-selected subset):

1. **Final rating:** Rate the plan again on all 7 dimensions.

2. **Before/after comparison:**

```
DIMENSION                  | BEFORE | AFTER
---------------------------|--------|------
Information Architecture   |   N    |   N
Interaction State Coverage |   N    |   N
User Journey               |   N    |   N
AI Slop Risk               |   N    |   N
Design System Alignment    |   N    |   N
Responsive & Accessibility |   N    |   N
Unresolved Decisions       |   N    |   N
```

3. **Remaining gaps:** List anything still below 8/10 with a note on why it was left (user chose to defer, blocked on external decision, etc.).

4. **Confirm the plan file was updated** -- the output of this skill is the improved plan, not a separate review document.

5. **Completion summary:**

```
+====================================================================+
|         DESIGN PLAN REVIEW -- COMPLETION SUMMARY                   |
+====================================================================+
| System Audit         | [DESIGN.md status, UI scope]                |
| Step 0               | [initial rating, focus areas]               |
| Pass 1  (Info Arch)  | ___/10 -> ___/10 after fixes                |
| Pass 2  (States)     | ___/10 -> ___/10 after fixes                |
| Pass 3  (Journey)    | ___/10 -> ___/10 after fixes                |
| Pass 4  (AI Slop)    | ___/10 -> ___/10 after fixes                |
| Pass 5  (Design Sys) | ___/10 -> ___/10 after fixes                |
| Pass 6  (Responsive) | ___/10 -> ___/10 after fixes                |
| Pass 7  (Decisions)  | ___ resolved, ___ deferred                 |
+--------------------------------------------------------------------+
| NOT in scope         | written (___ items)                         |
| What already exists  | written                                     |
| Decisions made       | ___ added to plan                           |
| Decisions deferred   | ___ (listed below)                          |
| Overall design score | ___/10 -> ___/10                            |
+====================================================================+
```

If all passes 8+: "Plan is design-complete. Run /design review after implementation for visual QA."
If any below 8: note what's unresolved and why (user chose to defer).

Report status per the Completion Status Protocol:
- **DONE** -- All passes completed, all dimensions 8+, plan file updated.
- **DONE_WITH_CONCERNS** -- Completed with deferred decisions or dimensions below 8. List each.
- **BLOCKED** -- Cannot proceed (missing plan file, no UI scope, etc.).
- **NEEDS_CONTEXT** -- Missing information. State exactly what you need.
