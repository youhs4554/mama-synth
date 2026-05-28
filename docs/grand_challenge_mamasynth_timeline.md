# Crawled Page: 
            
    Timeline & Rules - The MAMA-SYNTH Challenge - Grand Challenge

            
                
            
        
- **Source URL:** [https://mamasynth.grand-challenge.org/timeline/](https://mamasynth.grand-challenge.org/timeline/)

---

### **Competition Timeline**[¶](#competition-timeline "Permanent link")

#### **Challenge schedule**[¶](#challenge-schedule "Permanent link")

The MAMA-SYNTH 2026 challenge is organized in sequential phases to support method development, validation, and final ranking under a standardized evaluation framework.

* **May 8, 2026** — Validation phase opens
* **June 25, 2026** — Test phase opens
* **July 10, 2026** — Last submission deadline
* **August 1, 2026** — Official results release
* **September 27, 2026** — Winners announcement at the **Deep-Breath Workshop (MICCAI 2026)**

#### **Important notes**[¶](#important-notes "Permanent link")

Please monitor the challenge page regularly for updates regarding:

* submission instructions,
* evaluation details,
* leaderboard policies,
* final ranking announcements,
* and workshop presentation information.

---

### **Rules**[¶](#rules "Permanent link")

#### **General participation rules**[¶](#general-participation-rules "Permanent link")

ENTRY INTO THIS CHALLENGE CONSTITUTES YOUR ACCEPTANCE OF THE OFFICIAL RULES AND POLICIES OF THE MAMA-SYNTH 2026 CHALLENGE.

Every participant must register for a valid **Grand Challenge** account and join the challenge in order to access the submission system and participate in the official evaluation.

#### **Eligible methods**[¶](#eligible-methods "Permanent link")

Participants are invited to submit methods for **virtual post-contrast breast MRI synthesis** from **pre-contrast T1-weighted MRI**.

At this stage, submissions will be evaluated according to the official challenge procedure described on the dedicated submission and evaluation pages.

#### **Use of training data and pre-trained models**[¶](#use-of-training-data-and-pre-trained-models "Permanent link")

Participants must train their algorithms using:

* the data provided by the challenge, and/or
* additional **publicly available datasets** that are accessible to all participants before the submission deadline.

Any external data, pre-trained model, or publicly available initialization used in the submitted method should be clearly documented in the method description.

Note that “Publicly available” will refer to datasets and pretrained models released before the start of the validation phase, i.e. by **May 7, 2026 23:59 CET**.

Specifically:

* ✅ **Allowed:** Using the challenge data for model development
* ✅ **Allowed:** Using publicly available external datasets
* ✅ **Allowed:** Using publicly available pre-trained weights or open-source implementations
* ❌ **Not allowed:** Using private datasets
* ❌ **Not allowed:** Using private model weights or non-public training resources unavailable to other participants

Participants are free to use publicly released models, including the evaluation models provided by the organizers, as components during the training and evaluation of their models. (e.g. as a composite training objective, say, providing perceptual, segmentation, or radiomics-based losses). Methods where such models serve as one signal among several, in service of improving synthesis quality, are permitted.

Methods where the primary training objective is to maximize scores on the evaluation pipeline, rather than to improve the fidelity of the synthesized images, are considered metric gaming and are grounds for disqualification.

Note that evaluation models used in the final test phase will be updated and may differ from the released checkpoints; participants should not assume checkpoint stability across validation and test phases.

The top 3 ranked teams will be required to submit their full training code for organizer review prior to final ranking confirmation.

#### **One team, one submission identity**[¶](#one-team-one-submission-identity "Permanent link")

Each participant or team should participate using a single challenge identity on Grand Challenge.

If team-level participation rules are further specified, they will be announced on this page.

### **Awards**[¶](#awards "Permanent link")

The official results and winning teams will be announced publicly after completion of the challenge evaluation.

Selected top teams may be invited to present their approach at the **Deep-Breath Workshop (MICCAI 2026)**.

Top 3 teams based on the official challenge evaluation criteria will be recognized and awarded the following:

1st Position: €500

2nd Position: €250

3rd Position: €150

Additionally, best paper award will be awarded to the team whose paper demonstrates high scientific quality, methodological novelty, and potential impact, independent of leaderboard ranking. Challenge papers submitted to the Deep-Breath Workshop will be considered.

Best Paper Award: €300

#### **Code and reproducibility**[¶](#code-and-reproducibility "Permanent link")

Participant code is encouraged to be open-access, but this is not a strict exclusion criteria. Particularly, code submission is mandatory for top-3 ranked teams as a condition for being awarded the challenge awards and co-authorship in the joint publication. The code must include training scripts, inference scripts, and documentation of external data/pretrained models.

#### **Follow-up publication**[¶](#follow-up-publication "Permanent link")

The organizers plan to prepare a challenge report or follow-up publication summarizing the benchmark, participating methods, and final results. Top-performing teams may be invited to contribute, subject to organizer policy and journal or workshop requirements.