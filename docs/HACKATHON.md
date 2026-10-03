# NeuraVac — Physical AI Track

Project: NeuraVac. Household robots should understand the semantics and outcomes of physical tasks instead of assuming coverage equals cleaning.

Nebius: the implemented runtime calls Nebius Token Factory's HTTPS chat-completions API through `NebiusClient`. NVIDIA: account-verified NVIDIA Nemotron provides structured high-level semantic/mission decisions. There is no onboard language model; the Pi is CPU-only. Optional physical vision reasoning requires an explicitly configured and verified endpoint.

Physical AI loop: camera → semantic world model → reasoning → navigation → physical cleaning → fresh visual verification → retry/replan. Cloud reasoning supplies semantic judgments and priorities; edge perception supplies floor observations; deterministic robotics supplies geometry and safety. Neither model can bypass local safety.

The [official rules](https://nebiusglobalaihackathon.devpost.com/rules) require a working Nebius-backed application using an NVIDIA open-source model, public source, licensing, setup instructions and a public video≤3minutes. Physical AI entries need at least a minute of real hardware operation, or key modules if the project has no hardware. NeuraVac targets hardware, so include genuine robot footage. Reconfirm the current submission page before submitting.

## Evidence checklist

- [ ] Publish this repository and confirm LICENSE and clone/setup work in a fresh checkout.
- [ ] Provide real validated FloorMess weights/dataset license and calibrated hardware.
- [ ] Run an actual Nebius/Nemotron mission; save redacted request IDs, model ID, latency and validated decisions in mission history.
- [ ] Show dashboard cloud status changing during real requests. Offline mode is not evidence of cloud use.
- [ ] Film≥1minute of the real robot moving, avoiding a cable, cleaning and observing the outcome.
- [ ] Include before/after evidence, a retry and dynamic replanning; keep final public video≤3minutes.
- [ ] Fill genuine tooling feedback in HACKATHON_FEEDBACK.md.
- [ ] Run source secret audit and review video frames, logs, recording files and environment exposure.
- [ ] Link the exact NVIDIA model card/license, Nebius runtime configuration, public repository and demo video in submission.

No genuine cloud/hardware/hackathon feedback evidence has been fabricated. The deterministic simulator is development evidence, not a physical demonstration.
