# jandi-picker

Obsidian TIL 노트를 매일 16:30에 자동으로 이 레포에 게시해서 GitHub 잔디를 심는 자동화.

## 동작

1. `pmset` 이 16:28에 맥을 깨움
2. `launchd` 가 16:30에 `scripts/publish_til.py` 실행
3. 스크립트가 오늘자 Obsidian TIL 노트를 찾아 **제목 / 요약 / 학습 토픽** 만 추출
4. `TIL/YYYY/MM/YYYY-MM-DD.md` 로 게시, `TIL: YYYY-MM-DD` 커밋 후 push

재실행해도 같은 날짜 파일이 이미 있으면 skip (안전).

## 설치

```bash
./scripts/install.sh
sudo pmset repeat wakeorpoweron MTWRFSU 16:28:00
```

### Windows

`launchd` + `pmset` 대신 작업 스케줄러를 쓴다 (절전 해제는 작업의 `WakeToRun` 옵션).

```powershell
winget install Python.Python.3.12        # Python 이 없을 때만
powershell -ExecutionPolicy Bypass -File scripts\install.ps1            # 기본 16:30
powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Time 18:00
```

- 볼트 TIL 경로 기본값은 `%USERPROFILE%\Documents\TIL\TIL`. 다른 위치면 환경변수 `JANDI_VAULT_TIL_DIR` 로 지정.
- 예약 시각에 PC 가 꺼져 있었으면 다음에 켜질 때 실행된다 (`StartWhenAvailable`).
- 로그인된 사용자 세션에서 실행되므로 push 인증은 Git Credential Manager 를 그대로 쓴다.

```powershell
Get-ScheduledTask jandi-picker | Get-ScheduledTaskInfo   # 등록·마지막 실행 결과
Start-ScheduledTask jandi-picker                         # 수동 실행
Get-Content logs\stdout.log -Tail 20 -Encoding UTF8      # 실행 로그
Unregister-ScheduledTask jandi-picker -Confirm:$false    # 제거
```

## 추출 규칙

| 항목 | 출처 |
|---|---|
| 제목 | 프론트매터 `title` |
| 요약 | `## 📌 오늘의 주제` 섹션의 `>` blockquote |
| 학습 토픽 | `### 개념` 하위 0~1단계 들여쓰기 bullet |

TIL 파일이 없거나 내용이 비어있는 날도 **제목만** 올려 잔디를 유지한다.

### 비공개 노트

`업무` / `회사` / `비공개` 태그(프론트매터 `tags` 또는 본문 `#태그`)가 붙은 노트는 회사 자료로 보고 제목을 포함해 아무 내용도 게시하지 않는다. 같은 날짜에 태그 없는 노트가 있으면 그것을 게시하고, 전부 비공개면 날짜만 올린다. 태그 목록은 `publish_til.py` 의 `PRIVATE_TAGS`.

### 빠진 날짜 채우기

```bash
python scripts/publish_til.py 2026-10-02   # 해당 날짜 16:30 으로 커밋
```

## 확인 명령

```bash
pmset -g sched                            # wake 스케줄
launchctl list | grep jandi               # launchd 등록
tail -f logs/stdout.log logs/stderr.log   # 실행 로그
/usr/bin/python3 scripts/publish_til.py   # 수동 실행
```
