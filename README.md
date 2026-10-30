# SE 480 - FastAPI Service

**Deployed Application:** https://se480-jonah-service.onrender.com

**Health Check:** https://se480-jonah-service.onrender.com/health

## How to Run It

1. Open this repository in GitHub Codespaces.
2. Wait for the development container to finish building.
3. Open a terminal and run:

   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

4. Open the forwarded port 8000 in your browser.
5. Visit `/` to see the greeting and `/health` to check the service status.

To run the automated tests:

```bash
python -m pytest -q
```

## What's in the Repo

- `app/main.py` — FastAPI application and API routes.
- `.devcontainer/` — Configuration for the GitHub Codespaces development environment.
- `.github/workflows/ci.yml` — GitHub Actions workflow for automated testing.
- `requirements.txt` — Python dependencies.
- `Dockerfile` — Configuration used to deploy the application to Render.
- `README.md` — Project setup and usage instructions.

## Help Received

I followed the course handout and used the provided template to complete the lab. I also used ChatGPT when I had questions about the setup process and troubleshooting.

## AI Tools Used

I used ChatGPT as a step-by-step guide to better understand the lab instructions and troubleshoot a few issues. I also used it to help organize and write this README. The application code and CI workflow came from the course template, and I ran and verified the tests myself.
