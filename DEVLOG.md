# CMUcraft development journal

This journal records what actually works, wrong turns, and how problems were found.
Unverified behavior stays explicit. A completed script is not a completed campus.

## 2026-11-05 — Acknowledging the first version's problems

The first version had the campus outline and could be opened as a Minecraft save,
but it was far from the intended result. The clearest feedback was that a student
who studies here still needed the map to work out where they were.

This was more than missing windows. Heights, relationships between buildings,
colors and distinctive architecture all affect recognition. Extruding real
footprints and applying generic windows does not recreate campus. Version 0.2
remains a comparison, not a finished map. A daily commit-count target was also
explicitly dropped: accuracy matters more than splitting work into more commits.

### Position checks need an independent source

Checking whether exported cells stay inside their input OSM outlines detects
projection and rasterization errors, but cannot prove that OSM itself is correct.
County building outlines were added as an independent comparison. Some county
records combine connected buildings into one outline; a large centroid difference
is not a reason to move one building. The Wean complex needs this individual review.
The 41 named-building records are reference packets, not 41 accepted models.

### Heights need more than floor counts

Floor-based estimates were especially poor on sloped ground. An inventory entry
such as `4+5` cannot simply mean four floors. Earlier models oversimplified the
parts and ground levels of Wean and Purnell.

A USGS service repeatedly rate-limited downloads, leaving partial files that were
not used as valid measurements. After obtaining 2019–2020 data, complete 2024 data
was found through Pennsylvania PASDA. Two details mattered:

- Both horizontal coordinates and elevations use US survey feet. Elevations need
  their own `1200 / 3937` conversion; reprojection alone does not convert them.
- The files do not provide a separate classified building population. Unclassified
  points may include trees. They are surface candidates, not automatically roofs.

The earlier LAZ decoder could not read this compression version. Laszip decoded
it successfully. Sources, hashes, unit conversions and reproduction steps were kept.

### Hunt became a specific detailed specimen

Hunt was developed as a separate preview for inspection, not as evidence that the
whole campus had been rebuilt. Aerial roof imagery appeared displaced from the OSM
outline, but 2024 point-cloud building edges mostly agreed with it. The building
was not shifted to match the aerial roof: image displacement, eaves and ground
footprints need separate interpretation.

The first roof trial used per-cell measured heights and looked fragmented. It was
replaced with separate lower flat and upper hipped roof models. Held-out measurement
cells gave a median fit error of about 6.5 cm and a 95th percentile around 22.4 cm.
These are model-to-measurement differences, not an accuracy guarantee for the building.

Silver vertical members, recessed glass, horizontal frames and a bronze-brown
entrance canopy were added at 1/16-block detail. Blue nighttime lighting in photos
was not interpreted as blue wall material. Some frame and entrance dimensions remain
photo estimates. Facades are not fully reviewed, and the preview is an external
geometry render, not an in-game screenshot. Materials, collisions and reload behavior
still require client checks.

### Detailed geometry exposed a storage limit

Some detailed chunks exceeded the internal region-file capacity. The exporter now
uses Minecraft's external `.mcc` data streams with a stub in `.mca`. Regression tests
and exported-chunk read-back were added. Save transfers must retain sidecars.
Hunt's 64 exported chunks passed storage checks; this did not validate the mod runtime.

### The experimental-settings warning had a concrete cause

The warning was not hidden with another mod. The generator had used fixed biomes
for Nether/End and the incorrect noise-setting IDs `minecraft:the_nether` and
`minecraft:the_end`. Those settings should be `minecraft:nether` and `minecraft:end`,
with standard biome sources.

Minecraft 1.16.5's own parser reported unknown settings and Experimental status for
the old data. Corrected data parsed as Stable. This did not start a server or change
the server EULA. The repair script backs up files and only fixes this known defect.
The delivered preview uses corrected copies without overwriting previously played
saves. Remaining Forge-client warnings must be checked in the actual client.

### The preview gained Xaero maps

Xaero's Minimap 26.6.0, World Map 1.47.0 and required XaeroLib 1.7.3 were added using
Forge 1.16.5 files. Published hashes, declared dependency ranges and JAR integrity
were checked. Maps reveal areas as the player explores; an initially empty map is
not itself a fault. The legacy full-campus world and detailed Hunt preview have
separate names so one building's progress is not presented as a finished campus.

### Remaining work at that point

- Test the intended mod profile, Hunt rendering, collisions and save/reload.
- Resolve building heights, segmentation, colors and facade details individually.
- Check slopes, bridges and entrances together.
- Review the full campus in-game before describing a finished release.

An explicitly failed experiment is more useful here than an unsupported success claim.

## 2026-11-05 — Making the project easier to continue

The README was reorganized around the project goal, current preview and entry points
for playing, running tools and contributing. Legacy campus and Hunt remained distinct.
Contribution guidance and building-review, bug, participation and PR templates were
added. Photos, entrance locations, window patterns and reload checks do not require code.

Dense statements were reformatted. Forty Python files received module documentation,
and functions and complex operations received English explanations, especially axes,
metres/feet, array order, NBT packing and large-chunk storage. The Java checker gained
comments. JSON, images and worlds were explained in the file guide without altering
raw measurements to insert comments.

An AST comparison found no logic changes from formatting/documentation. Fifty-one
tests passed and the small map rebuilt. This established that cleanup preserved the
workflow, not that architectural quality improved. The repository was still private
at this stage; documentation did not itself provide public access or a server.

## 2026-11-05 — Explaining the motivation

The introduction was simplified: rebuilding CMU is fun, and might eventually help
new students explore campus. Navigation remains a goal, not a present guarantee.
The onboarding review removed the implication that everyone needs HMCL or Python.
Launcher-format support was separated from actual pack testing. This was a maintainer
review of likely friction, not a user study.

## 2026-11-05 — Publishing the repository

Contribution guidance became a direct collaboration process. Future Plans was grouped
around reconstruction, playing, collaboration and validation. Before publication,
common secret patterns and sensitive filenames in history, plus account/log/game-binary
paths in release packages, were checked without finding those issues. Commits used a
GitHub noreply address. This was a scoped check, not a complete security audit.
The owner authorized making the repository public and enabling Issues. Publication
did not imply acceptance of client behavior, multiplayer or architectural fidelity.

## 2026-11-05 — Builder contribution workflow

Added kit generation from an existing campus snapshot, a coordinate-preserving
whole-chunk staging path, claim/submission forms, English Builder instructions and
an explicit client-test matrix. The workflow keeps original saves and rejects stale
target chunks. Schematic compatibility for Chisels & Bits remains unverified.
The journal is now in English along with the other contributor documentation.
