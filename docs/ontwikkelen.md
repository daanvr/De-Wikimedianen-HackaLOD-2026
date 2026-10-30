# Ontwikkelen
[Documentatie](README.md) › Ontwikkelen

We beginnen met lokaal ontwikkelen. Uitrollen naar de server komt daarna. Hoe de onderdelen samenhangen, staat in [architectuur.md](architectuur.md).

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

Werk je alleen aan de frontend, dan kun je `just data` overslaan en `just fixture` gebruiken. Dat zet de voorbeelddata klaar (zie [frontend-data.md](frontend-data.md#bestanden)).

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

# Gebouwde site lokaal tonen, zonder internet
preview: build
    cd frontend && npx vite preview

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

## Presenteren zonder internet
Een belangrijk doel is dat we kunnen presenteren, ook als een externe dienst uitvalt (zie de [principes](architectuur.md#principes)). Vóór een presentatie:
1. `just data` terwijl er nog internet is. Daarmee staan alle bronnen en plaatjes in de cache en in `frontend/public/data/`.
2. `just preview`. Dat bouwt de site en toont hem lokaal. Daarvoor is geen internet nodig.
3. Valt ook de kaartdienst uit, dan schakelt de kaart over op de lokale ondergrond (zie [frontend.md](frontend.md#live-bronnen)).

Houd de cache (`pipeline/cache/`) op meer dan één plek: op de server en op de laptops waarmee we presenteren. Een kopie van die map is genoeg.

## Server
- Domein: siboga.nl, met nginx. De configuratie staat in [etc/nginx.conf](../etc/nginx.conf).
- De site staat op de server in `/var/www/siboga.nl/htdocs/`. `just deploy` zet hem daar neer met rsync. Daarvoor heb je een SSH-host `siboga` nodig in je eigen `~/.ssh/config`.
- De router gebruikt gewone URL's (zie [frontend.md](frontend.md#routes)). Daarvoor moet nginx elke URL die geen bestand is naar `index.html` sturen. Toe te voegen aan het `server`-blok voor poort 443 in `etc/nginx.conf`, zodra de Vue-frontend live gaat:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

- Later: automatisch opnieuw bouwen en uitrollen als de content-repo verandert. Zie [beslissingen.md](beslissingen.md#open-vragen).

## Zie ook
- [pipeline.md](pipeline.md#commandos): de commando's van de pipeline
- [frontend.md](frontend.md): de opbouw van de frontend
- [beslissingen.md](beslissingen.md): wat nog open staat over draaien en uitrollen
