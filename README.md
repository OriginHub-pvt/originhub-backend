# OriginHub Backend

FastAPI backend for the OriginHub platform - a platform for idea generation and AI-powered chat.

## Features

- **Chat API**: AI-powered chat endpoint for user interactions
- **Ideas API**: Full CRUD operations for ideas with filtering, sorting, and ownership verification
- **User Management**: Clerk webhook integration for user synchronization
- **Authentication**: Header-based authentication with ownership checks
- **CORS Enabled**: Configured to work with Next.js frontend
- **Docker Support**: Complete Docker setup with PostgreSQL and Weaviate
- **PostgreSQL Integration**: Full database integration with SQLAlchemy ORM

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

| Feature           | Docker               | Direct Uvicorn               |
| ----------------- | -------------------- | ---------------------------- |
| Setup Complexity  | Easy (one command)   | Requires manual DB setup     |
| Database Included | ✅ Yes               | ❌ Need separate setup       |
| Hot Reload        | ✅ Yes               | ✅ Yes                       |
| Isolation         | ✅ Full              | ❌ Uses system Python        |
| Production Ready  | ✅ Yes               | ⚠️ Need process manager      |
| Best For          | Production, Team Dev | Local Development, Debugging |

## Project Structure

```
originhub-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with CORS configuration
│   ├── database.py          # Database connection and session management
│   ├── dependencies.py     # Authentication dependencies
│   ├── models/              # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── idea.py          # Idea model
│   │   └── user.py           # User model
│   ├── routes/              # API route handlers
│   │   ├── __init__.py
│   │   ├── chat.py          # Chat endpoints
│   │   ├── ideas.py         # Ideas endpoints (CRUD)
│   │   └── webhooks.py       # Clerk webhook endpoints
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── idea.py
│   │   └── user.py
│   └── services/            # Business logic layer
│       ├── __init__.py
│       ├── ideas_service.py # Ideas service
│       ├── weaviate_client.py
│       └── weaviate_service.py
├── docker/                  # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── volumes/              # Database volumes
├── migrations/              # Alembic database migrations
│   ├── env.py
│   └── versions/
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md
```

## API Endpoints

### Chat

- **POST** `/chat`
  - Request body: `{ "message": "user message here" }`
  - Response: `{ "success": true, "data": { "response": "AI response here" }, "message": "..." }`

### Ideas

- **GET** `/ideas`

  - Query parameters:
    - `search?` - Search query for filtering ideas (searches title, description, problem, solution)
    - `tags?` - Comma-separated tags to filter by
    - `sort_by?` - Sort field (createdAt, title)
  - Response: `{ "success": true, "data": { "ideas": [...] }, "message": "..." }`
  - Each idea includes: `id`, `title`, `description`, `problem`, `solution`, `marketSize`, `tags`, `author`, `createdAt`, `upvotes`, `views`, `status`, `user_id`, `link`

- **GET** `/ideas/{idea_id}`

  - Get a single idea by ID
  - Response: `{ "success": true, "data": { ...idea object... }, "message": "Idea retrieved successfully" }`
  - Returns 404 if idea not found

- **POST** `/ideas`

  - Create a new idea
  - Request body:
    ```json
    {
      "title": "Idea Title",
      "description": "Description",
      "problem": "Problem statement",
      "solution": "Proposed solution",
      "marketSize": "Market size",
      "tags": ["tag1", "tag2"],
      "author": "Author Name",
      "link": "https://example.com" // optional
    }
    ```
  - Response: `{ "success": true, "data": { "id": "..." }, "message": "Idea created successfully" }`

- **POST** `/ideas/add`

  - Alternative endpoint for adding ideas with flexible structure
  - Accepts additional fields: `id`, `upvotes`, `views`, `status`, `user_id`, `link`
  - Same response format as POST `/ideas`

- **PUT** `/ideas/{idea_id}` 🔒 **Requires Authentication**

  - Update an idea (partial updates supported)
  - **Headers**: `X-User-Id: <clerk_user_id>` (required)
  - Request body (all fields optional):
    ```json
    {
      "title": "Updated Title",
      "description": "Updated description",
      "problem": "Updated problem",
      "solution": "Updated solution",
      "marketSize": "Updated market size",
      "tags": ["tag1", "tag2"],
      "link": "https://example.com"
    }
    ```
  - Response: `{ "success": true, "data": { ...updated idea... }, "message": "Idea updated successfully" }`
  - Returns 403 if user is not the owner
  - Returns 404 if idea not found

- **DELETE** `/ideas/{idea_id}` 🔒 **Requires Authentication**
  - Delete an idea
  - **Headers**: `X-User-Id: <clerk_user_id>` (required)
  - Response: `{ "success": true, "message": "Idea deleted successfully" }`
  - Returns 403 if user is not the owner
  - Returns 404 if idea not found

### Webhooks

- **POST** `/webhooks/clerk`
  - Clerk webhook endpoint for user synchronization
  - Handles `user.created`, `user.updated`, `user.deleted` events
  - Requires `svix-id`, `svix-timestamp`, `svix-signature` headers for verification

### Health Check

- **GET** `/` - Root endpoint
- **GET** `/health` - Health check endpoint

## Authentication

Some endpoints require authentication via the `X-User-Id` header:

- **Header**: `X-User-Id: <clerk_user_id>`
- **Required for**: PUT `/ideas/{idea_id}`, DELETE `/ideas/{idea_id}`
- **Ownership Verification**: The authenticated user's `clerk_user_id` must match the idea's `user_id` to update or delete

**Example:**

```bash
curl -X PUT http://localhost:8000/ideas/{idea_id} \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_abc123" \
  -d '{"title": "Updated Title"}'
```

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

**Note:** Database migrations are automatically run when the Docker container starts. If running locally, you may need to run migrations manually:

```bash
alembic upgrade head
```

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
- `CLERK_WEBHOOK_SECRET`: Secret for verifying Clerk webhook signatures (optional for development)

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
FastAPI returns standard HTTP error responses:

```json
{
  "detail": "Error message"
}
```

**Idea Response Format:**
All idea responses include the `user_id` field (Clerk user ID) for ownership checking:

```json
{
  "id": "uuid",
  "title": "Idea Title",
  "description": "Description",
  "problem": "Problem statement",
  "solution": "Solution",
  "marketSize": "Market size",
  "tags": ["tag1", "tag2"],
  "author": "Author Name",
  "createdAt": "2024-01-01T00:00:00Z",
  "upvotes": 0,
  "views": 0,
  "status": "draft",
  "user_id": "clerk_user_id_here", // For ownership checking
  "link": "https://example.com"
}
```

## Database Migrations

The project uses Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

Migrations are automatically run when starting the Docker container.

## License

MIT
