# Stack (one line per layer)

| Layer | Choice | Why |
|---|---|---|
| Simulator / optimiser | Python 3.11, SciPy `linprog` | Fast to write and test; the LP needs no extra solver install |
| API | FastAPI | Typed request bodies, one command to run locally, wraps for Lambda with Mangum |
| Frontend | Vite + React + TypeScript, three.js, one theme file | Full design control; 2D first, 3D on top |
| Vision | Amazon Bedrock (vision-capable model) | Organiser's platform; only used to read the photo |
| Infra | AWS SAM: API Gateway → Lambda, S3 (site + photos), CloudWatch | Whole cloud setup in one template, `sam deploy` |
| Tests | pytest | Every claim has a test |
| Demo video | Playwright + ffmpeg | Reproducible, no editor |
| 3D view | three.js 0.160.0, vendored in `web/src/vendor/three` (MIT, licence file included) | The npm registry was unreachable on the venue network; vendoring keeps the build offline-safe |
