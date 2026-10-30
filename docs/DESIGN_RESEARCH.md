# Website design: research method (from the team playbook)

Owner: Bhumika. Goal: a site judges remember in the first 10 seconds, that does not look like a template.
Look rules for the product view are in `docs/VISUAL_STYLE.md`; this file is how to research and build the site around it.

## 1. Vibe discovery (15 minutes, before any UI code)
Answer these four in `design/VIBE.md`, then derive colours, type and layout from the answers:
1. What real-world place or object is this brand? (e.g. an architect's white scale model; a fire-safety control room)
2. What ONE emotion in the first 3 seconds? (e.g. calm control, "we've got this")
3. Which TWO unexpected influences collide? (e.g. architectural drawings x airport wayfinding signs)
4. What must it NEVER be mistaken for? (e.g. a game, a generic dashboard template)

Avoid the generic defaults: purple gradients, Inter/Roboto everywhere, stock icon sets, bento grids.

## 2. Pick references (save screenshots into `design/refs/`, many galleries load by script)
Copy patterns (layout, spacing, hierarchy, motion), never logos, copy or paid assets.
- Whole sites: godly.website, landdding.com, minimal.gallery, maxibestof.one, seesaw.website, a1.gallery, recent.design, on.design, inspora.design
- Polished product sites: linear.app, vercel.com, stripe.com, raycast.com, wisprflow.ai
- Sections: supahero.io (hero), navbar.gallery, cta.gallery, footer.design, 404s.design, detail.design (small details), 60fps.design (mobile motion), scrolltide.co (scroll effects)
- Assets (check licence first): iconly.design, encyclopedia.iconography.co (icons), backgrounds.supply, fontinlogo.com (which fonts brands use)

## 3. Design system in one file: `web/src/theme.css`
- Every colour, font, radius and shadow as a CSS variable, with a 5-line rule comment at the top.
- One accent colour for the single primary action; other colours only mean state
  (walking orange, queuing red, stairs blue, route green, fire red - same as the 3D view).
- A display font for one statement per page, a UI font, a mono font for ids and numbers.
- Hairlines and floating cards, not boxes. No component library.

## 4. Build in rounds, one improvement per round
theme → motion (CSS only, off under `prefers-reduced-motion`) → landing page → mobile → loading / empty / error states → polish (404, toasts).

Landing page (the judges' first 10 seconds): hero with the real product screenshot, the original
floor-plan photo next to its digital twin, a stats row with **our real numbers from `docs/RESULTS.md`**
(e.g. "validated against SFPE Example 1: 245.25 s vs 245.2 s"), three features, FAQ, call to action
("Try it: block a stair").

## 5. Review after every round
Screenshots at **1440, 1024 and 400 px** wide. List everything broken, cramped, misaligned,
low-contrast or generic; fix; repeat. No horizontal scroll at any width.

## 6. Must-haves for judging
- `?demo=1` plays the whole story with no backend and no login.
- A live page where judges break it themselves: tap a stair to block it, watch the re-plan.
- "Beat Nikaas": the judge assigns exits by hand and compares the time.
