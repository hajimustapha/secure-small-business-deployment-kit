# Secure Small-Business Deployment Kit

A containerized deployment kit for running a Python Flask application with a PostgreSQL database using Docker and Docker Compose.

The project demonstrates how to package an application, connect it to a separate database service, persist data, perform database backups, and apply practical container security controls.

## 1. Project Objectives

The objectives of this project are to:

- Containerize a Python Flask application.
- Deploy the application and PostgreSQL as separate services.
- Establish private communication between application and database containers.
- Persist database records beyond container recreation.
- Implement database backup and restore procedures.
- Configure health checks and application logging.
- Apply baseline container security controls.
- Document deployment, operation, recovery, and known limitations.

## 2. Architecture

The deployment consists of two primary services:

| Component | Responsibility |
|---|---|
| Flask application | Handles HTTP requests and application logic |
| PostgreSQL | Stores application records |
| Docker Compose | Defines and manages the services |
| Named Docker volume | Persists PostgreSQL data |
| Docker secrets | Supplies the application with its database password |

### Request flow

```text
          Host machine
               |
               | HTTP :5050
               v
       Flask Application
          (Container)
               |
               | PostgreSQL :5432
               v
       PostgreSQL Database
          (Container)
               |
               v
         Named Volume
        (Persistent Data)
```

The database is not published on a host port. The Flask application accesses it through the internal Docker Compose network.

## 3. Technology Stack

- Python 3.12
- Flask
- PostgreSQL 15
- Psycopg
- Docker Engine
- Docker Compose

## 4. Prerequisites

Install the following before deployment:

- Linux, macOS, or Windows with a supported Docker environment.
- Docker Engine or Docker Desktop.
- Docker Compose.
- Git (optional, for repository management).

Verify the Docker installation:

```bash
docker --version
docker compose version
```

## 5. Project Structure

```text
secure-deployment-kit/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── compose.yml
├── .dockerignore
├── .gitignore
├── .env.example
├── README.md
│
├── secrets/
│   └── db_password.txt
│
└── backup/
    └── database backups
```

**Note:** The `secrets/` and `backup/` directories contain local operational files and are excluded from Git.

## 6. Configuration

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd secure-deployment-kit
```

### Step 2: Configure environment variables

Create your local environment file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
DB_USER=your_database_user
BD_PASSWD=your_database_password
```

Use a strong database password.

### Step 3: Configure the database secret

Create the required directories:

```bash
mkdir -p secrets backup
```

Create the secret file:

```bash
nano secrets/db_password.txt
```

Enter the same database password configured as `BD_PASSWD` in `.env`.

The application reads its database password from the mounted secret file rather than receiving it through a regular application environment variable.

**Important:** The secret file and the database password must match.

## 7. Deployment

Build and start the application:

```bash
docker compose up -d --build
```

Check the running services:

```bash
docker compose ps
```

Both the application and database should report a healthy status.

Inspect application logs:

```bash
docker compose logs app
```

Inspect database logs:

```bash
docker compose logs db
```

## 8. Application Endpoints

The application exposes the following HTTP endpoints.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks application responsiveness |
| GET | `/notes` | Retrieves stored notes |
| POST | `/notes` | Creates a new note |

### Health check

```bash
curl -i http://localhost:5050/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Retrieve notes

```bash
curl -i http://localhost:5050/notes
```

### Create a note

```bash
curl -i -X POST http://localhost:5050/notes \
  -H "Content-Type: application/json" \
  -d '{"content": "My first database record"}'
```

A successful creation returns HTTP `201 Created`.

## 9. Database Persistence

PostgreSQL stores its data in a named Docker volume.

The volume is defined in `compose.yml`:

```yaml
volumes:
  db_data:
```

The database service mounts this volume at:

```text
/var/lib/postgresql/data
```

This allows database records to survive database container recreation.

To verify persistence, recreate only the database container:

```bash
docker compose up -d --force-recreate db
```

Wait until the database reports healthy, then retrieve the records:

```bash
curl http://localhost:5050/notes
```

Existing records should remain available.

## 10. Database Backup and Restore

### Creating a backup

Create a PostgreSQL SQL dump:

```bash
docker compose exec -T db sh -c \
  'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "backup/backup_$(date +%Y%m%d_%H%M%S).sql"
```

Verify the backup file:

```bash
ls -lh backup/
```

### Testing a restore

Restore testing should use a separate database so that the existing application database is not overwritten.

Create a temporary database:

```bash
docker compose exec db sh -c \
  'createdb -U "$POSTGRES_USER" restore_test'
```

Restore a selected backup:

```bash
cat backup/your_backup_file.sql | docker compose exec -T db sh -c \
  'psql -U "$POSTGRES_USER" -d restore_test'
```

Inspect the restored tables:

```bash
docker compose exec db sh -c \
  'psql -U "$POSTGRES_USER" -d restore_test -c "\dt"'
```

After verifying the restored records, remove only the temporary test database:

```bash
docker compose exec db sh -c \
  'dropdb -U "$POSTGRES_USER" restore_test'
```

Keep a copy of important backups outside the Docker host as an additional recovery measure.

## 11. Container Security Controls

The application container uses several security controls.

| Security control | Implementation |
|---|---|
| Non-root execution | Runs as an unprivileged `appuser` |
| Capability reduction | Drops all Linux capabilities |
| Read-only filesystem | Enables `read_only: true` |
| Temporary writable storage | Uses `/tmp` through `tmpfs` |
| Privilege escalation protection | Enables `no-new-privileges` |
| Secret handling | Mounts the database password as a Docker secret |
| Network isolation | Does not publish the PostgreSQL port to the host |
| Build-context protection | Uses `.dockerignore` |
| Repository protection | Excludes credentials and backups through `.gitignore` |

### Security limitations

This project implements a practical baseline, not a complete production security architecture.

- File-backed Docker Compose secrets are mounted files; they are not automatically encrypted at rest.
- PostgreSQL currently receives its initial password through the Compose environment configuration.
- The Flask application currently uses Werkzeug's development server. It should be replaced with a production WSGI server before an internet-facing production deployment.
- Additional controls such as TLS, centralized secret management, monitoring, and production infrastructure hardening are outside the current project scope.

## 12. Troubleshooting

### Check service status

```bash
docker compose ps
```

### Inspect application logs

```bash
docker compose logs --tail=50 app
```

### Inspect database logs

```bash
docker compose logs --tail=50 db
```

### Validate Compose configuration

```bash
docker compose config -q
```

### Check application responsiveness

```bash
curl -i http://localhost:5050/health
```

### Check database connectivity through the application

```bash
curl -i http://localhost:5050/notes
```

An HTTP `503` from `/notes` indicates that the application could not complete its database operation. Check database health, credentials, and service logs.

## 13. Stopping the Deployment

Stop and remove the Compose containers and network:

```bash
docker compose down
```

This preserves the named database volume.

**Warning:** Do not use `docker compose down -v` unless you deliberately intend to delete the database volume and its stored data.

## 14. Verification Results

The following tests have been performed during development:

| Test | Result |
|---|---|
| Application container builds and starts | Passed |
| Application health endpoint | Passed |
| PostgreSQL health check | Passed |
| Flask-to-PostgreSQL communication | Passed |
| Note creation and retrieval | Passed |
| Non-root application execution | Passed |
| Read-only filesystem verification | Passed |
| Temporary `/tmp` write access | Passed |
| Linux capability reduction | Passed |
| `no-new-privileges` verification | Passed |
| Database backup creation | Passed |
| Database restore test | Passed |
| Database persistence after container recreation | Passed |

## 15. Project Status

The core deployment, persistence, backup/recovery, and baseline security objectives have been implemented and tested.

The remaining work focuses on documentation review, repository hygiene, and preparing the project for publication.

---

**Project:** Secure Small-Business Deployment Kit  
**Purpose:** Practical demonstration of containerized application deployment, database persistence, recovery, and baseline container security.