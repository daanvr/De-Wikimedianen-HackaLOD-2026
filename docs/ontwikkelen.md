# Ontwikkelen
We beginnen met lokaal ontwikkelen. Uitrollen naar de server komt daarna.

## Nodig
- [uv](https://docs.astral.sh/uv/) voor Python
- Node.js (LTS) met npm
- [just](https://just.systems/) voor de commando's
- git

## Eerste keer
```bash
git clone https://github.com/hay/siboga-content content
```

```bash
just setup
```

```bash
just data
```

```bash
just dev
```

Daarna draait de site op het adres dat Vite noemt (meestal http://localhost:5173/).

Wil je de pipeline naar een andere map met content laten kijken, bijvoorbeeld je eigen Obsidian-kluis, zet dan in `pipeline/config.toml`:

```toml
[content]
path = "/pad/naar/de/kluis"
```

Werk je alleen aan de frontend, dan kun je `just data` overslaan en `just fixture` gebruiken. Dat zet de voorbeelddata klaar.

## justfile
Voorstel voor de `justfile`. Alle commando's draaien vanuit de root van de repo.

```just
_default:
    @just --list

# Python- en npm-afhankelijkheden installeren
setup:
    cd pipeline && uv sync
    cd frontend && npm install

# Content-repo bijwerken
content:
    git -C content pull

# Linked Data ophalen naar de cache
fetch:
    cd pipeline && uv run siboga fetch

# Frontend data bouwen uit content en cache
data: fetch
    cd pipeline && uv run siboga build

# Voorbeelddata klaarzetten voor frontendwerk zonder pipeline
fixture:
    mkdir -p frontend/public/data
    cp frontend/fixtures/siboga.example.json frontend/public/data/siboga.json

# Vite-ontwikkelserver
dev:
    cd frontend && npm run dev

# Pipeline-tests
test:
    cd pipeline && uv run pytest

# Statische site bouwen
build:
    cd frontend && npm run build

# Naar de server
deploy: build
    rsync -avzL --delete frontend/dist/ siboga:/var/www/siboga.nl/htdocs/
```

Nu deployt de `justfile` nog de placeholder in `site/`. Zodra de Vue-frontend klaar is, gaat `deploy` naar `frontend/dist/`, zoals hierboven.

## .gitignore
Toe te voegen zodra de mappen er zijn:

```
content/
pipeline/.venv/
pipeline/cache/
pipeline/config.toml
frontend/node_modules/
frontend/dist/
frontend/public/data/
```

## Server
- Domein: siboga.nl, met nginx. De configuratie staat in [etc/nginx.conf](../etc/nginx.conf).
- De site staat op de server in `/var/www/siboga.nl/htdocs/`. `just deploy` zet hem daar neer met rsync. Daarvoor heb je een SSH-host `siboga` nodig in je eigen `~/.ssh/config`.
- Omdat de router hash-history gebruikt, hoeft er niets aan de nginx-configuratie te veranderen.
- Later: automatisch opnieuw bouwen en uitrollen als de content-repo verandert. Zie [beslissingen.md](beslissingen.md).
