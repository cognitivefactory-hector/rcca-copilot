# Whiteboard Drill — RCCA Copilot (design-stage)

> Rehearsal for the recorded whiteboard session. **The push** is me playing tough reviewer; **Defense** is the position that survives; **⚠ Your move** is what only you can answer once you've built/measured it. Fold the survivors into `DECISIONS.md`, then record.
> Scope: design-stage. Re-run after **M3** (grounded agent) with a real "insufficient-evidence" case to show.

## Q1 — "This is just a prompt wrapped around an LLM with a nice form. Where's the engineering?"
**The push:** You wrote a system prompt and called it a product.
**Defense (survives):** The LLM is the smallest part. The engineering is the **grounding + citation layer** (every cause cites retrieved evidence or is marked insufficient), the **typed 8D schema** the UI gates on, **tool-use retrieval** so the model fetches rather than recalls, and the **sign-off state machine** (`Drafted → Edited → Approved`). The model drafts; the system decides what's allowed to advance.
**⚠ Your move:** Point at the state machine + grounding tests as the substance.

## Q2 — "If the engineer reviews every section anyway, what did you save? Maybe it's net slower."
**The push:** Human-in-the-loop everywhere = no time saved.
**Defense (survives):** It saves the *drafting and structuring* — the blank-page hours of assembling the 8D, pulling the relevant trends, and writing consistent narrative — not the *deciding*. Review-and-edit is far faster than author-from-scratch, and every RCCA comes out audit-consistent regardless of who's on shift.
**⚠ Your move:** Be honest where it does **not** save time (a novel failure mode the model has no evidence for) — naming the limit is credibility.

## Q3 (the killer) — "The LLM hallucinates a perfect-sounding root cause. A tired engineer rubber-stamps it. You built a liability."
**The push:** Your tool will get a bad CAPA approved.
**Defense (survives):** This is the risk I designed against. Every candidate cause must **cite specific evidence or be labeled "insufficient evidence"** — the model is structurally barred from asserting an uncited root cause as confirmed. The UI makes the engineer approve **the evidence, not the prose**; low-confidence items are flagged; nothing advances unapproved. I deliberately rejected the auto-file version because an unsigned machine conclusion is exactly the liability you describe.
**⚠ Your move:** Demo the adversarial fixture — an NC with no supporting evidence yields "insufficient evidence," **not** a fabricated cause. That single behavior is the whole defense.

## Q4 — "How does this pass NADCAP? Auditors distrust black boxes."
**The push:** An auditor will reject AI-generated findings.
**Defense (survives):** It's built for traceability: every cause links to its evidence, there's an **audit trail of what the agent proposed vs. what the engineer changed**, and a human approver of record. It's a *drafting aid* that makes the human's reasoning more visible, not less — which is what an auditor actually wants.
**⚠ Your move:** You've sat through audits — name the specific thing an auditor checks that this trail satisfies.

## Q5 — "You tested on synthetic NCs you wrote. Real ones are messier, the data dirtier."
**The push:** Why believe it generalizes?
**Defense (survives):** Synthetic proves the *mechanism* (grounding, gating, structure). I authored NCs with a known planted root cause precisely so I can check whether the agent finds it or correctly says "insufficient." First real-data validation: run it on closed historical NCs and compare its draft to the actual signed CAPA.
**⚠ Your move:** Note what's hardest in real NCs (free-text travelers, missing data) from experience.

## Q6 — "Who is legally responsible when a corrective action fails — you, the tool, or the engineer?"
**The push:** Liability is a landmine.
**Defense (survives):** The engineer who signs. The sign-off gate exists exactly to keep accountability human — the tool assists, the qualified person dispositions. That's why I refused autonomy: not a limitation, a requirement.

## Verdict — SDRC after the drill
- **Holds:** the human-as-decider decision; the confident-wrong-cause risk and its mitigations; accountability framing.
- **Sharpen:** lead with **Q3** and the insufficient-evidence demo; be honest on the time-saving limit (Q2); land the NADCAP traceability point (Q4) with a specific auditor concern.
- **Land this line in the room:** *"The agent drafts and cites; the engineer decides and signs — and the model is structurally unable to assert a root cause it can't back with evidence."*
