# Git Push

현재 프로젝트의 변경사항을 commit하고 GitHub에 push합니다.

## 실행 단계

1. `git status`로 변경사항 확인
2. `git add .`로 모든 변경사항 스테이징
3. 변경사항을 분석하여 적절한 커밋 메시지 생성
4. `git commit`으로 커밋 생성
5. `git push origin`으로 GitHub에 push

## 대상 저장소

- Remote: https://github.com/donseok/prd-generator.git

## 주의사항

- 커밋 메시지는 변경 내용을 분석하여 자동 생성합니다
- push 전에 현재 브랜치를 확인합니다
- 충돌이 발생하면 사용자에게 알립니다
