# Backlog

본 레포 범위에서 당장 다루지 않고 미뤄둔 후속 항목들.

## 1. stderr `Operation not permitted` 원인 규명 및 가설 검증

**증상**
`logs/stderr.log` 에 다음 에러가 반복적으로 기록되어 있었음:

```
/Applications/Xcode.app/Contents/Developer/usr/bin/python3: can't open file '/Users/zephyr/Documents/projects/jandi-picker/scripts/publish_til.py': [Errno 1] Operation not permitted
```

**현재까지 파악**
- 에러 경로는 Xcode 번들 내부 python3 (`/Applications/Xcode.app/Contents/Developer/usr/bin/python3`)
- 현 `install.sh` 는 `/usr/bin/python3` 로 하드핀 — 과거 설치 시점엔 하드핀이 없어 Xcode python 이 잡혔을 가능성
- launchd 컨텍스트는 사용자 터미널과 보안 컨텍스트가 달라, Xcode 내부 바이너리가 사용자 디렉터리 스크립트를 여는 데 Full Disk Access 가 필요
- 2026-04-22 15:40 `install.sh` 재실행으로 plist 의 Python 경로가 `/usr/bin/python3` 로 갱신됨
- 동일 시점 `/usr/bin/python3 scripts/publish_til.py` 수동 실행은 성공 (exit 0, commit/push 완료)

**가설**
Python 경로가 시스템 `/usr/bin/python3` 로 고정된 이상, launchd 자동 실행도 더 이상 *Operation not permitted* 으로 실패하지 않는다.

**검증 방법**
- 2026-04-22 16:30 이후 `tail -n 20 logs/stdout.log logs/stderr.log` 확인
  - `stderr.log` 에 새 타임스탬프의 에러가 **추가되지 않으면** 가설 성립
  - 오늘은 수동 실행으로 오늘자 TIL 파일이 이미 커밋됐으므로, 스크립트는 "skip" 경로를 탈 것 → `stdout.log` 에 skip 로그만 기록되면 정상
- 2026-04-23 아침 한 번 더 확인 (새 하루, skip 아닌 정상 경로)

**티켓을 닫는 조건**
- 위 검증에서 가설이 맞으면 원인·해결을 README 또는 별도 노트에 기록하고 닫음
- 가설이 틀리면 Full Disk Access 설정을 System Settings → Privacy & Security 에서 `/usr/bin/python3` 또는 launchd 대상으로 부여하는 방안 검토

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
