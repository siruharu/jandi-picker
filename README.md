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

## 추출 규칙

| 항목 | 출처 |
|---|---|
| 제목 | 프론트매터 `title` |
| 요약 | `## 📌 오늘의 주제` 섹션의 `>` blockquote |
| 학습 토픽 | `### 개념` 하위 0~1단계 들여쓰기 bullet |

TIL 파일이 없거나 내용이 비어있는 날도 **제목만** 올려 잔디를 유지한다.

## 확인 명령

```bash
pmset -g sched                            # wake 스케줄
launchctl list | grep jandi               # launchd 등록
tail -f logs/stdout.log logs/stderr.log   # 실행 로그
/usr/bin/python3 scripts/publish_til.py   # 수동 실행
```
