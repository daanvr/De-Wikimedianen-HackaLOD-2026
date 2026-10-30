_default:
    @just --list

# Install the Python dependencies of the pipeline
setup:
    cd pipeline && uv sync

# Clone or update the content repo
content:
    if [ -d content/.git ]; then git -C content pull; else git clone https://github.com/hay/siboga-content content; fi

# Fetch sources into the cache (needs internet)
fetch:
    cd pipeline && uv run siboga fetch

# Build the frontend data from content and cache (no internet)
build-data:
    cd pipeline && uv run siboga build

# Fetch, build and check
data:
    cd pipeline && uv run siboga all && uv run siboga check

# Check the frontend data
check:
    cd pipeline && uv run siboga check

# Pipeline tests
test:
    cd pipeline && uv run pytest

# Install the frontend dependencies
frontend:
    cd frontend && npm install

# Run the frontend on http://localhost:5173
dev:
    cd frontend && npm run dev

# Build the static site into frontend/dist/
build:
    cd frontend && npm run build

deploy:
    rsync -avzL --delete site/* siboga:/var/www/siboga.nl/htdocs/
