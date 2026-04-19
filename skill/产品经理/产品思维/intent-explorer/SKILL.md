---
name: intent-explorer
description: Use when starting a new feature, product idea, or problem exploration and the real user need is unclear. Trigger on "intent", "explore intent", "intentspec", "what should we build", "what's the real problem", "explore this idea", "user research", "discovery", "requirements grounding", or before any specification work.
---

# Intent Explorer

## Mission

Explore the intent behind a problem or idea through structured interactive dialogue. Produce an intentSpec — a structured, agent-ready specification precise enough that an AI agent can execute it without guessing.

## When to Use

- Starting a new feature and the user problem isn't well-defined
- Ambiguous goals where stakeholders disagree on what to build
- Before `/kiro:spec-init` when no `intent-spec.md` or `discovery.md` exists
- User says "what should we build", "what's the real problem", "explore this idea"
- High-stakes decisions where getting the intent wrong is costly

## When NOT to Use

- Bug fixes with clear reproduction steps — just fix them
- Well-scoped tasks where the user already has measurable success criteria
- When `intent-spec.md` already exists for this feature
- Pure implementation questions ("how do I build X") — this explores _what_ and _why_, not _how_

## Hard Rules

- **Synthesize, don't transcribe** — elevate raw answers to product language
- **Validate before writing** — present the full intentSpec draft for approval before writing to disk
- **No solution design** — this skill explores intent, not implementation

## Interaction Model — CRITICAL

This is a **conversational** skill. Each question-answer pair is one turn.

**Per turn:**

1. Ask exactly ONE question using AskUserQuestion (with 2-4 options plus "Other" for free text)
2. **STOP. Wait for the user's response.**
3. Read and incorporate their answer
4. Adapt the next question based on what you learned
5. Repeat

**NEVER call AskUserQuestion more than once per response.** Each response contains at most one AskUserQuestion call. Between questions, you may add a brief synthesis of what you heard (1-2 sentences max) to show you're tracking.

**AskUserQuestion format — every question MUST have options:**

```
AskUserQuestion with:
- question: "Your question here?"
- options: 2-4 concrete choices relevant to the problem context
- The user can always select "Other" for free-text input
```

## Entry Point

1. Read the problem description from $ARGUMENTS
2. Ask the user to choose exploration depth:

   > "What depth of exploration does this need?"
   >
   > - **Quick** — Well-scoped change, known user problem (~6-8 questions)
   > - **Deep** — Ambiguous goal, novel territory, high stakes (~15-20 questions)

3. Generate a feature slug from the description (kebab-case, 2-4 words)
4. Create `.kiro/specs/<slug>/` directory if it doesn't exist
5. Proceed to the selected mode

## Quick Mode — JTBD-Focused Exploration

Read `references/jtbd-framework.md` for methodology, examples, and calibration.

### Phase: Context & JTBD (~6-8 questions)

Cover these topics through conversation. Ask ONE question per turn, wait for the answer, then ask the next. Adapt phrasing and options to the specific problem. Skip or combine topics if the user's earlier answers already covered them.

**Topics to cover (in rough order):**

- **Situation & trigger** — What's happening that makes this a priority now?
- **Who** — Who has this problem? What's their role/context?
- **Functional job** — What is this person trying to accomplish? (Format: "Help me [verb] [object]")
- **Emotional dimension** — How do they want to feel? (Format: "Make me feel [emotion]")
- **Social dimension** — How do they want to be perceived? (Skip if not contextually relevant)
- **Current alternatives** — What do they do today instead? Think through the job lens — real competition, not category competition. (Netflix competes with sleep, not just Hulu.)
- **Residual pain** — What's frustrating or broken about those alternatives?
- **Desired outcomes** — What does measurable success look like? (Push for 2-3 specific criteria)

### Synthesis

After all questions, synthesize:

1. **Job Statement**: "When [situation], I want [motivation], so I can [outcome]"
2. **Forces of Progress**: Assess Push + Pull vs Anxiety + Habit
3. **Opportunity Score**: Rate importance and current satisfaction

Present the synthesis and ask: "Does this capture the intent accurately?"

If yes → proceed to intentSpec generation.
If no → ask which part needs correction, adjust, and re-validate.

## Deep Mode — Three Compounding Lenses

### Phase 1: JTBD Exploration (~6-8 questions)

Same as Quick Mode above. Produces JTBD statement + Forces + Opportunity Score.

After synthesis, checkpoint: "Phase 1 complete. Does this track before we go deeper?"

### Phase 2: First Principles Decomposition (~5-6 questions)

Read `references/first-principles-framework.md` for methodology, traps, and examples.

Cover these topics ONE question per turn. Wait for each answer before proceeding.

- **Surface assumptions** — Present 3-5 candidate assumptions derived from Phase 1 answers. Ask which the user would add or challenge.
- **Trap check** — For challenged assumptions, check against the 4 traps (Industry Standard, Customer Said, Technology Exists, Competitor Does It). Present findings and ask for agreement.
- **Decompose to atoms** — Walk down the decomposition ladder (Surface → Functional → Emotional → Fundamental → Atomic). Ask: "Does this hit bedrock?"
- **Rebuild** — Present a rebuilt direction from fundamental truths only. Ask for reaction.
- **Compare** — "If we were starting from scratch today with no legacy, would we build it this way?"

Synthesis checkpoint: "Phase 2 complete. Here are the assumptions we challenged and the fundamental truths we found. Does this hold?"

### Phase 3: Cross-Pollination (~4-5 questions)

Read `references/cross-pollination-framework.md` for the industry library and examples.

Cover these topics ONE question per turn. Wait for each answer before proceeding.

- **Strip context** — Restate the core job without domain jargon. Ask: "Is this the right framing?"
- **Industry lookup** — Propose 3 surprising industries as AskUserQuestion options. Ask which 1-2 to explore.
- **Extract principles** — For selected industries, present how they solve it and the underlying principle. Ask which principles resonate.
- **Translate** — Adapt strongest principles to the user's context. Ask: "Does this spark anything?"

Synthesis: "Phase 3 complete. Here's the combined cross-pollination insight."

## IntentSpec Generation

After all phases complete:

1. Read `templates/intent-spec.md` for the output structure
2. Fill in all sections from the exploration:
   - **Objective** — from Phase 1 situation + trigger + JTBD evidence
   - **User Goal** — job statement + dimensions + forces + opportunity score
   - **Outcomes** — from desired outcomes question, refined to be measurable
   - **Edge Cases** — inferred from alternatives, pain points, and assumptions
   - **Verification** — derived from outcomes, stated as checkable criteria
   - **Deep Exploration** (deep mode only) — assumptions table, rebuilt direction, cross-pollination table + synthesis
3. Replace template placeholders:
   - `{{FEATURE_NAME}}` → generated feature name
   - `{{DATE}}` → current ISO date
   - `{{SLUG}}` → feature slug
4. Present the complete intentSpec to the user: "Here's the full intentSpec. Review each section — does this capture the intent?"
5. If approved → write to `.kiro/specs/<slug>/intent-spec.md`
6. If needs changes → adjust and re-present

## Post-Write: Workflow Integration

After writing the intentSpec, ask:

> "IntentSpec saved to `.kiro/specs/<slug>/intent-spec.md`. Continue into the spec workflow?"
>
> - **Yes — run `/kiro:spec-init`** to initialize the spec structure using this intentSpec as grounding
> - **No — done for now** — the intentSpec stands alone

If yes: respond with `/kiro:spec-init "<original description>"` — spec-init will detect the existing intent-spec.md and use it as grounding context.

## Common Mistakes

- **Rapid-firing AskUserQuestion** — Calling AskUserQuestion multiple times in one response. Claude sees a list of topics and tries to execute them all at once. STOP after each question. One AskUserQuestion per response, always.
- **Batching questions** — Asking 3 questions at once collapses the dialogue. Users give shallow answers. One at a time always.
- **Transcribing instead of synthesizing** — Don't parrot user words back. Elevate "it's annoying when the page loads slow" to "perceived performance degrades trust during critical decision moments."
- **Skipping the social dimension without thought** — Don't auto-skip question 5. Briefly consider whether the social job is relevant, then decide.
- **Jumping to solutions** — "We should add a dashboard" is solution design, not intent exploration. If the user proposes solutions, redirect: "What outcome would that dashboard achieve?"
- **Writing intentSpec before approval** — Always present the full draft inline first. Writing to disk before user says "yes" creates cleanup work.
- **Weak outcomes** — "Improve user experience" is not measurable. Push for specifics: "Reduce task completion from 6 clicks to 2."

## Reference Materials

The following references contain the methodologies, frameworks, and calibration examples that power each exploration phase:

- `references/jtbd-framework.md` — JTBD methodology, forces of progress, interview techniques, opportunity scoring, 4 calibration examples
- `references/first-principles-framework.md` — decomposition ladder, 4 assumption traps, cutting questions, integrated Stanford + MIT framework, 4 calibration examples
- `references/cross-pollination-framework.md` — industry inspiration library, principle extraction, adapt-don't-copy rule, 4 calibration examples
- `references/intent-engineering.md` — intentSpec definition and principles from pathmode.io
