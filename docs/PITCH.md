# Nikaas — 3-minute pitch script
*Draft by 17:00 · Final by 06:00 · Mark who says each line*

---

## 0:00 – 0:15 · Problem  *(Bhumika)*

> "On the 4th of June 2025, 11 people died outside Chinnaswamy Stadium in Bengaluru.
> They were trying to leave through a single narrow gate.
> No one knew the crowd was about to crush — because no building in India has a tool
> that tells you in advance."

---

## 0:15 – 0:30 · Product name  *(Chirag)*

> "We built Nikaas — Hindi for 'exit'.
> Nikaas is a real-time evacuation simulator that tells you:
> how long your building takes to evacuate, where the dangerous bottlenecks are,
> and — new today — where the crowd will get dense enough to kill."

---

## 0:30 – 1:30 · Live demo  *(Chirag drives, Bhumika narrates)*

**Step 1 — Load the IIT KGP museum building**
> "This is the National Museum of Science and Technology at IIT Kharagpur — 507 people, 3 exits.
> Nikaas simulates their full evacuation in under a second."

**Step 2 — Play the animation**
> "Watch: orange is walking, red is queuing.
> Total evacuation: 145 seconds.  Bottleneck: corridor g820 to the VER exit, peak queue 104."

**Step 3 — Block the MAIN exit**
> "Now I close the main exit — a fire blocks it.
> Evacuation time jumps to 318 seconds.  The VER corridor hits 226 people queuing."

**Step 4 — Show Crowd mode**  *(if live by demo time)*
> "Crowd mode overlays density.  Red means above 4 people per square metre —
> that is the threshold at which crowd forces reach fatal levels, per G. Keith Still.
> You can see exactly which corridor becomes a crush hazard, and at what time."

---

## 1:30 – 1:45 · Validation  *(Chirag)*

> "We didn't guess these numbers.
> The SFPE Handbook of Fire Protection Engineering publishes a worked example —
> a real building, hand-calculated.  Our simulator reproduces it to within 0.05 seconds:
> 245.25 s versus 245.2 s.
> Same hydraulic model.  Same constants.  We just made it interactive."

---

## 1:45 – 2:15 · Wow number  *(Bhumika, from docs/RESULTS.md)*

> "On the lab block — 528 people, 3 exits —
> closing Stair A actually makes evacuation *faster*: from 301 seconds down to 284.
> That is counterintuitive, but it is what the hydraulic model predicts,
> and it is the kind of insight a fire safety engineer cannot get from a static floor plan."

---

## 2:15 – 2:45 · Crowd mode  *(Bhumika)*

> "Crowd mode adds a layer the existing tools miss entirely.
> You give us a building.  We tell you which corridor exceeds the crush threshold
> — 4 people per square metre — and at what time.
> For Chinnaswamy, our stadium model shows Gate South, the narrow metro-side gate,
> exceeds that threshold within the first 60 seconds of a panic evacuation.
> That is the gate that failed on June 4th."

---

## 2:45 – 3:00 · Close  *(Chirag)*

> "Nikaas is open source, runs in a browser, and calls a single API endpoint.
> Any fire safety consultant, any stadium operator, any college building can use it today.
> We are Nikaas — and we want to make sure no one dies because the exit was in the wrong place."

---

*Numbers to verify before final version:*
- *145.25 s, 301.25 s, 284.75 s — from docs/RESULTS.md ✓*
- *245.25 s vs 245.2 s — from nikaas/sim.py docstring ✓*
- *Stadium Gate South timing — run stadium_gates.json through /simulate before demo*
