"""Stage the Lambda source in build/lambda/: just the nikaas package and its runtime requirements.
SAM packages whatever CodeUri points at, and the repo root (web/, data/, node_modules) is far over Lambda's
250 MB limit. Run before `sam build`:

    python scripts/build_lambda.py && sam build && sam deploy
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "lambda"
DEV_ONLY = {"pytest", "uvicorn", "httpx"}  # local tools; Lambda runs through Mangum


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(ROOT / "nikaas", OUT / "nikaas", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    reqs = []
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        name = line.split("#")[0].strip().split("<")[0].split(">")[0].split("=")[0].split("[")[0].strip().lower()
        if name and name not in DEV_ONLY:
            reqs.append(line.strip())
    (OUT / "requirements.txt").write_text("\n".join(reqs) + "\n", encoding="utf-8")
    print(f"staged {OUT.relative_to(ROOT).as_posix()}: nikaas/ + {len(reqs)} requirements ({', '.join(reqs)})")


if __name__ == "__main__":
    main()
