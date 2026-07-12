#!/usr/bin/env bats

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  test_dir="$(mktemp -d)"
  mkdir -p "$test_dir/scripts"
  ln -s "$repo_root/scripts/check-encoding" "$test_dir/scripts/check-encoding"
  cd "$test_dir" || return 1
  git init -q
  git config user.email test@example.com
  git config user.name test
  fffd=$'\xef\xbf\xbd'
}

teardown() {
  rm -rf "$test_dir"
}

# --- pass cases ---

@test "no tracked files: exits 0" {
  run ./scripts/check-encoding

  [ "$status" -eq 0 ]
}

@test "ASCII-only file: exits 0" {
  printf 'hello world\n' >clean.txt
  git add clean.txt

  run ./scripts/check-encoding

  [ "$status" -eq 0 ]
}

@test "valid UTF-8 with Japanese and box-drawing characters: exits 0" {
  {
    printf '## \xe3\x83\xac\xe3\x82\xa4\xe3\x83\xa4\xe3\x83\xbc\xe8\xa8\xad\xe8\xa8\x88\n'
    printf '\xe2\x94\x9c\xe2\x94\x80\xe2\x94\x80 base/\n'
    printf '\xe2\x94\x82   \xe2\x94\x94\xe2\x94\x80\xe2\x94\x80 part.toml\n'
    printf '\xe2\x94\x94\xe2\x94\x80\xe2\x94\x80 scale/\n'
  } >tree.md
  git add tree.md

  run ./scripts/check-encoding

  [ "$status" -eq 0 ]
}

@test "untracked file with U+FFFD: exits 0 (git-untracked files are not checked)" {
  printf "contains %s here\n" "$fffd" >garbled.txt
  # intentionally NOT added to git

  run ./scripts/check-encoding

  [ "$status" -eq 0 ]
}

@test "binary file with U+FFFD bytes is skipped: exits 0" {
  printf 'binary\x00data\xef\xbf\xbd\n' >binary.bin
  git add binary.bin

  run ./scripts/check-encoding

  [ "$status" -eq 0 ]
}

# --- fail cases ---

@test "single U+FFFD in tracked file: exits 1 with filename and line number" {
  printf "contains %s here\n" "$fffd" >garbled.txt
  git add garbled.txt

  run ./scripts/check-encoding

  [ "$status" -eq 1 ]
  [[ $output == *"garbled.txt:1: contains U+FFFD"* ]]
}

@test "U+FFFD mid-Japanese text (reイyaa garbling pattern): exits 1" {
  # レ + U+FFFD + ヤー (simulates the documented レイヤー corruption)
  printf '\xe3\x83\xac\xef\xbf\xbd\xe3\x83\xa4\xe3\x83\xbc\n' >garbled.md
  git add garbled.md

  run ./scripts/check-encoding

  [ "$status" -eq 1 ]
  [[ $output == *"garbled.md:1:"* ]]
}

@test "double consecutive U+FFFD (two replacement chars in a row): exits 1" {
  printf '\xef\xbf\xbd\xef\xbf\xbd\n' >garbled.txt
  git add garbled.txt

  run ./scripts/check-encoding

  [ "$status" -eq 1 ]
  [[ $output == *"garbled.txt:1:"* ]]
}

@test "U+FFFD at start of line: exits 1" {
  printf "%s start of line\n" "$fffd" >garbled.txt
  git add garbled.txt

  run ./scripts/check-encoding

  [ "$status" -eq 1 ]
  [[ $output == *"garbled.txt:1:"* ]]
}

@test "U+FFFD at end of line: exits 1" {
  printf "end of line %s\n" "$fffd" >garbled.txt
  git add garbled.txt

  run ./scripts/check-encoding

  [ "$status" -eq 1 ]
  [[ $output == *"garbled.txt:1:"* ]]
}

@test "multiple U+FFFD on different lines: all lines reported" {
  printf "line 1 ok\nline 2 %s bad\nline 3 ok\nline 4 %s bad\n" "$fffd" "$fffd" >garbled.txt
  git add garbled.txt

  run ./scripts/check-encoding

  [ "$status" -eq 1 ]
  [[ $output == *"garbled.txt:2:"* ]]
  [[ $output == *"garbled.txt:4:"* ]]
}

@test "U+FFFD in multiple files: all affected files reported" {
  printf "garbled %s\n" "$fffd" >file1.txt
  printf "also garbled %s\n" "$fffd" >file2.txt
  git add file1.txt file2.txt

  run ./scripts/check-encoding

  [ "$status" -eq 1 ]
  [[ $output == *"file1.txt:"* ]]
  [[ $output == *"file2.txt:"* ]]
}

@test "clean file and garbled file: only garbled file is reported" {
  printf 'clean content\n' >clean.txt
  printf "garbled %s content\n" "$fffd" >garbled.txt
  git add clean.txt garbled.txt

  run ./scripts/check-encoding

  [ "$status" -eq 1 ]
  [[ $output != *"clean.txt"* ]]
  [[ $output == *"garbled.txt:"* ]]
}

@test "error output mentions U+FFFD and fix guidance" {
  printf "bad %s content\n" "$fffd" >garbled.txt
  git add garbled.txt

  run ./scripts/check-encoding

  [ "$status" -eq 1 ]
  [[ $output == *"U+FFFD"* ]]
  [[ $output == *"Fix"* ]]
}
