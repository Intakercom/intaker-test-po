# Candidate guide: how this exercise works

Welcome, and thank you for your time. This page explains what we expect from you at each step. It is short on instructions and long on expectations, because how you get there is part of what we are looking at.

**Intake Desk** is a small, working repair-workshop app built only for this hiring process. It is fictional: no real customers, no real data, nothing deployed. You will explore it, reason about it, and propose improvements. You are **not** expected to write production code at any point.

The process has three phases.

| Phase | What it is | When | Roughly how long |
|---|---|---|---|
| **Phase 0** | Set up and get to know the product, on your own | Before the live session | 1–2 hours, at your pace |
| **Phase 1** | Live interview: product discussion plus live exercises | Scheduled with us | 80 minutes |
| **Phase 2** | Take-home assignment, if Phase 1 goes well | Sent to you afterwards | 3 hours maximum |

---

## Phase 0 — Get set up and get familiar

This happens before we meet. Nobody watches you do it, and setup itself is not scored. What we expect by the end of it:

**You have an AI coding assistant running on this repository.** We recommend VS Code + Claude Code. If you need access, the recruiter can provide a temporary Claude account; just ask. But you can use any comparable tool that you are familiar with. 

**You have the app running locally and you have clicked around it.** Get the code from the repository and build it locally to test the product. 

**You understand the product from two sides.** From the UI: what a coordinator and a technician can actually do, what the different statuses mean, what happens when you switch profiles. From the code: roughly where things live and how a change travels from the screen to the database.

**Reset the product to the baseline state before interview.** Make sure that before the interview, you have the product in the baseline state as it comes from the repository. 

Two things worth knowing now. **The app is intentionally incomplete, not broken** — some capabilities the briefs talk about simply do not exist yet, and that gap is the exercise. And **the code is the source of truth**: if a document and the code disagree, the code wins.

---

## Phase 1 — The live session

An 80-minute call, split roughly in half.

**The first half is a product conversation.** We talk about how you work as a product owner: how you define requirements, how you decide what not to build, how you handle incomplete information and disagreement with stakeholders. Some of it will be about your past work, some about this product.

**The second half is live, hands-on work.** You share your screen and work in this repository with your AI assistant while we watch. We will ask **specific questions about the product and its behavior** — things like what state a particular repair is really in, who can see it, what a given status does and does not guarantee. We are not testing recall; we expect you to find the answers during the call, using the UI and the code, with AI helping you. Then we will ask you to shape a small feature proposal from what you found.

What we expect from you across both halves:

- **Investigate, do not assume.** Back a claim with what you saw in the UI or a file and function in the code.
- **Say what you are unsure about.** "I think X, I have not verified it" is a strong answer. A confident wrong answer is not.
- **Separate the layers** — what the app does today, what the scenario tells you, what you are inferring, and what you are proposing.
- **Drive your AI assistant well.** Ask it good questions, and check what it tells you. Accepting a plausible but wrong AI answer is the most common way this exercise goes badly.
- **Make product decisions and defend them.** Scope something small, say what you are leaving out, and say why.
- **Think out loud.** We are interested in your reasoning as well as in your decision-making.

You may ask us clarifying questions at any point, including "where should I look?". That is normal product work, not a hint you failed to earn.

What we are **not** assessing: typing speed, memorized Python syntax, visual polish, or whether you implement anything. Do not spend the session writing code.

---

## Phase 2 — The take-home

If Phase 1 goes well, we invite you to the take-home. You keep the same repository and the same product; we send the brief and the deliverables then. It is capped at **three hours**, and we mean the cap — we would rather see a coherent, deliberately scoped piece of work than an exhaustive one.

Expect it to ask for a written product decision, AI-assisted wireframes, and an engineering handoff grounded in real references to this codebase. Same standard as the live session: evidence over assertion, clear scope, honest assumptions.

---

## Using AI

Using AI is expected, not merely allowed. Use it for exploring the code, investigating behavior, drafting, wireframing, and anything else that helps. We will ask you where it helped and where you checked its work — that conversation is part of the assessment, so keep a light note of it.

The one rule: **you own every claim you make.** If AI tells you something about this product, verify it before you rely on it.