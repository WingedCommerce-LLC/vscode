# Overseer Development Environment

This document provides instructions for setting up and using the Overseer development environment.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

## Quick Start

1. **Start the development environment:**
   ```bash
   cd overseer
   ./scripts/dev-start.sh
   ```

2. **Access the services:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

3. **Stop the environment:**
   ```bash
   ./scripts/dev-stop.sh
   ```

## Development Scripts

### Core Scripts
- `./scripts/dev-start.sh` - Start all services with health checks
- `./scripts/dev-stop.sh` - Stop all services and clean up
- `./scripts/dev-logs.sh` - View logs from all services
- `./scripts/dev-test.sh` - Run the test suite
- `./scripts/dev-reset.sh` - Reset database and restart services

### Database Management
- `python scripts/seed-dev-data.py` - Seed database with sample data

## Services

### API Service
- **Framework:** FastAPI with hot reload
- **Port:** 8000
- **Health Check:** http://localhost:8000/api/health
- **Documentation:** http://localhost:8000/docs

### PostgreSQL Database
- **Port:** 5432
- **Database:** overseer_dev
- **Username:** overseer
- **Password:** overseer_dev_password

### Redis Cache
- **Port:** 6379
- **No authentication required in development

## Sample Data

The development environment includes sample data:

### Users
- **Admin:** admin / admin123
- **Director:** director1 / director123
- **Member:** member1 / member123

### Teams
- AI Development Team
- Platform Engineering

### Agents
- CodeGen Agent (Active)
- QA Agent (Active)
- DevOps Agent (Inactive)

### Tasks
- Implement user authentication API (In Progress)
- Set up automated testing pipeline (Pending)
- Deploy development environment (Completed)

## Development Workflow

1. **Start services:** `./scripts/dev-start.sh`
2. **Make code changes** - Hot reload is enabled
3. **Run tests:** `./scripts/dev-test.sh`
4. **View logs:** `./scripts/dev-logs.sh`
5. **Reset if needed:** `./scripts/dev-reset.sh`

## Testing

Run the test suite:
```bash
./scripts/dev-test.sh
```

Current test coverage: 64% (18/18 authentication tests passing)

## Troubleshooting

### Services won't start
- Check Docker is running
- Ensure ports 8000, 5432, 6379 are available
- Run `./scripts/dev-reset.sh` to clean up

### Database connection issues
- Verify PostgreSQL container is healthy
- Check database credentials in .env
- Run database migrations: `alembic upgrade head`

### Hot reload not working
- Ensure volume mounts are correct in docker-compose.dev.yml
- Restart the API service: `docker-compose -f docker-compose.dev.yml restart api`

### Import errors
- Ensure all dependencies are installed in the container
- Check Python path configuration
- Rebuild containers if needed

## Environment Variables

Key environment variables for development:

```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://overseer:overseer_dev_password@postgres:5432/overseer_dev
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Next Steps

After completing Phase 1 (Foundation & Infrastructure), the next phase will focus on:
- Agent Management System (Phase 2)
- Real-time WebSocket communication
- Agent registration and lifecycle management
- Task distribution and queuing

For more information, see the memory-bank documentation.
