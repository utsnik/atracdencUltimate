#!/usr/bin/env bash
set -euo pipefail

cd /home/utking/atracdencUltimate

SLUGS=(
  "03_lorde_solar_power_2021_california"
  "bob_dylan_blood_on_the_tracks_03_youre_a_big_girl_now"
  "daft_punk_discovery_04_harder_better_faster_stronger"
  "fleetwood_mac_tango_in_the_night_10_isnt_it_midnight"
  "gundelach_my_frail_body_02_my_frail_body"
  "kendrick_lamar_to_pimp_a_butterfly_03_king_kunta"
  "miles_davis_kind_of_blue_04_all_blues"
  "rise_against_appeal_to_reason_11_savior"
  "the_weeknd_dawn_fm_02_gasoline"
)

for slug in "${SLUGS[@]}"; do
  ./build_linux/src/atracdenc \
    -e atrac3 \
    -i "/tmp/ref_${slug}_44k.wav" \
    -o "/tmp/ours_${slug}.at3" \
    --bitrate 132 \
    --quality-v10 \
    --quality-v10-stable \
    --parity \
    --smr-alloc \
    --temporal-masking

  ffmpeg -y -i "/tmp/ours_${slug}.at3" "/tmp/ours_${slug}_dec.wav"

  python3 tools/lp2_perceptual_proxy.py \
    --ref "/tmp/ref_${slug}_44k.wav" \
    --base "/tmp/sony_${slug}_dec.wav" \
    --cand "/tmp/ours_${slug}_dec.wav" \
    > "/tmp/score_${slug}.txt"

  echo "${slug}: full=$(grep delta_full /tmp/score_${slug}.txt | cut -d= -f2) hf=$(grep delta_hf /tmp/score_${slug}.txt | cut -d= -f2) seg_p10=$(grep delta_seg_p10 /tmp/score_${slug}.txt | cut -d= -f2) seg_med=$(grep delta_seg_median /tmp/score_${slug}.txt | cut -d= -f2)"
done
