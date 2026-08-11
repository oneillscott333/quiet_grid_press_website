#!/bin/zsh

# Double-click this file in Finder to start the local preview and open it in Safari.
project_dir="$(cd "$(dirname "$0")" && pwd)"
preview_url="http://127.0.0.1:4321"

cd "$project_dir" || exit 1

if ! curl --silent --fail "$preview_url" >/dev/null 2>&1; then
  npm run dev -- --host 127.0.0.1 >/tmp/quiet-grid-press-preview.log 2>&1 &

  for attempt in {1..20}; do
    if curl --silent --fail "$preview_url" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

open -a "Safari" "$preview_url"
