# Future Plans

The aim is to turn the current experiments into a recognizable, explorable CMU campus that people can build on together. The full-campus preview and the detailed Hunt model are still separate. These plans describe the direction of the project, not a promised release schedule.

## Campus reconstruction

Replace the generic architecture in the original campus model with building-specific geometry. Improve proportions, materials, roof forms and the relationship between buildings and the surrounding terrain. Geographic sources and photographs should support these changes, with uncertainty recorded where the evidence is incomplete.

Bring reviewed models into a single world with a consistent coordinate system. Improve paths, entrances, elevation changes and connections between campus areas so the map makes sense from a player's perspective, not just from above.

## Playing and exploring

Verify installation across commonly used launchers and operating systems. Simplify the release downloads and document a tested setup that does not depend on one person's launcher configuration.

Complete client testing of the detailed geometry, including rendering, collisions and save/reload behavior. Navigation tools and a short campus introduction could eventually make the world useful to people who are new to CMU, once the layout and routes are reliable enough.

## Collaborative development

Building Kits and offline chunk staging provide a contribution path without Python
or Git. A local three-block C&B sample passed save/re-entry and integration into a
separate campus copy. Next, test a fresh pack installation, CUC world entry and a
real volunteer's submission. Larger builds and collisions still need testing;
C&B schematic-only delivery remains unavailable until its round trip is verified.

Test multiplayer synchronization and persistence before offering a shared building environment. A community server is a possibility, but hosting, maintenance and moderation have not been arranged.

## Tools and validation

Make the generation pipeline easier to extend beyond the current hard-coded examples. Strengthen placement checks, data provenance, release validation and reproducible builds while keeping the tools understandable to new contributors.

Add automated checks where they catch real failures, and complement them with documented visual and in-game reviews. Neither survey data nor a passing test suite is enough on its own to establish that the campus looks right.

## Longer term

Interior spaces, additional campus areas and more detailed environmental work can follow once the exterior world is coherent. Suggestions are welcome through issues and pull requests, especially when they help make the existing project easier to use or develop.

## First contributor round: Hunt and CUC

Fixed exterior trial packs and small tasks now support participation before a
whole-building commitment. Hunt starts with a window-and-fin proposal; CUC starts
with entrance/facade identification. One accepted-save coordinator per building
avoids conflicting whole-chunk submissions. Other building reference packets are
research inventory, not 41 simultaneous open assignments. Expand to more buildings
after this first round works well for contributors.
