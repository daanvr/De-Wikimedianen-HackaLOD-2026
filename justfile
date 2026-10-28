_default:
    @just --list

deploy:
    rsync -avzL --delete site/* siboga:/var/www/siboga.nl/htdocs/