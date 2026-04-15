#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/utking/atracdencUltimate"

if [[ "$(pwd)" != "$REPO_DIR" ]]; then
  echo "ERROR: Run this script from $REPO_DIR" >&2
  exit 1
fi

TRACKS=(
  '03 Lorde - Solar Power [2021] - California.flac'
  "Bob Dylan - Blood on the Tracks - 03 - You"$'\xe2\x80\x99'"re a Big Girl Now.flac"
  'Daft Punk - Discovery - 04 - Harder, Better, Faster, Stronger.flac'
  "Fleetwood Mac - Tango in the Night - 10 - Isn"$'\xe2\x80\x99'"t It Midnight.flac"
  'Gundelach - My Frail Body - 02 - My Frail Body.flac'
  'Kendrick Lamar - To Pimp a Butterfly - 03 - King Kunta.flac'
  'Miles Davis - Kind of Blue - 04 - All Blues.flac'
  'Rise Against - Appeal to Reason - 11 - Savior.flac'
  'The Weeknd - Dawn FM - 02 - Gasoline.flac'
)

slugify() {
  local name="$1"
  local stem="${name##*/}"
  stem="${stem%.flac}"

  # lowercase, spaces to underscores, strip non [a-z0-9_], collapse repeats
  stem="$(printf '%s' "$stem" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | sed -E 's/[^a-z0-9_]+//g; s/_+/_/g; s/^_+//; s/_+$//')"

  if [[ -z "$stem" ]]; then
    echo "untitled"
  else
    echo "$stem"
  fi
}

for track in "${TRACKS[@]}"; do
  if [[ ! -f "$track" ]]; then
    echo "ERROR: Missing track: $track" >&2
    exit 1
  fi

  slug="$(slugify "$track")"
  wav_44k="/tmp/ref_${slug}_44k.wav"
  sony_at3="/tmp/sony_${slug}.at3"
  sony_dec_wav="/tmp/sony_${slug}_dec.wav"

  ffmpeg -y -i "$track" -ar 44100 "$wav_44k"
  LD_LIBRARY_PATH=./reverse/linux ./reverse/linux/at3tool -e -br 132 "$wav_44k" "$sony_at3"
  ffmpeg -y -i "$sony_at3" "$sony_dec_wav"

  echo "DONE: $slug"
done
