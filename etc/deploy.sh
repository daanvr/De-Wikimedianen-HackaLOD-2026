#!/usr/bin/env bash
# Rebuild and deploy siboga.nl when the content repo or the code repo has new commits.
# Runs on the server from the systemd timer, or by hand with --force.
set -euo pipefail

# The code repo is the parent of etc/; state and lock live next to it
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$(dirname "$APP_DIR")"
HTDOCS=/var/www/siboga.nl/htdocs
STATE_FILE="$STATE_DIR/last-deployed"
LOCK_FILE="$STATE_DIR/deploy.lock"

# systemd and a non-interactive ssh session don't load ~/.profile or ~/.bashrc,
# so add uv (~/.local/bin), snaps and Node from nvm, if that is how it was installed
export PATH="$HOME/.local/bin:$PATH:/snap/bin"
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

if [[ -s "$NVM_DIR/nvm.sh" ]]; then
    set +eu
    source "$NVM_DIR/nvm.sh"
    set -eu
fi

for command in git flock uv npm rsync; do
    if ! command -v "$command" > /dev/null; then
        echo "Error: $command not found on PATH ($PATH)" >&2
        exit 1
    fi
done

# Everything lives in a function, so bash has read the whole script before
# the git reset below can change this file.
function main() {
    cd "$APP_DIR"

    # Never run two builds at once
    exec 9> "$LOCK_FILE"
    flock -n 9 || exit 0

    git fetch --quiet origin
    git -C content fetch --quiet origin
    local target="$(git rev-parse '@{u}') $(git -C content rev-parse '@{u}')"

    if [[ "${1:-}" != "--force" && -f "$STATE_FILE" && "$(cat "$STATE_FILE")" == "$target" ]]; then
        exit 0
    fi

    echo "Deploying code and content: $target"
    git reset --hard --quiet '@{u}'
    git -C content reset --hard --quiet '@{u}'

    (cd pipeline && uv sync --quiet && uv run siboga all && uv run siboga check)
    (cd frontend && npm ci --silent && npm run build)

    rsync -a --delete frontend/dist/ "$HTDOCS/"
    echo "$target" > "$STATE_FILE"
    echo "Deployed"
}

main "$@"
exit