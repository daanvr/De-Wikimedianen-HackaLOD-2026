_default:
    @just --list

# Python-afhankelijkheden van de pipeline installeren
setup:
    cd pipeline && uv sync

# Content-repo ophalen of bijwerken
content:
    if [ -d content/.git ]; then git -C content pull; else git clone https://github.com/hay/siboga-content content; fi

# Bronnen ophalen naar de cache (internet nodig)
fetch:
    cd pipeline && uv run siboga fetch

# Frontend data bouwen uit content en cache (zonder internet)
build-data:
    cd pipeline && uv run siboga build

# Ophalen, bouwen en controleren
data:
    cd pipeline && uv run siboga all && uv run siboga check

# Frontend data controleren
check:
    cd pipeline && uv run siboga check

# Pipeline-tests
test:
    cd pipeline && uv run pytest

deploy:
    rsync -avzL --delete site/* siboga:/var/www/siboga.nl/htdocs/
