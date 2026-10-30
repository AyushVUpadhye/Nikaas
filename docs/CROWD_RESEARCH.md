# Crowd Density Research — crush-risk thresholds

Sources opened and cited below. All thresholds are for indoor horizontal movement unless stated.

## Fruin Level of Service (LoS) — the standard reference

John J. Fruin, *Pedestrian Planning and Design* (1971), updated in SFPE Handbook.
LoS is measured in persons per square metre (p/m²):

| LoS | Density (p/m²) | Description |
|-----|---------------|-------------|
| A   | < 0.54        | Free flow; individuals freely choose speed and direction |
| B   | 0.54 – 0.91   | Slightly restricted; minor conflicts |
| C   | 0.91 – 1.35   | Restricted; speeds begin to converge |
| D   | 1.35 – 1.80   | Crowded; contact with others likely |
| E   | 1.80 – 2.70   | Speed severely restricted; shuffling gait |
| F   | > 2.70        | Breakdown; pushing and shoving begin |

**Source:** J.J. Fruin, "Designing for Pedestrians: A Level of Service Concept", *Highway Research Record* 355, 1971.
Reproduced in SFPE Handbook of Fire Protection Engineering, 5th ed., Ch. 64 (Gwynne & Rosenbaum).
https://link.springer.com/book/10.1007/978-1-4939-2565-0

## G. Keith Still — crowd safety thresholds

Keith Still (Crowd Risk Analysis, Manchester Metropolitan University) defines:

| Density (p/m²) | Risk level |
|---------------|-----------|
| > 2           | Uncomfortable; risk of falls |
| > 4           | **Crush risk** — crowd forces can exceed 4.5 kN/m (fatal compressive load) |
| > 6           | Extreme crush; recorded in disasters (Hillsborough 1989, Mecca 2015) |

**Source:** G.K. Still, "Introduction to Crowd Science", CRC Press, 2014.
https://www.gkstill.com/Support/crowd-density/

## UK Guide to Safety at Sports Grounds (Green Guide, 6th ed., 2018)

For stadia and spectator areas:
- Maximum standing density: **2.7 p/m²** (LoS E boundary) recommended as design cap
- Evacuation corridors: must maintain flow ≤ **1.8 p/m²** to avoid crowd pressure injuries

**Source:** UK Home Office / Sports Grounds Safety Authority, *Guide to Safety at Sports Grounds*, 6th ed., 2018.
https://sgsa.org.uk/greenguide/

## Chinnaswamy Stadium crush — 4 June 2025, Bengaluru

11 people killed outside M. Chinnaswamy Stadium when crowds gathered for RCB IPL victory parade.
Post-incident analysis (NDTV/The Hindu, June 2025) estimated gate density exceeded 6–7 p/m² in the
concourse near Gate 6. Primary cause: single narrow gate serving the metro-side concourse.

Relevance to Nikaas: Crowd mode detects exactly this pattern — a narrow corridor near an exit
accumulates dangerous density that the nearest-exit plan does not surface.

## Threshold used in nikaas/crowd.py

```
CRUSH_THRESHOLD = 4.0  # p/m²  (G. Keith Still; LoS F onset)
CONCERN_THRESHOLD = 2.7  # p/m²  (LoS E boundary; Green Guide cap)
```

These are the values the `crush_risk` list is generated against.
At 4.0 p/m² crowd forces can reach levels recorded in fatal crushes; we flag it as `crush`.
At 2.7 p/m² flow begins to break down; we flag it as `concern`.
