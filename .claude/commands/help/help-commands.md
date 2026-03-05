# Help - All Commands

이 프로젝트에서 사용 가능한 모든 커스텀 명령어를 보여줍니다.

---

## 명령어 목록

아래 내용을 그대로 출력하세요:

```
==============================================================
PRD Generator - 커스텀 명령어 목록
==============================================================

[문서 생성 파이프라인]
  입력파일 -> PRD -> TRD -> WBS -> 제안서 -> PPT

  /prd:prd-maker       입력 파일에서 PRD 생성
  /trd:trd-maker       PRD에서 TRD 생성
  /wbs:wbs-maker       PRD+TRD에서 WBS 생성
  /pro:pro-maker       PRD+TRD+WBS에서 제안서 생성
  /ppt:ppt-maker       제안서에서 PPT 생성
  @auto-doc            5종 문서 일괄 생성

[DOCX 변환]
  /doc:doc-maker       전체 DOCX 변환 (PRD+TRD+WBS+제안서)
  /doc:doc-prd         PRD DOCX 변환
  /doc:doc-trd         TRD DOCX 변환
  /doc:doc-wbs         WBS DOCX 변환
  /doc:doc-proposal    제안서 DOCX 변환

[다이어그램]
  /diagram:arch-diagram  TRD에서 아키텍처 다이어그램 PNG 생성

[서버 & 웹]
  /web:dash-board      백엔드+프론트엔드 서버 실행 + 크롬 열기
  /web:api-health      API 서버 헬스체크

[삭제]
  /del:del-input       입력 파일 삭제
  /del:del-doc         출력 문서 삭제
  /del:del-all         전체 초기화 (입력+출력 모두 삭제)

[점검]
  /check:check-status    문서 현황 확인 (파이프라인 진행도)
  /check:check-quality   코드 품질 검사 (Python+Frontend)

[테스트]
  /test:test-run       전체 테스트 실행 및 결과 보고

[의존성]
  /deps:deps-check     Python/Node.js 의존성 점검

[Git]
  /git:git-push        변경사항 커밋 및 푸시
  /git:git-pull        최신 코드 가져오기

[도움말]
  /help:help-commands   이 도움말 표시

==============================================================
팁: 새 프로젝트 시작 시 권장 순서
  1. /del:del-all          (초기화)
  2. 입력 파일 추가         (workspace/inputs/projects/)
  3. @auto-doc             (5종 문서 일괄 생성)
  4. /web:dash-board       (대시보드에서 확인)
==============================================================
```
