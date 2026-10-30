# Nikaas — visual style for the build (decided 30 Oct, before 09:30)

Target: the two evacuation reference renders (white architectural model + orange people + fire,
and white walls with green escape routes). NOT the cartoon school-sim look.

## The look in one line
A white architectural scale model of the real floor, lit like a studio photo, with realistic
human figures and glowing escape routes. Colour is spent only on people, routes and danger.

## Rules
| Element | Do | Don't |
|---|---|---|
| Walls | Matte white, slight panel grid texture, crisp edges, wall height ~1.4 m cutaway | Wood, bright colours, cartoon outlines |
| Floor | Dark charcoal (ref 1) or warm concrete (ref 2); room floors one shade lighter | Checkerboard, tiles with colour |
| Furniture | White/light-grey low-detail desks, chairs, shelves; a few plants as the only green | Coloured props, toys, stickers |
| People | Human silhouettes (head, torso, two legs, arms), walking animation by leg swing; **orange** = queuing / at risk, **dark grey** = moving normally, fade out on exit | Capsules, chibi/cartoon faces, name bubbles |
| Routes | Glowing **green** ribbon on the floor from each room to its assigned exit, with arrow chevrons moving along it | Thin lines, dashed debug lines |
| Exits | Green EXIT box above the door; blue marker = exit point | — |
| Fire / blocked | Flame particles + orange heat rings spreading on the floor; red crossed target on the blocked stair | Cartoon flame emoji |
| Lighting | Soft shadows (PCF), ambient-occlusion feel, slight fog at the edges | Flat lighting |
| Camera | **Perspective** camera, ~35° down, slow orbit/dolly; tilt-shift blur optional | Orthographic "game" camera for the hero view |
| UI | Same white cards as the concept video (clock, dot-grid, legend, event log, scenario bar), Times for numbers, Segoe/Inter for labels | Game HUD, coins, emojis |

## Build note (rules)
- Write all of this fresh after 09:30 inside the new repo. Do not copy `video/scenes3d.html`
  (the concept mockup) into the project: pre-written code is not allowed.
- Order: core simulator + tests first, 2D view second, this 3D look after H12.
- Free assets only if the licence allows (e.g. CC0 low-poly human from Poly Pizza / Quaternius); credit in README.
