#!/bin/zsh

set -eu

repo_root="${0:A:h:h}"
source "$repo_root/zprofile"

typeset -ga captured_args
sox() {
  captured_args=("$@")
}

ffmpeg() {
  return 0
}

capture_audio

expected_prefix=(
  -t coreaudio "BlackHole 2ch"
  -r 48000
  -c 1
  -b 24
  -C 8
)

if [[ "${captured_args[1,11]}" != "${expected_prefix}" ]]; then
  print -u2 "unexpected sox arguments: ${captured_args[*]}"
  exit 1
fi

if [[ ! "${captured_args[12]}" =~ '^\./video_audio_[0-9]{8}_[0-9]{6}\.flac$' ]]; then
  print -u2 "unexpected output path: ${captured_args[12]-<missing>}"
  exit 1
fi

if [[ "${captured_args[13,14]}" != "remix -" ]]; then
  print -u2 "expected mono downmix effect, got: ${captured_args[13,14]-<missing>}"
  exit 1
fi
