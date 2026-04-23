# Backlog

본 레포 범위에서 당장 다루지 않고 미뤄둔 후속 항목들.

## 1. stderr `Operation not permitted` 원인 규명 및 가설 검증 ✅ 해결 (2026-04-23)

**증상**
`logs/stderr.log` 에 다음 에러가 반복적으로 기록되어 있었음:

```
/Applications/Xcode.app/Contents/Developer/usr/bin/python3: can't open file '/Users/zephyr/Documents/projects/jandi-picker/scripts/publish_til.py': [Errno 1] Operation not permitted
```

**결론: 가설 기각 → 근본 원인은 `~/Documents/` TCC 보호**
- `/usr/bin/python3` 하드핀 이후에도 launchd 컨텍스트에서는 실제로는 Xcode CLT shim(`/Applications/Xcode.app/Contents/Developer/usr/bin/python3`) 이 호출됨 — macOS 의 `/usr/bin/python3` 자체가 Xcode shim 이기 때문.
- 문제는 Python 바이너리가 아니라 **대상 경로**: `~/Documents/` 는 macOS TCC 보호 영역으로, launchd 데몬 컨텍스트의 Xcode python 바이너리에는 Full Disk Access 가 부여되지 않음.
- FDA 를 Xcode python 에 명시적으로 부여해봐도 launchd 컨텍스트의 TCC 평가는 여전히 차단됨 (캐시·데몬 컨텍스트 특수성).

**해결 — 레포·볼트를 TCC 보호 영역 밖으로 이동 (B2 경로)**
- `~/Documents/projects/jandi-picker/` → `~/dev/jandi-picker/`
- `~/Documents/내거/` → `~/dev/내거/`
- `scripts/publish_til.py` 의 `VAULT_TIL_DIR` 및 `.claude/settings.local.json` 의 Read 권한 패턴을 새 경로로 갱신
- `./scripts/install.sh` 재실행으로 plist 의 모든 경로(`ProgramArguments[1]`, `WorkingDirectory`, `StandardOutPath`, `StandardErrorPath`) 를 새 경로로 재렌더
- 2026-04-23 13:57 `launchctl kickstart` 결과: stderr 에 신규 TCC 에러 0건, stdout 에 `[2026-04-23] 게시 완료` 로그, `TIL: 2026-04-23` 커밋 자동 생성·푸시 완료 (커밋 `17a161d`).

**참고 (가설이 틀린 이유)**
- "시스템 Python 경로 하드핀만으로 충분하다" 가정은 macOS 의 `/usr/bin/python3` → Xcode CLT shim 이라는 사실을 간과함.
- launchd 의 TCC 평가는 터미널 컨텍스트와 분리되어 있어 FDA UI 에서 체크해도 반영되지 않는 엣지가 존재.

---

## 2. 시각 외부화 (install.sh 인자화)

**문제의식**
현재 시각을 바꾸려면 세 곳을 수동으로 수정해야 한다:
- `launchd/com.zephyr.jandi-picker.plist.template` 의 `Hour`/`Minute`
- `sudo pmset repeat ...` 명령의 시각
- `README.md` 의 하드코딩 문자열
- (+ `install.sh` 내부 echo 힌트까지 포함하면 네 곳)

**아이디어**
`install.sh` 가 `--time HH:MM` 인자를 받아:
- 플리스트 템플릿의 `Hour`/`Minute` 까지 `sed` 치환
- 안내 메시지의 `pmset` 명령을 입력한 시각(−2분)으로 렌더
- 단일 진실 원천(인자)에서 모든 파생값이 나오도록

**회수 시점**
시각이 3번째로 바뀔 때, 또는 팀원이 추가되어 온보딩 문서가 필요할 때.

**불확실한 부분**
- `pmset repeat` 는 여전히 `sudo` 가 필요해 스크립트가 직접 실행하기 어려움 — 출력만 렌더하는 선에서 타협 가능
- `MTWRFSU` 요일 지정을 변경 가능하게 할지 (현재는 "매일" 고정)
