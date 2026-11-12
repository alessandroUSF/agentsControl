# Llama 3.1 Acceptable Use Policy — compliance assessment (DRAFT for the PI to review and adopt)

> **Note of 10 November 2026 (protocol v2.3).** This draft was written for protocol v2.2. Two parts are out of date. The author's own prompts are not used in this study (protocol v2.3, Section 15.2). And no statement about what the models will produce can be made before any answer is handled under the protocol: the sentences below that predict compliance are expectations, not findings. The PI writes the assessment of decision D3 from the licence text itself.

> Satisfies the protocol's requirement to record **who assessed** the Llama policy for harmful
> generations by Llama derivatives, and the **conclusion**. This is a good-faith assessment by
> the PI, **not legal advice**; for a binding determination, seek institutional/legal review.
> Assessed by: **[PI name]**, date **[date]**. Source: Llama 3.1 Acceptable Use Policy,
> retrieved 2026-11-09.

## 1. Scope
The Llama 3.1 Community License and its Acceptable Use Policy (AUP) bind Llama 3.1 **and its
derivatives**. In this study that is: **model 4** (Llama 3.1 8B, safety intact), **model 6**
(an abliterated Llama 3.1 derivative), and **model 20** (Dolphin 3, Llama-derived).

## 2. What the AUP says (relevant parts)
The AUP's "Prohibited Uses" bar using Llama to generate, among others: illegal/unlawful
activity or content; violence or terrorism; **guns and illegal weapons, including weapon
development**; illegal drugs and controlled substances; **self-harm** (incl. suicide);
harassment; child exploitation; and **malicious code / malware**. There is **no exemption for
research, red-teaming or safety evaluation**; the only related provisions are channels for
*reporting* risky content. So the AUP restricts the **act of generating** this content,
regardless of a research purpose.

## 3. What the study does with the Llama-derived models
Models 4, 6 and 20 receive the public benchmark harmful prompts (OR-Bench Toxic, XSTest
unsafe) and the author's own prompts. Model 4, with safety intact, refuses most prohibited
requests. **Models 6 and 20 have had refusal removed and will comply**, producing completions
that overlap AUP-prohibited categories (e.g. weapons, drugs, malware) when the benchmark
prompts fall there. These completions are generated **locally**, never published, shared only
through a gated researcher release, access-controlled, withheld when `uplift = yes` or in
hazard category S9, and deleted on the retention schedule. The author's **own** prompts already
exclude weapons, biology, chemistry and minors.

## 4. Honest assessment
- The study's **purpose** (measuring and improving judge/model safety behaviour) and its
  **safeguards** (non-distributive, local, access-controlled, uplift-withheld,
  retention-limited) substantially reduce real-world harm.
- But the AUP has **no research carve-out** and prohibits the **generation** itself. The
  safeguards therefore mitigate harm **without** bringing the generation into literal AUP
  compliance for the prohibited categories. The protocol already states that the study does
  **not** claim a research purpose exempts it from the licence/AUP.
- The tension is **concentrated in the safety-removed derivatives (6, 20)**, which are the
  ones that actually emit prohibited content; model 4 largely refuses.
- Conclusion: a **residual compliance tension exists**; it is not resolved by purpose or
  safeguards alone.

## 5. Mitigations in place
Own prompts exclude weapons/bio/chem/minors; benchmark prompts are public and sent verbatim;
generation is local; nothing is published; access is gated; uplift and S9 items are withheld
even from the gated release; raw data is deleted after the retention period.

## 6. Recommendations ([PI] to decide)
1. **Record** this assessment (assessor, date, conclusion) in the protocol and the ethics
   section.
2. **Disclose** the tension openly in the paper's ethics/limitations (not hide it behind
   "research purpose").
3. **Seek Meta's guidance / notify** via the AUP's reporting/researcher channel, documenting
   the contact — the cleanest path to defensibility.
4. **Institutional/legal review** of this specific use before the paid runs (I am not a
   lawyer; this is the item most worth a second opinion).
5. **Optional scope limit:** for models 6 and 20 specifically, consider excluding the hardest
   AUP categories (weapon development, malware, drug synthesis) from their prompt set — at the
   cost of comparability with the other respondents — or document why the full set is kept.

## 7. Decision ([PI])
- [ ] Proceed with safeguards + open disclosure + Meta notification, accepting the documented
  residual risk; **or**
- [ ] Restrict what models 6 and 20 are prompted with; **or**
- [ ] Pause the Llama-derivative runs pending institutional/legal review.
