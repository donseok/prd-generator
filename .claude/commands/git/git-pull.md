# Git Pull

원격 저장소(GitHub)에서 최신 변경사항을 pull합니다.

## 실행 단계

1. `git status`로 현재 작업 상태 확인
2. 커밋되지 않은 변경사항이 있으면 사용자에게 알림
3. `git fetch`로 원격 변경사항 확인
4. `git pull origin`으로 최신 코드를 가져옴

## 대상 저장소

- Remote: https://github.com/donseok/prd-generator.git

## 주의사항

- pull 전에 현재 브랜치를 확인합니다
- 로컬 변경사항이 있으면 stash 또는 commit 여부를 확인합니다
- 충돌이 발생하면 사용자에게 알립니다
