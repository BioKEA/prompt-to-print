# Starter prompt

Paste this into a new chat at claude.ai **with your STL attached**. Replace the three `[BLANKS]`.
Full instructions are in [attendee-guide.md](attendee-guide.md).

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

## Menu of changes (pick one, add numbers)

| Change | Say something like |
| --- | --- |
| Sieve floor | a hex grid of 4 mm holes, 6 mm apart, with a 3 mm solid border |
| Compartments | 3 columns by 2 rows of dividers, same thickness as the walls |
| Your name or logo | emboss SEAN on the front wall, raised 1 mm |
| Rounded corners | round the four vertical edges with an 8 mm radius, inside and out |
| Lid | a drop-in lid as a separate STL with 0.3 mm clearance |
| Hanging slot | a keyhole slot in the back wall so it hangs on a screw |
| Your idea | describe it with numbers; Claude will say if it will not print |

## Follow-up prompts that work

- "Make the holes 5 mm and keep everything else."
- "Import this back into Tinkercad showed a gap at the corner. Check the mesh for non-manifold edges and repair it."
- "Give me a second STL of just the lid, plug side up, ready to print."
- "Is this printable without supports if I print it floor-down? Explain in two sentences."
