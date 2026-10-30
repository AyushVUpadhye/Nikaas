# Deploy (AWS SAM, region ap-south-1)

## Live URLs

| What | URL |
|---|---|
| Website | http://nikaas-webbucket-hbkfctr0cw8s.s3-website.ap-south-1.amazonaws.com |
| API | https://4kzez16ucj.execute-api.ap-south-1.amazonaws.com (try `/health`) |

The API is `nikaas/api.py` as-is: same routes as local, CORS open, gzip on.

| Route | What |
|---|---|
| `GET /health` | `{"ok": true, "routes": [...]}` |
| `POST /validate` | see `docs/CONTRACT.md` |
| `POST /simulate` | see `docs/CONTRACT.md` |
| `POST /optimise` | best exit plan + lower bound (`nikaas/optimise.py`). ~2 s museum, ~8 s lab block. |
| `POST /beat` | time a hand-made `plan` against the optimiser ("Beat Nikaas"). ~3 s. |
| `POST /qa` | graph quality score and warnings (`nikaas/graph_qa.py`). <1 s. |
| `POST /vision` | photo of a floor plan → building graph (+ `quality`). ~20 s. |

Last checked live on 30 Oct 14:15 IST: all routes 200, museum `/simulate` 145.25 s, `/optimise` 124.0 s.

### `POST /vision`

Body: `{"image": "<base64 PNG/JPEG/WebP, a data: URL is fine>", "width_m": 80, "name": "optional"}`.
`width_m` is the building's real east-west length (photos have no scale). Max photo 3.75 MB.

Returns `{"ok", "id", "building", "problems", "photo_key"}`. `building` is in the contract format and can go
straight to `/simulate` when `ok` is true. `building.vision` says what was guessed:
`exits_added` (from the exits-only pass) and `auto_links` (links the model left out, added to the nearest
walkway). **Exits are the weak part (see `runs/vision_check.md`): let the user confirm them before simulating.**

Errors: 400 not base64, 413 too big, 415 not an image, 422 bad `width_m`, 502 Bedrock failed.
Photos and results are kept 30 days in the private photo bucket (`photos/<id>.<ext>`, `results/<id>.json`).

```js
const image = await new Promise(r => { const f = new FileReader(); f.onload = () => r(f.result); f.readAsDataURL(file) })
const res = await fetch(`${API}/vision`, { method: 'POST', headers: { 'content-type': 'application/json' },
  body: JSON.stringify({ image, width_m: 80 }) }).then(r => r.json())
```

## Redeploy the API

Needs Python 3.11 on `PATH` (SAM builds Linux packages for the `python3.11` runtime).

```bash
python scripts/build_lambda.py
sam build
sam deploy
```

`scripts/build_lambda.py` stages only `nikaas/` and the runtime requirements in `build/lambda/` (the template's
`CodeUri`). Packaging the repo root pulls in `web/node_modules` and `data/` and goes over Lambda's 250 MB limit.

numpy/scipy (used by `/optimise`) are capped in `requirements.txt` (numpy < 2.3, scipy < 1.16): newer versions
only ship Linux wheels for glibc 2.28+, and the python3.11 Lambda image has glibc 2.26. Do not lift the cap
without moving the runtime to python3.12+. Never deploy a package without scipy: `nikaas/api.py` imports the
optimiser at start-up, so every route would fail.

Settings (stack `nikaas`, region) are in `samconfig.toml`, so no prompts.

## Publish the website

```bash
cd web && npm ci && npm run build && cd ..
aws s3 sync web/dist s3://nikaas-webbucket-hbkfctr0cw8s --delete --exclude index.html --cache-control "public,max-age=300"
aws s3 cp web/dist/index.html s3://nikaas-webbucket-hbkfctr0cw8s/index.html --cache-control no-cache --content-type text/html
```

The API URL comes from `web/.env.production` at build time.

## Notes

- Bedrock is called in `us-east-1` (env var `BEDROCK_REGION`, model `BEDROCK_MODEL`, default Nova Pro) until
  ap-south-1 Bedrock access is verified.
- First request after idle takes ~3 s (Lambda cold start); later ones are fast.
- The API is rate-limited to 10 requests/s (bursts of 20) in `template.yaml`, so a public URL cannot burn the
  AWS credits through `/vision` (Bedrock). Raise it there if a demo needs more.
- API Gateway stops waiting after 30 s; `/vision` runs its two Bedrock calls in parallel to stay well under that.
