#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_TPL="$REPO_DIR/launchd/com.zephyr.jandi-picker.plist.template"
PLIST_OUT="$HOME/Library/LaunchAgents/com.zephyr.jandi-picker.plist"
LOG_DIR="$REPO_DIR/logs"

# launchd runs with a minimal PATH and no shim resolution — pin the system python3
# to keep the job independent from asdf / version manager state.
PYTHON_PATH="/usr/bin/python3"
if [[ ! -x "$PYTHON_PATH" ]]; then
  echo "✗ $PYTHON_PATH 를 찾을 수 없습니다. 'xcode-select --install' 실행 필요"
  exit 1
fi

mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$PLIST_OUT")"

sed -e "s|__PYTHON_PATH__|$PYTHON_PATH|g" \
    -e "s|__REPO_DIR__|$REPO_DIR|g" \
    "$PLIST_TPL" > "$PLIST_OUT"

launchctl unload "$PLIST_OUT" 2>/dev/null || true
launchctl load "$PLIST_OUT"

echo "✓ launchd 등록 완료: $PLIST_OUT"
echo ""
echo "다음 단계 (sudo 권한 필요 — 맥 잠자기 깨우기):"
echo "    sudo pmset repeat wakeorpoweron MTWRFSU 19:58:00"
echo ""
echo "확인 명령:"
echo "    pmset -g sched                    # 깨우기 스케줄 확인"
echo "    launchctl list | grep jandi       # launchd 등록 확인"
echo "    tail -f $LOG_DIR/stdout.log       # 실행 로그"
echo ""
echo "수동 테스트:"
echo "    $PYTHON_PATH $REPO_DIR/scripts/publish_til.py"
