# Ontwikkelen
[Documentatie](README.md) › Ontwikkelen

Nodig: [uv](https://docs.astral.sh/uv/), [just](https://just.systems/) en git. Voor de frontend straks ook Node.js met npm.

## Eerste keer
```bash
just content    # kloont de content-repo naar content/
just setup      # uv sync in pipeline/
just data       # fetch, build en check
```

Daarna staan `siboga.json` en `media/` in `frontend/public/data/` (niet in git). Wil je naar een andere kluis wijzen, zet dan `[content] path` in `pipeline/config.toml`.

## justfile
| Recept       | Doet                                           |
| ------------ | ---------------------------------------------- |
| `content`    | Content-repo klonen of bijwerken               |
| `setup`      | Afhankelijkheden van de pipeline installeren   |
| `fetch`      | Bronnen ophalen naar de cache                  |
| `build-data` | Frontend data bouwen, zonder internet          |
| `data`       | Ophalen, bouwen en controleren                 |
| `check`      | Frontend data controleren                      |
| `test`       | Pipeline-tests                                 |
| `deploy`     | Zet nog de placeholder in `site/` op de server |

Recepten voor de frontend (`dev`, `preview`, en `deploy` van `frontend/dist/`) komen erbij als de frontend er is.

## Presenteren zonder internet
Draai `just data` zolang er internet is. Daarna werkt `just build-data` zonder internet, en staat alles lokaal. Valt een bron uit tijdens `fetch`, dan blijft de oude kopie in de cache staan. Bewaar een kopie van `pipeline/cache/` op meer dan één laptop.

## Server
siboga.nl draait op nginx ([etc/nginx.conf](../etc/nginx.conf)). `just deploy` zet de site met rsync in `/var/www/siboga.nl/htdocs/`; daarvoor heb je een SSH-host `siboga` nodig. Omdat de router volledige paden gebruikt, moet in het `server`-blok voor poort 443:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

## Automatisch bouwen
Een cronjob kijkt regelmatig of er nieuwe commits in de content-repo staan. Zo ja, dan haalt hij de content-repo op, draait `just data` en zet de nieuwe site op de server. Hoe en waar die cronjob precies draait, werken we uit als we de server inrichten.
