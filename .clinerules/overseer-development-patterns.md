## Brief overview
Development patterns and preferences specific to the Overseer AI Development Platform project, focusing on authentication systems, database architecture, and dev container setup based on Session 1.2 implementation.

## Development workflow
- Always use proper dev container configuration with Docker Compose for services like PostgreSQL and Redis
- Prefer PostgreSQL over SQLite for development to match production environment
- Use Alembic for database migrations with proper model imports and environment variable configuration
- Implement comprehensive testing before moving to next development phase
- Use task progress tracking with detailed checklists to monitor implementation status
- Fix import issues systematically by converting relative imports to absolute imports when needed

## Database and backend architecture
- Use UUID primary keys stored as PostgreSQL UUID type (not strings)
- Implement timezone-aware timestamps with proper PostgreSQL functions (func.now())
- Structure models with proper relationships and foreign key constraints
- Use SQLAlchemy ORM with connection pooling and proper session management
- Organize code into logical modules: models/, auth/, api/, alembic/
- Use environment variables for database connections with secure defaults

## Authentication system patterns
- Implement JWT with both access tokens (30 min) and refresh tokens (7 days)
- Use bcrypt for password hashing with proper salt handling
- Create role-based access control with hierarchical permissions (ADMIN > DIRECTOR > MEMBER > AGENT)
- Structure authentication endpoints: register, login, logout, refresh, /me, verify-token
- Use FastAPI dependencies for authentication middleware and role checking
- Implement comprehensive Pydantic models for request/response validation

## API development practices
- Use FastAPI with automatic OpenAPI documentation
- Implement proper CORS and security middleware
- Structure API with routers and proper error handling
- Use dependency injection for database sessions and authentication
- Include health check endpoints and proper logging
- Forward appropriate ports in dev container (3000, 8000, 5432, 6379)

## Error handling and debugging
- When encountering database connection issues, check service availability first
- For import errors, systematically convert relative imports to absolute imports
- Use proper environment variable loading and validation
- Implement comprehensive error handling with meaningful HTTP status codes
- Test endpoints with curl commands to validate functionality

## Dev container best practices
- Use multi-service Docker Compose with health checks
- Include PostgreSQL client and Redis tools in development environment
- Set up post-create scripts for automatic dependency installation and database setup
- Configure proper environment variables in dev container configuration
- Use proper volume mounting and network configuration for service communication
