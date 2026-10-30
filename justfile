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

# Clone the content repo into content/, or update it
content:
    if [ -d content/.git ]; then git -C content pull --ff-only; else git clone https://github.com/hay/siboga-content.git content; fi

# Fetch, build and check
data:
    cd pipeline && uv run siboga all && uv run siboga check

# Build and deploy on the server right now, without waiting for the timer
deploy:
    ssh siboga siboga/app/etc/deploy.sh --force

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
