> Historical planning notes. The current contribution process is in [CONTRIBUTING.md](../CONTRIBUTING.md), and the project direction is in [Future Plans](../ROADMAP.md).

# First-time contributor review

This is a maintainer's walkthrough of likely friction, not feedback collected from a user study. The intended visitor is a CMU student who likes the idea and might spend a little time helping. They may not know Python, GIS, Git, Forge or HMCL.

| Question a student might ask | Current friction | What changed now | Still worth doing |
| --- | --- | --- | --- |
| Why would I want to join? | The introduction sounded more like a survey pipeline than a fun campus project. | Lead with rebuilding CMU for fun and exploring together; campus orientation is a future goal. | Show an actual in-game walkthrough once validated. |
| Can I even see the project? | The repository and release assets are private. | State the access limit plainly. | Decide whether to make it public; this review does not change visibility. |
| Do I need a different launcher? | HMCL was presented as the only route. | Explain the required game environment, documented Prism format support and manual route. | Test a fresh install on more than one launcher and OS. |
| Which file do I download? | Preview, Workbench, worlds ZIP and source archive serve different purposes. | Recommend Preview for playing; explain worlds-only and calibration-only alternatives. | Reduce release-page choices or add a short illustrated install guide. |
| Is this the whole campus? | A detailed Hunt image can imply a detailed campus. | State that Hunt and the legacy campus are separate worlds. | Integrate accepted models into one coherent playable world. |
| Do I have to install Python just to look around? | Code setup takes up a lot of the README. | Explicitly separate playing, non-code feedback and programming. | Watch a first-time reader follow the instructions without coaching. |
| What can I finish in one sitting? | Many tasks, such as rebuilding Wean, are large and ambiguous. | Offer one Hunt observation as a concrete first contribution. | Open and maintain small, unclaimed issues with reference views and a clear endpoint. |
| I can build, but how do I submit a world? | Git handles code changes more naturally than binary saves. | Allow a small save contribution and explain coordinates and `.mcc` files. | Test a reliable export/import handoff; provide a small example submission. |
| Will I get useful feedback? | No response schedule or active contributor roster has been established. | Keep coordination in issues/PRs and make credit optional and explicit. | Set a realistic review cadence after there is capacity; do not promise one now. |
| Can we build together tonight? | There is no shared server, and multiplayer is untested. | Say so before someone installs the pack expecting a live session. | Verify two-client synchronization and save/reload before hosting anything. |

The best next validation is a small, real onboarding test: invite a willing student to find the correct download, open the intended world and submit one observation. Record where they stop. Launcher support should be based on those results rather than a growing list of untested launcher names.
