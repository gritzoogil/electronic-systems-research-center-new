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
- `FIREBASE_SERVICE_ACCOUNT_PATH` — local path to your downloaded Firebase service account JSON
- `FIREBASE_SERVICE_ACCOUNT` — deployment-only single-line JSON value for the same service account
- `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, and `FIREBASE_PROJECT_ID` — the web client config for Firebase email/password sign-in

### 4. Run the app locally
```bash
uv run flask --app api.index run --debug
```
The site should now be running at `http://127.0.0.1:5000`.

### Firebase setup
Firebase email/password authentication is a client-side sign-in provider. The backend does not receive user passwords. Instead, the frontend signs the user in with Firebase and sends the Firebase ID token to Flask as:
```http
Authorization: Bearer <firebase-id-token>
```

The backend verifies that token with the Firebase Admin SDK before allowing protected requests.

For local development, put the downloaded service account JSON somewhere ignored by git, for example:
```bash
mkdir -p .firebase
mv ~/Downloads/your-service-account.json .firebase/service-account.json
```

Then set this in `.env`:
```bash
FIREBASE_SERVICE_ACCOUNT_PATH=.firebase/service-account.json
```

For Vercel or another hosted environment, set `FIREBASE_SERVICE_ACCOUNT` to the full service account JSON as a single-line environment variable instead of uploading the file.

Once Firebase is configured, you can test backend token verification with:
```bash
curl -H "Authorization: Bearer <firebase-id-token>" http://127.0.0.1:5000/admin/me
```

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
