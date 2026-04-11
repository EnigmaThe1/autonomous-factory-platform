# Runtime and Deployment

## Initial deployment target
- local-first Docker Compose deployment
- frontend container
- backend API container
- controller/worker container
- Postgres container
- optional Redis container

## Local developer mode
- backend and worker can run directly for debugging
- frontend can run in dev mode with hot reload
- adapters connect to local backend URL

## Future deployment
- remote hosted control plane
- remote or local workspace runners
- multi-worker queue-driven scaling
- enterprise deployment profiles
