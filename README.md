# Assumption Excavator — verdict-suppressed novelty loop

**Date:** 2026-06-23
**Goal:** Direct an LLM agent to *mimic creativity* — produce non-obvious-but-real attack directions on a hard problem — instead of the mode-collapsed obvious answers default sampling returns.

---

## 0. The problem this is trying to solve

Ask a model "improve X" with no area → you get the corpus center (tracing, benchmark, debug, status line). Specify the area → you get exactly what you specified, zero novelty. Want: *"look for better things"* and have it be **creative** — find the side nobody looked at, on a fixed target.

Two failure poles observed across opus/gpt/sonnet (same prompt → near-identical ideas = mode collapse, proven):
- **over-secure** → regress to corpus prior → "that'll fail, it's been tried" → kills the embryo before it exists.
- **unleashed** → plausible-sounding novel garbage, hallucinated breaks.

Key reframe (the load-bearing idea): **novelty is not generated, it is *released* by breaking a load-bearing assumption.** Every real win (Avi's 47ms BGSAVE freeze; pushing below quant floors) came from the same move — the field's "floor" was a **shared contingent primitive** (everyone used the same tool, e.g. `PAGEMAP_SCAN` O(range)), NOT a fundamental limit. The model maps **both** "fundamental limit" and "shared contingent primitive" to *"dead"* — that conflation is the bug. The discriminator we want the model to run: **is this floor a physical law, or an assumption everyone happens to make?** Then attack the assumption.

Premature validation kills this. Validation is the FINAL triage, not mid-search. "Don't verdict for me — I need you for knowledge and thinking" is the manual version; the harness mechanizes that.

> Original seed was an RND/curiosity novelty sidecar (steer agent off repeated states). **Dead** — that operates in action/observation space (don't-repeat-tool-calls); the real problem is in *idea space* (don't-propose-the-obvious). RND on execution states is the wrong layer and redundant with `collide`.

---

## 1. The method (what actually works after 3 trials)

A recursive **assumption-excavation loop**, run inside `claude -p`, streamed and traced. The model is both move-generator and node-evaluator. Each node = a barrier. Classify barrier → fundamental ⇒ backtrack; contingent ⇒ attack the primitive → exposes next barrier → recurse.

Load-bearing disciplines (each added because a trial failed without it):
1. **Verdict ban.** Banned endpoints: "won't work / infeasible / that's the floor / can't go below X / accept the loss." A barrier is a node, never a conclusion. Prior failures = data about the OLD primitive, not the goal.
2. **Tag every claim** `[FACT]` (law or python number computed this run) / `[EMPIRICAL]` (measured in cited published work) / `[ASSUMED]` (intuition/extrapolation). **Only `[FACT]` can move a floor.**
3. **State the limitation in its strongest form BEFORE attacking** — no strawmen.
4. **Math is python-only**, and every script must explain *what* it computes and *why that is the correct thing to compute*. (Stops the model hand-waving numbers.)
5. **Choose the attack explicitly** — list candidates, pick one, say which assumption it removes and why it is the most load-bearing. State direction. Recurse.
6. **Defer validation** — mark leaps `[ASSUMED]`, keep descending.
7. **Fundamental only if a named inequality with units, verified in python.** Else it's a contingent primitive → attackable.
8. **Collide tool** (`/tmp/blend`) to escape the model's own truth-loop — samples real published domains structurally FAR from the problem; borrow a *mechanism* from a far field, build back.
9. **No product-search.** Web search is for principles/physics/math, NOT "what tool already solves this." If a solution existed, we wouldn't be running. Searching for it pulls back to the corpus center.

**The deliverable is a ranked TRIAGE LIST** — the `[ASSUMED]` leaps to prove/disprove, each with the concrete experiment that settles it — NOT a finished answer. The resolution is the user's to prove.

---

## 2. Test target (held fixed across all 3 trials)

Run a **230B-param MoE** (~10B active/token) locally on Avi's rig:
- 1× RTX 5090 laptop, 24 GB VRAM (~900 GB/s), ~60 GB DDR5 (~90 GB/s), NVMe ~7 GB/s. Budget ~84 GB.
- **>30 tok/s, <5% quality loss vs full model.**

**Why it's a real unsolved problem (not a toy):** ktransformers doesn't run on this system; GPTQ Q4 = 115 GB doesn't fit; only 10B active but spread unpredictably across CPU/GPU/disk per token + KV room needed. To *fit* you're forced to Q2-class, and Q2 loses >>5%. No built solution exists.

### The grounded wall (python-verified — `/tmp/floor.py`)
```
Footprint:  Q4=115GB  Q3=86GB  Q2.5=72GB  Q2=57GB   (budget 84GB, minus ~8 KV/OS → ~76 usable)
→ max ~2.64 bits/param to fit at all. Q2-class MANDATORY.
Quality:    <5% loss historically needs ~4 bits/param.
THE GAP:    storage allows ~2.6 bits, quality demands ~4. ~1.4-bit gap @ fixed 84GB = the whole problem.
Speed:      NOT binding. Q2 active (2.5GB/tok) from DDR5 = 36 tok/s; from VRAM = 360. If it FITS at quality, fast enough.
Asymmetry:  30B-dense Q4 = 15GB fits VRAM whole (why it runs); 230B Q4 = 115GB doesn't (why it doesn't).
```

---

## 3. The three trials

### Trial 1 — bare loop (sonnet, no tools)
Prompt: `/tmp/excavator_prompt.txt`. 6 nodes, no python, no search.
- **Worked:** verdict-suppression held (zero death-verdicts); precondition-recursion fired correctly at NODE 1 ("goal needs *computing* 10B active, not *storing* 230B resident").
- **Failed:** produced the **obvious answer wearing the loop's clothes** — every "attack" was published prior art it cited itself (expert-streaming/ktransformers, hot/cold cache, GPTQ/AWQ, SparseGPT). Mode-collapse reproduced *inside* the loop. **Verdict-ban ≠ novelty.** Also: arithmetic went soft (hallucinated "fits in 30-40GB", which is false).
- **Lesson:** the ATTACK step was unconstrained → filled with the most-probable (= published) break.

### Trial 2 — python-gated, anti-modal (sonnet + Bash)
Prompt: `/tmp/excavator_v2.txt`. Added: python-for-every-number, banned-approaches list, "attack must NOT be the literature default." 5 nodes.
- **Worked:** no fake "it fits" — every number traceable to a script. Stayed on the residual (1.4-bit gap). Banned-list held. **One genuine reframe** (NODE 3): *"bits/param" vs "bits/active-param weighted by routing frequency"* — the historical "4 bits for <5%" was measured on **dense** models where bits/param = bits/active; MoE breaks that identity (220B dormant per token). Right *kind* of thought.
- **Failed — new failure mode: python-as-credibility-prop.** It ran python on a **fabricated** loss curve (`loss = 5% × 2^(4−bits)`), and the fabrication *laundered* into looking verified. Worse than Trial 1's open hand-wave because it *looks* grounded. NODE 2 (amplify routing skew via temperature) was probably wrong — hand-waved the quality cost of forcing tokens off their true expert.
- **Lesson:** gating arithmetic ≠ gating the *model* behind the arithmetic. Need to tag the *formula* itself.

### Trial 3 — opus + websearch/fetch + collide + tagging (the keeper)
Prompt: `/tmp/excavator_v3.txt`. Added: opus; `[FACT]/[EMPIRICAL]/[ASSUMED]` tags (only `[FACT]` moves a floor); "state limitation before attacking"; explicit attack-choice; web for *principles only* (product-search banned); the **collide blend tool**; explicit "a prior assumption is itself suspect" (e.g. "quant hurts MoE more" might be backwards — maybe there's an unbuilt MoE-specific method). 35 turns, $2.47.

- **Self-corrected its own fabrications mid-run** (4×: "Wait — my gamma model was wrong", "WAIT - recheck my alpha=0.3 claim"). The Trial-2 laundering failure **did not survive** — tagging + "explain why the calculation is correct" forced re-derivation.
- **Web search did the right job:** pulled *physics* (singular-value decay of transformer weights, CKA between experts) and tagged adjacent work (D²-MoE, MoBiE 2026) as `[EMPIRICAL]` launch pads, **not** "the solution." Found no shippable tool (correct — none exists).
- **Found the actual MoE lever** trials 1-2 missed: 97% of params are experts; experts are **small perturbations of a shared base** → store **centroid + low-rank SVD delta + quantized residual**. The structural invariant the 30B-dense case lacks.

---

## 4. Trial-3 result (the current best)

**Attack:** kill the assumption *"bits/param must be uniform / fidelity = per-weight reconstruction."* Decompose each expert as `Expert_i = Centroid + Delta_i`, store the delta structurally.

**The scheme (python-backed):**
```
┌─────────────────────────────────────────────────────────────────┐
│ Component        │ Size    │ Precision │ Purpose                  │
├─────────────────────────────────────────────────────────────────┤
│ Shared params    │ 3.25 GB │ 4 bpp     │ Attention/embed/norm     │
│ Expert centroid  │ 1.31 GB │ 6 bpp     │ Shared expert base       │
│ 128× SVD factors │ 3.2 GB  │ 4 bpp     │ Top-r delta directions   │
│ 128× Quant resid │ 68.2 GB │ 2.44 bpp  │ Remaining delta          │
├─────────────────────────────────────────────────────────────────┤
│ TOTAL            │ 76.0 GB │ 2.64 avg  │                          │
└─────────────────────────────────────────────────────────────────┘
```
Per-token inference: shared in VRAM; router picks 2 experts; each = `x@centroid (cached) + x@U_i@V_i^T (50MB) + x@residual_i (533MB)`.
Bandwidth: 2×(50+533)=1.12 GB/token @ 90 GB/s = **81 tok/s** (bandwidth-bound; compute ~5000 tok/s, not the bottleneck).

**`[FACT]` floor moved:** 230B MoE → **76 GB at 2.64 effective bpp**, modeled <5% loss, **81 tok/s** — all numerically verified *against the model's error model*.

**`[FACT]` SVD-capture numbers (the lever's sensitivity):**
```
rank-6000 delta-variance captured:  alpha=0.3 → 75% ... alpha=0.5 → 93% ... alpha=0.6 → 97.6%
hybrid (SVD-256 + 2.5bpp residual), worst case alpha=0.5: needs quant-fidelity >74% → modeled 2.62-3.34% loss → PASS
```

**Claimed novelty (correctly scoped, not overclaimed):** D²-MoE already does centroid + SVD-delta. The asserted new part is the **quantized-residual third component** (makes the scheme robust regardless of α, the delta's singular-value decay) + the **rate-distortion argument**: the post-SVD residual is zero-mean / low dynamic range → quantizes far better than raw weights at the same bpp → closes the gap universally. **Not yet built. Testable.**

---

## 5. The honest caveat (the disease, one layer deeper)

The `[FACT]` floor is moved against a **modeled** error, NOT measured perplexity. It hinges on two numbers the run could only `[ASSUMED]`:
- **α** = singular-value decay rate of real expert deltas (found indirect evidence: CKA 0.3-0.6, "exponential SV decay" claim — never the real measurement).
- **delta_frac** = ‖delta‖/‖expert‖ (assumed centroid dominates, <20%).

So "works in ALL tested configurations" means *its own arithmetic over assumed α* — not a real model. Trial 3 **contained** the fabrication (tagged it, triaged it) instead of **eliminating** it. Better than Trial 2, not cured. The "BREAKTHROUGH" framing oversells what a python model of an assumed curve establishes.

---

## 6. Deliverable — the triage list (what to prove first)

1. **Measure α** (SV decay of real expert deltas, e.g. on Qwen3-235B / Mixtral) — settles pure-SVD vs hybrid choice. Experiment: SVD the per-layer delta matrices, plot σ_k.
2. **Measure delta_frac** (‖delta‖/‖expert‖) — settles whether centroid dominates (predicted <20%). Experiment: compute centroid, measure residual Frobenius norm ratio.
3. **End-to-end perplexity** of the full scheme vs FP16 baseline — ground truth beats all theory. The only thing that turns `[ASSUMED]` into `[FACT]`.

---

## 7. Method verdict + open problems for next iteration

**Works** for the asked task ("make it one major step more feasible, find the first problem and tackle it"): refused death-verdict across 35 turns, killed a real load-bearing assumption, grounded floor-claims in python, tagged the leaps, produced a ranked triage list.

What's carrying the method: **verdict-ban + state-limitation-first + explicit-attack-choice + tag-every-claim + python-with-why + only-[FACT]-moves-floor.** Collide is NOT yet earning its slot.

**Open problems:**
1. **Collide anchor-distance is wrong — too far.** Returned Alamo / graphql / quakec; model said "blend didn't give useful far-field domains" twice. The real escape came from the *reframe* ("experts are perturbations"), not collide. Needs a tighter band or a near-field mode anchored on the problem's *mechanism* not its *surface words*.
2. **Fabrication leak not closed, only tagged.** Need a hard rule: a floor cannot be called "moved" on a modeled curve at all — only "moved **pending measurement X**." `[FACT]` should require a real measurement or a named law, never a fitted/assumed formula.
3. **Truly-new part under-excavated.** It leaned on D²-MoE as a launch pad (good grounding) but the genuinely-new quantized-residual claim didn't get the same adversarial excavation the rest got. Next: turn the loop on the novel part itself.

---

## Appendix — files & repro

All under `~/projects/assumption-excavator/`:
- Floor grounding: `tools/floor.py`
- Prompts: `prompts/v1_bare.txt`, `prompts/v2_python_gated.txt`, `prompts/v3_opus_collide.txt`
- Collide blend tool: `tools/collide_blend.py` (problem-anchored wrapper over itch's `collide_sample.py`), launcher `tools/blend`
- Raw run logs: `runs/v1.jsonl`, `runs/v2.jsonl`, `runs/v3.jsonl`
- Tracer: `tools/trace.py <jsonl> [full|headers]`

Note: `tools/blend` hardcodes `/tmp/collide_blend.py` and the sxc venv
(`~/projects/splade-3-colbert-2/.venv/bin/python`). Edit `blend` to point at `tools/collide_blend.py`
before reuse. `tools/collide_blend.py` imports itch's `collide_sample.py` from `~/projects/itch`.
Requires itch's collide corpus at `~/.config/itch/collide/` (17320 embedded domains).

Run v3:
```
cat prompts/v3_opus_collide.txt | claude -p --output-format stream-json --verbose --model opus \
  --allowedTools "Bash WebSearch WebFetch" --permission-mode bypassPermissions > runs/v3.jsonl
```
Collide blend:
```
tools/blend "<problem anchor text>" <temp 0.6-0.9> <k>
```
