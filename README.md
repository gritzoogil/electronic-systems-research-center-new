## Getting Started

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Make sure you have `uv` installed first: [installation instructions here](https://docs.astral.sh/uv/getting-started/installation/).

### 1. Clone the repo
```bash
git clone https://github.com/electronic-systems-research-center/esrc-website-v2.git
cd esrc-website-v2
```

### 2. Install dependencies
```bash
uv sync
```
This creates a `.venv` and installs the exact dependency versions locked in `uv.lock` — no manual venv setup needed.

### 3. Set up environment variables
Copy the example env file and fill in your own values:
```bash
copy .env.example .env
```
You'll need:
- `POSTGRES_URL` — get this from the team's Vercel Postgres dashboard
- `FIREBASE_SERVICE_ACCOUNT` — ask the backend lead for this (never commit this file or its contents to git)

### 4. Run the app locally
```bash
uv run flask --app api.index run --debug
```
The site should now be running at `http://127.0.0.1:5000`.

### 5. Adding a new dependency
If you need a new package:
```bash
uv add package-name
```
Then commit the updated `pyproject.toml` and `uv.lock` so everyone stays in sync.

### 6. Database migrations
After pulling new changes, if models were updated:
```bash
uv run flask --app api.index db upgrade
```

---

**Notes:**
- Do not run `pip install` directly — always use `uv add` / `uv sync` so the lockfile stays accurate for everyone.
- `requirements.txt` exists only for Vercel's deployment build step. You don't need to touch it locally.
- If `uv sync` fails or behaves unexpectedly after pulling, try `uv sync --reinstall`.