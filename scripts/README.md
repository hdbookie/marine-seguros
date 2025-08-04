# Docker Scripts

## Available Scripts

### docker-dev.sh
Run the application in development mode with live code reloading:
```bash
./scripts/docker-dev.sh
```
- Mounts code for hot reload
- Uses local file storage
- Perfect for development

### docker-prod.sh
Run the application in production mode with persistent volumes:
```bash
./scripts/docker-prod.sh
```
- Uses Docker volumes for persistence
- Simulates Railway production environment
- No code mounting

### docker-rebuild.sh
Rebuild Docker images from scratch:
```bash
./scripts/docker-rebuild.sh
```
- Forces rebuild of all images
- Useful when dependencies change
- Clears Docker cache