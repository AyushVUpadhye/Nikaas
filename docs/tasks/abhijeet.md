# Abhijeet — all AWS, photo → graph

Part of Nikaas (AfterHours 1.0). Read first: `docs/CONTRACT.md` (shared data format) and `docs/TASKS.md` (team rules, checkpoints).

1. **AWS on every laptop (now):** IAM user per member, `aws configure` (region `ap-south-1`), billing alarm ₹500,
   Bedrock model access (Amazon Nova, vision-capable). Done when `aws sts get-caller-identity` works on all 4 laptops.
2. **Deploy skeleton (by 15:30):** `template.yaml` (AWS SAM): HTTP API → Lambda (Python 3.11, `nikaas.api` via
   Mangum) + S3 bucket for the web build. `sam build && sam deploy`. Done when `/health` answers on the public URL.
3. **Photo → graph (by 19:00):** `nikaas/vision.py`: send the map photo to Bedrock (`converse` with an image),
   ask for JSON in the `docs/CONTRACT.md` format, validate with `nikaas.building.load`. Compare against Chirag's
   hand-made `data/cse_labs.json`; write the differences to `runs/vision_check.md`.
4. **Upload flow (by 23:00):** `POST /vision` endpoint + S3 for photos; deploy everything; frontend on S3.
5. **Give Bhumika the live URL** as soon as it works (for the README and the pitch).

Fallback: if Bedrock misreads the map, the hand-made JSON + editor is the demo and vision is shown as "assisted".

## Notes from Chirag (build lead)
Newest at the bottom. Check this section after every `git pull`.
- **11:47** — The Lambda entry point is ready: set the SAM `Handler` to `nikaas.api.handler` (Mangum wraps the FastAPI app; `mangum` is in `requirements.txt`). Runtime `python3.11`.
- **11:47** — Chirag's laptop has no AWS credentials yet. Set it up first so he can test deploys too.
- **11:58** — Run every vision result through `nikaas.building.validate(d)` (or `POST /validate`); it returns readable problems like `room staff cannot reach any exit`. Put them in `runs/vision_check.md`.
- **12:00** — No public floor plan of the CSE Labs exists online; if anyone can photograph a real posted evacuation map, test vision on it and compare with `data/lab_block.json`'s format.
- **12:05** — Test vision on `data/maps/iit_kgp_nmst_block_b.jpg` (real photographed panel) and compare with the hand-digitised `data/iit_kgp_museum.json`. Same photo, so the comparison is fair.
- **12:25** — README, pitch and demo video moved to Bhumika so you can focus on AWS and vision. Send her the live URL when it is up.
- **12:23** — Reviewed your deploy: `/health`, `/validate` and `/simulate` work on the live URL and match local results (IIT KGP 145.25 s). Please **redeploy now**: commit 400ffc1 adds gzip, which cuts `/simulate` from ~1.5 MB to under 0.1 MB on the wire (live is still sending 1.5 MB uncompressed). Also: `samconfig.toml` and `docs/DEPLOY.md` are good, thanks.
- **12:33** — Reviewed vision: excellent and honest (`runs/vision_check.md`: Nova Pro 14/15 rooms, median 3.3 m, tests pass). Next most valuable: **exits**. It finds 1 of 3, which alone explains 388.5 s vs 145.25 s. Try a second, focused call that asks only for doors to the outside / stairs / steps with their positions, then merge. Re-run `scripts/vision_check.py` and report rooms + exits found. I will show your result in the website as the photo-to-twin step with an editor to fix exits.
- **12:51** — Your Nova Pro graph is now in the website as "Read from the photo (Amazon Nova Pro)" next to the hand-digitised building, simulated live on your API (388.5 s, same as `runs/vision_check.md`). When the exits pass improves, rerun `scripts/vision_check.py` and copy the new graph to `web/public/data/vision_nova_pro.json`.
