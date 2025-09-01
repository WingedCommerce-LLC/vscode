# Overseer - AI Development Platform

Overseer is an AI-enabled director platform for development teams, built as a layer on top of VSCode.

## Project Structure

```
overseer/
├── api/                 # FastAPI backend services
│   └── main.py         # Main API application
├── frontend/           # Frontend application (React/Next.js)
├── agents/             # AI agent implementations
├── models/             # Data models and schemas
├── data/               # Data storage and processing
├── scripts/            # Utility scripts
├── tests/              # Test suites
├── docs/               # Documentation
├── config/             # Configuration files
├── requirements.txt    # Python dependencies
├── package.json        # Node.js dependencies
└── .env.template       # Environment variables template
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 22.18.0+ (matches VSCode project requirements)
- Docker (for development containers)

### Development Setup

1. **Using VSCode Dev Containers** (Recommended):
   - Open the project in VSCode
   - Select "Reopen in Container" when prompted
   - Choose the "Overseer" configuration
   - The post-create script will automatically set up the environment

2. **Manual Setup**:
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt

   # Install Node.js dependencies
   npm install

   # Copy environment template
   cp .env.template .env
   # Edit .env with your configuration
   ```

### Running the Application

#### API Server
```bash
# Development mode with auto-reload
cd overseer
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python api/main.py
```

#### Jupyter Lab (for AI development)
```bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

### Available Ports

- `3000`: Frontend Dev Server
- `8000`: API Server
- `8080`: Alternative Web Server
- `8888`: Jupyter Notebook
- `5432`: PostgreSQL
- `3306`: MySQL
- `6379`: Redis

## Development Workflow

### API Development
- Main API code is in `api/main.py`
- Add new endpoints and services in the `api/` directory
- Use FastAPI for REST API development
- Follow async/await patterns for better performance

### AI Agent Development
- Implement AI agents in the `agents/` directory
- Use the `models/` directory for data schemas
- Leverage Jupyter notebooks for experimentation

### Frontend Development
- Frontend code goes in the `frontend/` directory
- Use React/Next.js for the web interface
- Connect to the API server running on port 8000

### Testing
```bash
# Run Python tests
pytest

# Run with coverage
pytest --cov=overseer
```

### Code Quality
```bash
# Format code
black .

# Lint code
pylint overseer/

# Type checking
mypy overseer/
```

## Environment Variables

Copy `.env.template` to `.env` and configure:

- `OVERSEER_ENV`: Environment (development/production)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude integration

## Contributing

1. Create a feature branch from `overseer-dev`
2. Make your changes in the appropriate directory
3. Add tests for new functionality
4. Ensure code quality checks pass
5. Submit a pull request

## Architecture

Overseer is designed as a modular AI platform:

- **API Layer**: FastAPI-based REST API
- **AI Agents**: Pluggable AI agents for different tasks
- **Data Layer**: SQLAlchemy models with PostgreSQL
- **Cache Layer**: Redis for session and cache management
- **Frontend**: React-based web interface
- **Integration**: Deep integration with VSCode and development tools

## License

Proprietary - WingedCommerce LLC
