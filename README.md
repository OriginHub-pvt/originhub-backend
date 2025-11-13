# OriginHub Backend

FastAPI backend for the OriginHub platform - a platform for idea generation and AI-powered chat.

## Features

- **Chat API**: AI-powered chat endpoint for user interactions
- **Ideas API**: Create and retrieve ideas with filtering and sorting
- **CORS Enabled**: Configured to work with Next.js frontend
- **Docker Support**: Complete Docker setup with PostgreSQL and Weaviate
- **In-Memory Storage**: Simple storage solution (database integration ready)

## Tech Stack

- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Relational database
- **Weaviate**: Vector database for semantic search
- **Docker**: Containerization
- **Uvicorn**: ASGI server

## Running the Application

The application can be run in **two ways**:

### Method 1: Docker (Recommended)

**Best for:** Production, consistency, easy setup with databases

#### Prerequisites

- Docker and Docker Compose installed
- `.env` file (copy from `.env.example`)

#### Setup

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Start all services (PostgreSQL, Weaviate, and API):**
   ```bash
   cd docker
   docker compose up -d
   ```
   
   **Note:** All Docker files are in the `docker/` directory. Run commands from there.

3. **View logs:**
   ```bash
   docker compose logs -f api
   ```

4. **Stop services:**
   ```bash
   docker compose down
   ```

**Services available:**
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Weaviate**: http://localhost:8080

### Method 2: Direct Uvicorn (Local Development)

**Best for:** Fast iteration, debugging, local development without Docker

#### Prerequisites

- Python 3.11+
- PostgreSQL and Weaviate running (via Docker or locally)

#### Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database connection details
   ```

4. **Start PostgreSQL and Weaviate (if not already running):**
   ```bash
   # Option A: Start only databases via Docker
   docker compose up -d postgres weaviate
   
   # Option B: Use local PostgreSQL and Weaviate installations
   ```

5. **Run the FastAPI application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

**API available at:** http://localhost:8000

### Comparison

| Feature | Docker | Direct Uvicorn |
|---------|--------|----------------|
| Setup Complexity | Easy (one command) | Requires manual DB setup |
| Database Included | ✅ Yes | ❌ Need separate setup |
| Hot Reload | ✅ Yes | ✅ Yes |
| Isolation | ✅ Full | ❌ Uses system Python |
| Production Ready | ✅ Yes | ⚠️ Need process manager |
| Best For | Production, Team Dev | Local Development, Debugging |

## Project Structure

```
originhub-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with CORS configuration
│   ├── models.py            # Pydantic data models
│   ├── routes/              # API route handlers
│   │   ├── __init__.py
│   │   ├── chat.py          # Chat endpoints
│   │   └── ideas.py         # Ideas endpoints
│   └── services/            # Business logic layer
│       ├── __init__.py
│       └── ideas_service.py # Ideas service
├── Dockerfile               # Docker configuration for API
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md
```

## API Endpoints

### Chat

- **POST** `/api/chat`
  - Request body: `{ "message": "user message here" }`
  - Response: `{ "success": true, "data": { "response": "AI response here" }, "message": "..." }`

### Ideas

- **GET** `/api/ideas`
  - Query parameters:
    - `search?` - Search query for filtering ideas
    - `tags?` - Comma-separated tags to filter by
    - `sort_by?` - Sort field (createdAt, title)
  - Response: `{ "success": true, "data": { "ideas": [...] }, "message": "..." }`

- **POST** `/api/ideas`
  - Request body:
    ```json
    {
      "title": "Idea Title",
      "description": "Description",
      "problem": "Problem statement",
      "solution": "Proposed solution",
      "marketSize": "Market size",
      "tags": ["tag1", "tag2"],
      "author": "Author Name"
    }
    ```
  - Response: `{ "success": true, "data": { "id": "..." }, "message": "Idea created successfully" }`

### Health Check

- **GET** `/` - Root endpoint
- **GET** `/health` - Health check endpoint

## Development Workflows

### Workflow 1: Full Docker Development

Run everything in Docker (databases + API):

```bash
# Start all services
docker compose up -d

# View API logs
docker compose logs -f api

# Make code changes (auto-reloads)
# Test at http://localhost:8000

# Stop everything
docker compose down
```

### Workflow 2: Hybrid Development (Recommended for Fast Iteration)

Run databases in Docker, but run API locally with uvicorn:

```bash
# Start only databases
docker compose up -d postgres weaviate

# Run API locally (faster iteration, better debugging)
uvicorn app.main:app --reload

# Make code changes (instant reload)
# Test at http://localhost:8000

# Stop databases when done
docker compose down
```

### Workflow 3: Pure Local Development

Run everything locally (requires local PostgreSQL and Weaviate):

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env to point to local databases

# Run API
uvicorn app.main:app --reload
```

### Docker Commands

**Important:** All Docker commands should be run from the `docker/` directory:

```bash
cd docker

# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f api
docker compose logs -f postgres
docker compose logs -f weaviate

# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# Rebuild after code changes
docker compose up -d --build

# Execute command in running container
docker compose exec api bash
```

### Viewing Data Files

When you run `docker compose up -d`, Docker automatically creates the `volumes/` directories and stores data there:

- **Weaviate data**: `docker/volumes/weaviate/` - All Weaviate database files are visible here
- **PostgreSQL data**: `docker/volumes/postgres/` - PostgreSQL data files

**Note:** The `volumes/` directories are created automatically by Docker Compose when you run `docker compose up -d`. You don't need to create them manually.

You can browse these directories to see the actual data files. When you add new ideas via the API, the Weaviate data files will be updated in `docker/volumes/weaviate/`.

## Database Setup

### PostgreSQL

PostgreSQL is automatically set up via Docker Compose. Connection details:

- **Host**: `postgres` (from within Docker) or `localhost` (from host)
- **Port**: `5432`
- **Database**: `originhub` (default)
- **User**: `originhub` (default)
- **Password**: `originhub123` (default - change in production!)

### Weaviate

Weaviate is automatically set up via Docker Compose. Access:

- **URL**: `http://weaviate:8080` (from within Docker) or `http://localhost:8080` (from host)
- **Authentication**: Anonymous access enabled (for development)

## Environment Variables

Key environment variables (see `.env.example` for full list):

- `API_PORT`: Port for the FastAPI application (default: 8000)
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name
- `WEAVIATE_URL`: Weaviate server URL
- `DATABASE_URL`: Full PostgreSQL connection string

## Response Format

All responses follow a consistent format:

**Success Response:**
```json
{
  "success": true,
  "data": {...},
  "message": "optional message"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Next Steps

Future enhancements planned:
- [ ] Database integration (PostgreSQL)
- [ ] Weaviate integration for semantic search
- [ ] Authentication and authorization
- [ ] Real AI integration for chat
- [ ] User management
- [ ] Idea voting and comments
- [ ] File uploads
- [ ] Advanced search and filtering

## License

MIT
