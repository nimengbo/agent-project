# Deployment

This project is prepared for a single ECS host with Docker Compose.

## Server prerequisites

- Open inbound port 80 in the ECS security group.
- Install Docker and Docker Compose plugin.
- Clone this repository on the server.

## First deploy

```bash
cp .env.example .env
docker compose up -d --build
```

Open:

```text
http://SERVER_IP/
```

The frontend is served by Nginx. Requests under `/api` and `/health` are proxied to the FastAPI backend container.

## Check status

```bash
docker compose ps
curl -fsS http://127.0.0.1/health
```

## Logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f qdrant
```

## Update deploy

```bash
git pull
docker compose up -d --build
```

## Model config

After deployment, open the app and configure the model provider in the UI. The backend stores it in the `backend_runtime` Docker volume at `/app/runtime/model_config.json`.

Do not commit real API keys into `.env` or source files.
