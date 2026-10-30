# Ontwikkelen
[Documentatie](README.md) › Ontwikkelen

Nodig: [uv](https://docs.astral.sh/uv/), [just](https://just.systems/) en git. Voor de frontend ook Node.js met npm.

## Eerste keer
```bash
just content    # kloont de content-repo naar content/
just setup      # uv sync in pipeline/
just data       # fetch, build en check
just frontend   # npm install in frontend/
just dev        # de site op http://localhost:5173
```

Daarna staan `siboga.json` en `media/` in `frontend/public/data/` (niet in git). Wil je naar een andere kluis wijzen, zet dan `[content] path` in `pipeline/config.toml`.

## justfile
| Recept           | Doet                                         |
| ---------------- | -------------------------------------------- |
| `content`        | Content-repo klonen of bijwerken             |
| `setup`          | Afhankelijkheden van de pipeline installeren |
| `fetch`          | Bronnen ophalen naar de cache                |
| `build-data`     | Frontend data bouwen, zonder internet        |
| `data`           | Ophalen, bouwen en controleren               |
| `check`          | Frontend data controleren                    |
| `test`           | Pipeline-tests                               |
| `deploy`         | Op de server nu bouwen en uitrollen          |
| `frontend`       | Afhankelijkheden van de frontend installeren |
| `dev`            | Frontend draaien op http://localhost:5173    |
| `build-frontend` | Statische site bouwen in `frontend/dist/`    |

## Presenteren zonder internet
Draai `just data` zolang er internet is. Daarna werkt `just build-data` zonder internet, en staat alles lokaal. Valt een bron uit tijdens `fetch`, dan blijft de oude kopie in de cache staan. Bewaar een kopie van `pipeline/cache/` op meer dan één laptop.

## Server
siboga.nl draait op Ubuntu met nginx ([etc/nginx.conf](../etc/nginx.conf)). De server bouwt de site zelf en zet hem in `/var/www/siboga.nl/htdocs/` (zie [Automatisch bouwen](#automatisch-bouwen)). Omdat de router volledige paden gebruikt, moet in het `server`-blok voor poort 443:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

## Automatisch bouwen
Een systemd-timer start elke minuut [etc/deploy.sh](../etc/deploy.sh). Dat script kijkt of er nieuwe commits in de content-repo of in deze repo staan. Zo ja, dan:

1. haalt het beide repo's op;
2. draait het `siboga all` en `siboga check` in `pipeline/`;
3. bouwt het de frontend met `npm run build`;
4. zet het `frontend/dist/` met rsync in `/var/www/siboga.nl/htdocs/`.

Gaat een stap mis, dan blijft de oude site staan en probeert het script het een minuut later opnieuw. Welke commits het laatst zijn uitgerold, staat in `~/siboga/last-deployed`. Twee builds tegelijk kan niet; dan stopt de tweede meteen.

Nieuwe content staat dus binnen een minuut of twee online, plus de tijd die het bouwen kost. Meteen bouwen, zonder op de timer te wachten, doe je vanaf je laptop met `just deploy` (je hebt een SSH-host `siboga` nodig die inlogt als `hay`). Wat er gebeurde, zie je op de server met:

```bash
sudo journalctl -u siboga-deploy -f
```

Het script ziet alleen gepushte commits: wat lokaal op de server in `app/` of `app/content/` verandert, gooit het weg.

## Server inrichten
Eenmalig, op de Ubuntu-server. Nodig: git, rsync en Node.js met npm (`sudo apt install git rsync nodejs npm`, of Node via [NodeSource](https://github.com/nodesource/distributions) als de versie van Ubuntu te oud is voor Vite).

Alles draait als gebruiker `hay`, vanuit `~/siboga/`. Die gebruiker moet de htdocs bezitten:

```bash
sudo mkdir -p /var/www/siboga.nl/htdocs
sudo chown -R hay:hay /var/www/siboga.nl/htdocs
```

Installeer uv en kloon de twee repo's:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
mkdir ~/siboga
git clone https://github.com/daanvr/De-Wikimedianen-HackaLOD-2026.git ~/siboga/app
git clone https://github.com/hay/siboga-content.git ~/siboga/app/content
```

Beide repo's zijn openbaar, dus klonen over HTTPS werkt zonder sleutels.

Draai de eerste keer met de hand, zodat je fouten meteen ziet:

```bash
~/siboga/app/etc/deploy.sh --force
```

Zet daarna de timer aan:

```bash
sudo cp ~/siboga/app/etc/siboga-deploy.service ~/siboga/app/etc/siboga-deploy.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now siboga-deploy.timer
systemctl list-timers siboga-deploy.timer
```

Verander je later iets aan de twee unit-bestanden in `etc/`, kopieer ze dan opnieuw en draai weer `daemon-reload`. Een nieuwe versie van `deploy.sh` komt vanzelf mee met de volgende deploy. Staat de code ergens anders dan `/home/hay/siboga/app`, pas dan `User`, `PATH` en `ExecStart` in de service aan; het script zelf vindt zijn paden vanuit waar het staat.

De cache in `~/siboga/app/pipeline/cache/` is de kopie waarmee we zonder internet kunnen presenteren. Haal hem af en toe naar een laptop:

```bash
rsync -avz siboga:siboga/app/pipeline/cache/ pipeline/cache/
```
