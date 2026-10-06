# From Prompt to Print: Attendee Guide


## Before you arrive

Bring a laptop with Chrome, a free Tinkercad account you have already signed into once ([tinkercad.com](https://www.tinkercad.com)), and a Claude account signed in at [claude.ai](https://claude.ai) with Code execution and file creation switched on under Settings > Capabilities (it is on by default; use the event credits or your own Pro plan). Bookmark the session repo: github.com/YOUR-HANDLE/prompt-to-print. No GitHub account, no printer, nothing to install.

## Build 1: your box in Tinkercad (10 min)

Everyone builds an open-top box; you pick what it holds and how big it is (pens, cables, earbuds, seed packets, 15 ml tubes, SD cards). Keep walls at 2 mm and nothing thinner than 1.2 mm.

1. Go to tinkercad.com, click Create, then 3D Design.
2. Drag a Box from Basic Shapes onto the workplane. Click a white handle and type your size, for example 80 wide, 60 deep, 30 tall (all millimeters).
3. Drag a second Box, click Hole in the inspector, and size it 4 mm smaller in width and depth and the same height (76 x 56 x 30 for the example).
4. Click the black cone above the hole box and set it to 2. That 2 mm gap becomes the floor.
5. Shift-click both boxes, press L, then click the two center dots so the hole sits centered inside the box.
6. Press Ctrl+G (Cmd+G on Mac). The hole is cut out and you have an open box.
7. Click Export (top right), choose .STL, and rename the download something like box_80x60x30.stl.

Behind? Download examples/box_80x60x30.stl from the repo and skip to Build 2. Stuck on a click? Ask Claude: "I'm in Tinkercad, how do I ___?"

## Build 2: Claude modifies the STL (12 min)

You pick one change from the menu; Claude writes and runs the code that makes it.

1. Open claude.ai, start a new chat, and attach your STL (paperclip, or drag it in).
2. Paste the starter prompt below and fill in the three blanks: what the box holds, its size, and the change you want.
3. Claude measures the box first, makes the change, checks it, and posts a download link. Download the new STL.
4. Not right? Reply with the tweak ("bigger holes", "two compartments, not six") and Claude re-runs.

| Change | Say something like |
| --- | --- |
| Sieve floor | a hex grid of 4 mm holes, 6 mm apart, with a 3 mm solid border |
| Compartments | 3 columns by 2 rows of dividers, same thickness as the walls |
| Your name or logo | emboss SEAN on the front wall, raised 1 mm |
| Rounded corners | round the four vertical edges with an 8 mm radius, inside and out |
| Lid | a drop-in lid as a separate STL with 0.3 mm clearance |
| Hanging slot | a keyhole slot in the back wall so it hangs on a screw |
| Your idea | describe it with numbers; Claude will say if it will not print |

If Claude says it cannot run code, turn on Code execution and file creation under Settings > Capabilities and try again.

## The starter prompt

Copy this into Claude with your STL attached. Replace the three [BLANKS].

```text
I built this part in Tinkercad and exported it as an STL. Units are millimeters. It is an open-top box that will hold [WHAT IT HOLDS], about [W x D x H] mm outside with 2 mm walls.

Change I want: [YOUR CHANGE FROM THE MENU, with numbers, e.g. "turn the floor into a sieve: a hex grid of 4 mm holes, 6 mm apart, with a 3 mm solid border"].

How to work:
1. Load the STL in Python with trimesh (pip install trimesh manifold3d shapely rtree mapbox_earcut if needed). Measure the outer size, wall thickness and floor thickness, and tell me what you found before changing anything.
2. Make the change with boolean operations using the manifold engine, computed from the measured geometry, not guessed coordinates. Keep the outer size and orientation unless I asked to change them.
3. Printability: no wall thinner than 1.2 mm, no hole smaller than 2 mm, and the result must be watertight. If my request breaks a rule, make the closest printable version and tell me what you changed.
4. Give me the new file as a download named [original-name]_[change].stl, plus a short before/after report: size, volume, triangle count, watertight check, and one sentence on what changed.

If a package will not install or a boolean fails, say so and rebuild the box from the measured dimensions in code instead of stopping.
```

## What done looks like

- [ ] A new .stl downloaded from Claude with your change in its name
- [ ] Claude's report says watertight: true and the size matches your box
- [ ] You can say it in one sentence for the 5:00 showcase: "An 80 x 60 x 30 box for SD cards, and Claude turned the floor into a sieve."

That file prints anywhere: a library makerspace, a friend's printer, or an online print service. To see it first, click Import in Tinkercad and drop it in.
