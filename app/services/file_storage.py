"""
파일 기반 저장소 서비스입니다.
데이터베이스 대신 파일 시스템(폴더와 파일)을 사용하여 데이터를 저장하고 관리합니다.

관리하는 데이터:
1. PRD 문서 (JSON 파일)
2. 작업 상태 정보 (Jobs)
3. 업로드된 파일들 (Uploads)
4. 프로젝트 (Projects) - 여러 문서를 묶어 관리
"""

import json
import logging
import os
import re
import shutil
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional, TypeVar, Type
from pydantic import BaseModel

from app.models import PRDDocument, ProcessingJob, InputDocument, Project
from app.exceptions import StorageError

logger = logging.getLogger(__name__)


T = TypeVar("T", bound=BaseModel)


class FileStorage:
    """JSON 파일 기반의 단순 저장소 클래스입니다."""

    # ID에 허용되는 문자 패턴 (경로 탐색 방지)
    _SAFE_ID_CHARS = re.compile(r'^[A-Za-z0-9가-힣_\-]+$')

    def __init__(self, base_path: str = "data"):
        # 기본 저장 경로 설정 (기본값: data 폴더)
        self.base_path = Path(base_path)
        self.prd_path = self.base_path / "prd"
        self.jobs_path = self.base_path / "jobs"
        self.uploads_path = self.base_path / "uploads"
        self.projects_path = self.base_path / "projects"

        # 필요한 폴더들이 없으면 만듭니다.
        self._ensure_directories()

    def _validate_id(self, id_value: str, label: str = "ID") -> str:
        """ID 값의 경로 탐색 문자를 검증합니다."""
        if not id_value or not self._SAFE_ID_CHARS.match(id_value):
            raise StorageError(f"유효하지 않은 {label}입니다: {id_value}")
        return id_value

    def _ensure_directories(self):
        """저장소 폴더 생성 함수"""
        for path in [self.prd_path, self.jobs_path, self.uploads_path, self.projects_path]:
            path.mkdir(parents=True, exist_ok=True)

    # ==================== PRD 문서 관련 기능 ====================

    async def save_prd(self, prd: PRDDocument) -> str:
        """PRD 문서를 파일로 저장합니다."""
        file_path = self.prd_path / f"{prd.id}.json"
        await self._save_model(file_path, prd)
        return prd.id

    async def get_prd(self, prd_id: str) -> Optional[PRDDocument]:
        """ID로 PRD 문서를 불러옵니다."""
        self._validate_id(prd_id, "PRD ID")
        file_path = self.prd_path / f"{prd_id}.json"
        return await self._load_model(file_path, PRDDocument)

    async def list_prds(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> list[PRDDocument]:
        """
        저장된 PRD 목록을 페이지 단위로 가져옵니다.
        최신 수정된 순서대로 정렬됩니다.
        """
        prds = []
        # 파일들을 수정 시간 역순(최신순)으로 정렬
        files = sorted(
            self.prd_path.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        for file_path in files:
            prd = await self._load_model(file_path, PRDDocument)
            if prd:
                # 상태 필터가 있으면 해당 상태의 문서만 포함
                if status is None or prd.metadata.status == status:
                    prds.append(prd)

        # 페이지네이션 (원하는 범위만 자르기)
        return prds[skip:skip + limit]

    async def delete_prd(self, prd_id: str) -> bool:
        """PRD 문서를 삭제합니다."""
        file_path = self.prd_path / f"{prd_id}.json"
        return self._delete_file(file_path)

    async def update_prd(self, prd: PRDDocument) -> bool:
        """기존 PRD 문서를 업데이트합니다."""
        file_path = self.prd_path / f"{prd.id}.json"
        if not file_path.exists():
            return False
        prd.metadata.updated_at = datetime.now()
        await self._save_model(file_path, prd)
        return True

    # ==================== 작업(Job) 상태 관련 기능 ====================

    async def save_job(self, job: ProcessingJob) -> str:
        """작업 상태 정보를 저장합니다."""
        file_path = self.jobs_path / f"{job.job_id}.json"
        await self._save_model(file_path, job)
        return job.job_id

    async def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """작업 ID로 상태 정보를 조회합니다."""
        self._validate_id(job_id, "Job ID")
        file_path = self.jobs_path / f"{job_id}.json"
        return await self._load_model(file_path, ProcessingJob)

    async def update_job(self, job: ProcessingJob) -> bool:
        """작업 상태를 업데이트합니다."""
        file_path = self.jobs_path / f"{job.job_id}.json"
        job.updated_at = datetime.now()
        await self._save_model(file_path, job)
        return True

    async def list_jobs(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> list[ProcessingJob]:
        """작업 목록을 페이지 단위로 조회합니다."""
        jobs = []
        files = sorted(
            self.jobs_path.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        for file_path in files:
            job = await self._load_model(file_path, ProcessingJob)
            if job:
                if status is None or job.status.value == status:
                    jobs.append(job)

        return jobs[skip:skip + limit]

    async def delete_job(self, job_id: str) -> bool:
        """작업 정보를 삭제합니다."""
        file_path = self.jobs_path / f"{job_id}.json"
        return self._delete_file(file_path)

    # ==================== 파일 업로드 관련 기능 ====================

    async def save_upload(
        self,
        file_content: bytes,
        filename: str,
        document_id: str
    ) -> str:
        """
        업로드된 파일을 디스크에 저장합니다.
        문서 ID별로 별도의 폴더에 저장됩니다.
        """
        self._validate_id(document_id, "Document ID")
        # 파일명에서 경로 탐색 문자 제거
        safe_filename = Path(filename).name
        filename = safe_filename
        # 문서별 폴더 생성
        doc_dir = self.uploads_path / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        file_path = doc_dir / filename
        # 파일 쓰기 (비동기)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        # 저장된 파일의 절대 경로 반환
        return str(file_path.resolve())

    async def get_upload(self, document_id: str, filename: str) -> Optional[bytes]:
        """저장된 파일의 내용을 읽어옵니다."""
        file_path = self.uploads_path / document_id / filename
        if not file_path.exists():
            return None

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete_upload(self, document_id: str) -> bool:
        """특정 문서와 관련된 모든 업로드 파일을 삭제합니다."""
        doc_dir = self.uploads_path / document_id
        if doc_dir.exists():
            shutil.rmtree(doc_dir)  # 폴더 채로 삭제
            return True
        return False

    def get_upload_path(self, document_id: str, filename: str) -> Path:
        """업로드된 파일의 경로를 반환합니다."""
        return self.uploads_path / document_id / filename

    # ==================== 프로젝트 관련 기능 ====================

    async def save_project(self, project: Project) -> str:
        """프로젝트를 파일로 저장합니다."""
        file_path = self.projects_path / f"{project.id}.json"
        await self._save_model(file_path, project)
        return project.id

    async def get_project(self, project_id: str) -> Optional[Project]:
        """ID로 프로젝트를 불러옵니다."""
        self._validate_id(project_id, "Project ID")
        file_path = self.projects_path / f"{project_id}.json"
        return await self._load_model(file_path, Project)

    async def list_projects(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> list[Project]:
        """
        저장된 프로젝트 목록을 페이지 단위로 가져옵니다.
        최신 수정된 순서대로 정렬됩니다.
        """
        projects = []
        # 파일들을 수정 시간 역순(최신순)으로 정렬
        files = sorted(
            self.projects_path.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        for file_path in files:
            project = await self._load_model(file_path, Project)
            if project:
                # 상태 필터가 있으면 해당 상태의 프로젝트만 포함
                if status is None or project.status == status:
                    projects.append(project)

        # 페이지네이션 (원하는 범위만 자르기)
        return projects[skip : skip + limit]

    async def update_project(self, project: Project) -> bool:
        """기존 프로젝트를 업데이트합니다."""
        file_path = self.projects_path / f"{project.id}.json"
        if not file_path.exists():
            return False
        project.updated_at = datetime.now()
        await self._save_model(file_path, project)
        return True

    async def delete_project(self, project_id: str) -> bool:
        """프로젝트를 삭제합니다."""
        file_path = self.projects_path / f"{project_id}.json"
        return self._delete_file(file_path)

    async def count_projects(self, status: Optional[str] = None) -> int:
        """프로젝트 총 개수를 반환합니다."""
        count = 0
        for file_path in self.projects_path.glob("*.json"):
            if status is None:
                count += 1
            else:
                project = await self._load_model(file_path, Project)
                if project and project.status == status:
                    count += 1
        return count

    # ==================== 입력 문서 메타데이터 기능 ====================

    async def save_input_document(self, doc: InputDocument) -> str:
        """입력 문서의 정보를 저장합니다."""
        doc_dir = self.uploads_path / doc.id
        doc_dir.mkdir(parents=True, exist_ok=True)
        file_path = doc_dir / "metadata.json"
        await self._save_model(file_path, doc)
        return doc.id

    async def get_input_document(self, document_id: str) -> Optional[InputDocument]:
        """입력 문서 정보를 조회합니다."""
        file_path = self.uploads_path / document_id / "metadata.json"
        return await self._load_model(file_path, InputDocument)

    # ==================== 내부 도우미 함수들 ====================

    async def _save_model(self, file_path: Path, model: BaseModel):
        """데이터 모델을 JSON 파일로 저장하는 공통 함수"""
        try:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(model.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"파일 저장 실패 {file_path}: {e}", exc_info=True)
            raise StorageError(
                f"파일 저장에 실패했습니다: {file_path.name}",
                details={"path": str(file_path), "error": str(e)},
            )

    async def _load_model(self, file_path: Path, model_class: Type[T]) -> Optional[T]:
        """JSON 파일을 읽어서 데이터 모델로 변환하는 공통 함수"""
        if not file_path.exists():
            return None

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return model_class.model_validate_json(content)
        except Exception as e:
            logger.error(f"파일 로딩 에러 {file_path}: {e}", exc_info=True)
            return None

    def _delete_file(self, file_path: Path) -> bool:
        """파일 삭제 공통 함수"""
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# 싱글톤 인스턴스 (프로그램 전체에서 공유)
_file_storage: Optional[FileStorage] = None


def get_file_storage() -> FileStorage:
    """FileStorage 인스턴스를 반환합니다."""
    global _file_storage
    if _file_storage is None:
        _file_storage = FileStorage()
    return _file_storage