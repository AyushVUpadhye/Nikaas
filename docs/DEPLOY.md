# Deploy (AWS SAM, region ap-south-1)

## Live URLs

| What | URL |
|---|---|
| API | https://4kzez16ucj.execute-api.ap-south-1.amazonaws.com (try `/health`) |
| Website | http://nikaas-webbucket-hbkfctr0cw8s.s3-website.ap-south-1.amazonaws.com |

The API is `nikaas/api.py` as-is: same routes as local (`/health`, `/validate`, `/simulate`), CORS open.

## Redeploy the API

Needs Python 3.11 on `PATH` (SAM builds Linux packages for the `python3.11` runtime).

```bash
sam build
sam deploy
```

Settings (stack `nikaas`, region) are in `samconfig.toml`, so no prompts.

## Publish the website

```bash
aws s3 sync web/dist s3://nikaas-webbucket-hbkfctr0cw8s --delete
```

## Notes

- Bedrock is called in `us-east-1` (env var `BEDROCK_REGION`) until ap-south-1 Bedrock access is verified.
- First request after idle takes ~3 s (Lambda cold start); later ones are fast.
