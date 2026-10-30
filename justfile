_default:
    @just --list

# Build the frontend data from content and cache (no internet)
build-data:
    cd pipeline && uv run siboga build

# Build the static site into frontend/dist/
build-frontend:
    cd frontend && npm run build

# Check the frontend data
check:
    cd pipeline && uv run siboga check

# Fetch, build and check
data:
    cd pipeline && uv run siboga all && uv run siboga check

deploy:
    just build-frontend
    rsync -avzL --delete frontend/dist/* siboga:/var/www/siboga.nl/htdocs/

# Run the frontend on http://localhost:5173
dev:
    cd frontend && npm run dev

# Fetch sources into the cache (needs internet)
fetch:
    cd pipeline && uv run siboga fetch

# Install the frontend dependencies
frontend:
    cd frontend && npm install

# Install the Python dependencies of the pipeline
setup:
    cd pipeline && uv sync

# Pipeline tests
test:
    cd pipeline && uv run pytest
