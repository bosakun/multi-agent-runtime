# Synthetic usability self-audit

This is a checklist of interface properties verified against artificial preview pages. It is not a user study and does not establish usability with actual reviewers.

| Question a new Reviewer should answer | UI response |
|---|---|
| What stage is this? | Stage badge, plain-language stage heading, and `Case n / total` position appear first. |
| What should I do now? | The top task card states purpose, allowed material, comparison, response question, and material not to inspect. |
| What should I compare? | Baseline evidence/facts and observed stage record have separate labeled panels; desktop uses two columns, mobile stacks them. |
| What does a label mean? | Each available choice displays a Japanese explanation first and the unchanged canonical value beneath it. |
| Where is the original? | Japanese text is expanded by default; an English-original disclosure is directly beneath each translated passage. |
| How do I move and see progress? | Previous/next buttons, case position, progress bar, and index-level case list are provided. |
| How do I record a reason? | A note field accompanies every stage judgment; `unclear` requires a note. The reviewer selects the displayed supporting prose rather than typing sentence IDs. |
| How do I save? | Draft autosaves locally when the browser permits it; an explicit JSON download exports the existing v3 ballot shape. |
| Does this answer the study question by itself? | No. The page says it displays saved records and does not ask the Reviewer to infer model thought or internal evidence use. |

Remaining usability limitation: R1/R2 require several linked Registry objects. The guided form exposes those schema objects in separate labeled sections, but a human pilot is still needed to learn whether their Japanese wording and order are sufficiently clear. No Reviewer has been asked to validate this page.

v2.1 stage-screen audit: a synthetic S1 preview was rendered in headless Edge
and visually inspected. The fact and actual text are side by side; the main
screen does not require learning Worker/Registry/support-set terminology.
Node executes all five artificial stage screens to check one annotation unit,
plain choices, evidence selection and hidden coordinator metadata. This is
mechanical/self inspection, not an actual novice-user usability study.
