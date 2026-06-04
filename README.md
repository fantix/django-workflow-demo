# Django + Vercel Workflow Demo

A minimal example of a **Django** application running locally that triggers and monitors **Python workflows** executing on Vercel.

## Architecture

```
Local machine                        Vercel
+-----------------+                  +---------------------------+
| Django server   |  -- REST API --> | Workflow Server            |
| (localhost:8123)|                  |                           |
|                 |  -- Queue ----> | workflow service (Python)  |
|   Start workflow|                  |   greet() -> say_hello()  |
|   Poll status   |                  |   sleep(2s)               |
+-----------------+                  +---------------------------+
```

- **Django** handles the web UI and API endpoints; it runs entirely on your machine.
- **Workflow code** (`services/workflow/workflow.py`) is deployed to Vercel as a job service. Steps and sleeps execute durably on Vercel's infrastructure.
- Django communicates with Vercel via the Python SDK (`vercel` package) using a Vercel auth token.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [Vercel CLI](https://vercel.com/docs/cli) (`npm i -g vercel`)

## Project Structure

```
django-workflow-demo/
  demo/                    # Django project
    settings.py
    urls.py
    views.py               # API: /workflow/start/, /workflow/status/<id>/
    templates/index.html    # Web UI
  services/workflow/        # Deployed to Vercel
    workflow.py             # Workflow + step definitions
    pyproject.toml          # Python deps for Vercel build
    uv.lock
  vercel.json               # Vercel service configuration
  pyproject.toml            # Local Django deps
  manage.py
```

## Local Development (without deploying to Vercel)

You can test the full workflow loop locally using `vercel dev` to emulate the Vercel runtime.

### 1. Install dependencies

```bash
cd django-workflow-demo
uv sync
```

### 2. Start the Vercel dev server

In one terminal:

```bash
vercel dev
```

This starts the workflow service locally at `http://localhost:3000`.

### 3. Start Django

In another terminal:

```bash
PYTHONPATH=services/workflow \
VERCEL_QUEUE_BASE_URL=http://localhost:3000/_svc/_queues \
WORKFLOW_TARGET_WORLD=local \
VERCEL_QUEUE_TOKEN=vc-dev-token \
uv run python manage.py runserver 8123
```

### 4. Test

Visit http://localhost:8123/ or:

```bash
curl "http://localhost:8123/workflow/start/?name=Local"
```

The workflow runs entirely on your machine — Django talks to the local Vercel dev server instead of the cloud.

---

## Production Setup (deploying to Vercel)

### 1. Install dependencies

```bash
cd django-workflow-demo
uv sync
```

### 2. Deploy the workflow service to Vercel

Link the project to your Vercel team (first time only):

```bash
vercel link --scope <your-team>
```

Deploy to production:

```bash
vercel deploy --prod
```

Note the deployment ID from the output (e.g. `dpl_XXXX`). You'll also need the project ID and team ID, which you can find in `.vercel/project.json` after linking.

### 3. Set environment variables

```bash
export WORKFLOW_TARGET_WORLD=vercel
export WORKFLOW_VERCEL_AUTH_TOKEN=<your-vercel-token>
export VERCEL_DEPLOYMENT_ID=<deployment-id-from-step-2>
export WORKFLOW_VERCEL_PROJECT=<project-id>
export WORKFLOW_VERCEL_TEAM=<team-id>
```

You can get a token from https://vercel.com/account/tokens.

### 4. Start Django

```bash
PYTHONPATH=services/workflow uv run python manage.py runserver 8123
```

The `PYTHONPATH` ensures Django imports `workflow` from the same module path as Vercel, so workflow IDs match.

### 5. Open the demo

Visit http://localhost:8123/ in your browser. Enter a name and click "Start Workflow". The page polls for status updates automatically.

Or use the API directly:

```bash
# Start a workflow
curl "http://localhost:8123/workflow/start/?name=World"
# {"run_id": "wrun_...", "name": "World"}

# Check status
curl "http://localhost:8123/workflow/status/wrun_.../"
# {"run_id": "wrun_...", "status": "completed", "output": "Hello, World! Hope you are doing well!"}
```

## How It Works

1. **`POST /workflow/start/`** creates a `run_created` event via the Vercel Workflow API and enqueues a message to trigger the workflow service on Vercel.

2. **Vercel** picks up the queue message and executes `greet()` in `services/workflow/workflow.py`:
   - Runs the `say_hello` step
   - Sleeps for 2 seconds (durable timer)
   - Returns the greeting string

3. **`GET /workflow/status/<run_id>/`** polls the run status. Once completed, it returns the output.

## Notes

- Each `vercel deploy --prod` produces a new deployment ID. Update `VERCEL_DEPLOYMENT_ID` accordingly, or the queue messages won't route to the correct deployment.
