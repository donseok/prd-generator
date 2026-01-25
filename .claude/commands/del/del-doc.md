# Delete Generated Documents

테스트를 위해 생성된 문서들을 삭제하고 다음 테스트를 준비합니다.

## 목적

프로그램 테스트 과정에서 생성된 PRD, TRD, WBS, Proposal 문서들을 일괄 삭제하여 깨끗한 상태에서 다시 테스트할 수 있도록 합니다.

## 삭제 대상

다음 폴더 내의 모든 파일을 삭제합니다 (`.gitkeep` 파일 제외):

- `workspace/outputs/prd/` - PRD 문서
- `workspace/outputs/trd/` - TRD 문서
- `workspace/outputs/wbs/` - WBS 문서
- `workspace/outputs/proposals/` - 제안서 문서

## 실행 단계

1. 각 폴더의 현재 파일 목록을 확인하고 표시
2. 사용자에게 삭제 확인 요청
3. 확인 후 각 폴더의 파일 삭제 실행 (`.gitkeep` 제외)
4. 삭제 완료 후 결과 보고

## 실행 명령

```bash
# PRD 폴더 정리
find workspace/outputs/prd/ -type f ! -name '.gitkeep' -delete

# TRD 폴더 정리
find workspace/outputs/trd/ -type f ! -name '.gitkeep' -delete

# WBS 폴더 정리
find workspace/outputs/wbs/ -type f ! -name '.gitkeep' -delete

# Proposals 폴더 정리
find workspace/outputs/proposals/ -type f ! -name '.gitkeep' -delete
```

## 주의사항

- 삭제된 파일은 복구할 수 없습니다
- 실행 전 반드시 삭제할 파일 목록을 확인합니다
- `.gitkeep` 파일은 폴더 유지를 위해 보존합니다
