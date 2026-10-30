# Ontwikkelen
[Documentatie](README.md) › Ontwikkelen

Nodig: [uv](https://docs.astral.sh/uv/), Node.js met npm, [just](https://just.systems/) en git.

## Eerste keer
```bash
git clone https://github.com/hay/siboga-content content
just setup
just data
just dev
```

Alleen aan de frontend werken? Gebruik `just fixture` in plaats van `just data`. Wil je naar een andere kluis wijzen, zet dan `[content] path` in `pipeline/config.toml`.

## justfile
```just
setup:
    cd pipeline && uv sync
    cd frontend && npm install

data:
    cd pipeline && uv run siboga fetch && uv run siboga build

fixture:
    mkdir -p frontend/public/data
    cp frontend/fixtures/siboga.example.json frontend/public/data/siboga.json

dev:
    cd frontend && npm run dev

preview:
    cd frontend && npm run build && npx vite preview

deploy:
    cd frontend && npm run build
    rsync -avzL --delete frontend/dist/ siboga:/var/www/siboga.nl/htdocs/
```

Nu deployt de `justfile` nog de placeholder in `site/`.

In `.gitignore` komen: `content/`, `pipeline/cache/`, `pipeline/config.toml`, `frontend/node_modules/`, `frontend/dist/` en `frontend/public/data/`.

## Presenteren zonder internet
Draai `just data` zolang er internet is, en daarna `just preview`. Dan staat alles lokaal. Bewaar een kopie van `pipeline/cache/` op meer dan één laptop.

## Server
siboga.nl draait op nginx ([etc/nginx.conf](../etc/nginx.conf)). `just deploy` zet de site met rsync in `/var/www/siboga.nl/htdocs/`; daarvoor heb je een SSH-host `siboga` nodig. Omdat de router volledige paden gebruikt, moet in het `server`-blok voor poort 443:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```
