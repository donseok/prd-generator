"""
엑셀(.xlsx) 및 CSV 파일 파서입니다.
Pandas 라이브러리를 사용하여 데이터를 읽고 표 형태로 변환합니다.
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser
from ..prompts.parsing_prompts import EXCEL_PARSING_PROMPT


class ExcelParser(BaseParser):
    """Excel 및 CSV 데이터를 처리하는 파서입니다."""

    @property
    def supported_types(self) -> list[InputType]:
        return [InputType.EXCEL, InputType.CSV]

    @property
    def supported_extensions(self) -> list[str]:
        return [".xlsx", ".xls", ".csv"]

    async def parse(
        self,
        file_path: Path,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """파일 내용을 읽어서 구조화된 데이터로 변환합니다."""
        ext = file_path.suffix.lower()

        # 파일 형식에 따라 Pandas로 읽기
        if ext == ".csv":
            df_dict = {"Sheet1": pd.read_csv(file_path)}
            sheet_names = ["Sheet1"]
        else:
            # 엑셀 파일은 모든 시트를 읽음
            xlsx = pd.ExcelFile(file_path)
            sheet_names = xlsx.sheet_names
            df_dict = {name: pd.read_excel(xlsx, sheet_name=name) for name in sheet_names}

        # 텍스트 형태의 통합 본문 생성 (마크다운 표 형식)
        raw_text = self._build_raw_text(df_dict)

        # 구조 정보 추출 (컬럼명, 데이터 타입 등)
        structured_data = self._extract_structured_data(df_dict)

        # 메타데이터 생성
        file_metadata = await self.extract_metadata(file_path)
        file_metadata.sheet_names = sheet_names

        # 시트별 섹션 생성
        sections = []
        for sheet_name, df in df_dict.items():
            sections.append({
                "title": sheet_name,
                "content": df.to_string(),
                "columns": list(df.columns),
                "row_count": len(df),
            })

        # AI(Claude) 분석 (가능한 경우)
        if self.claude_client:
            try:
                analysis = await self._analyze_with_claude(raw_text)
                structured_data["ai_analysis"] = analysis
            except Exception as e:
                print(f"Claude 엑셀 분석 실패: {e}")

        return ParsedContent(
            raw_text=raw_text,
            structured_data=structured_data,
            metadata=file_metadata,
            sections=sections,
        )

    def _build_raw_text(self, df_dict: dict) -> str:
        """모든 시트의 데이터를 하나의 텍스트로 합칩니다."""
        parts = []

        for sheet_name, df in df_dict.items():
            parts.append(f"=== 시트: {sheet_name} ===")
            parts.append(f"컬럼: {', '.join(df.columns.astype(str))}")
            parts.append(f"행 수: {len(df)}")
            parts.append("")

            # 마크다운 표 형식으로 변환 (읽기 좋게)
            parts.append(df.to_markdown(index=False) if hasattr(df, 'to_markdown') else df.to_string())
            parts.append("")

        return "\n".join(parts)

    def _extract_structured_data(self, df_dict: dict) -> dict:
        """데이터의 통계 정보를 추출합니다."""
        sheets_info = {}

        for sheet_name, df in df_dict.items():
            # 컬럼별 정보 분석
            columns_info = []
            for col in df.columns:
                col_data = df[col]
                col_info = {
                    "name": str(col),
                    "dtype": str(col_data.dtype),
                    "non_null_count": int(col_data.notna().sum()),
                    "unique_count": int(col_data.nunique()),
                }

                # 샘플 데이터 5개 추출
                sample = col_data.dropna().head(5).tolist()
                col_info["sample_values"] = [str(v) for v in sample]

                # 요구사항 관련 컬럼인지 추측 (키워드 매칭)
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in
                       ["요구", "기능", "설명", "description", "requirement", "feature", "우선", "priority"]):
                    col_info["is_requirement_related"] = True

                columns_info.append(col_info)

            sheets_info[sheet_name] = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": columns_info,
            }

        return {
            "sheet_count": len(df_dict),
            "sheets": sheets_info,
        }

    async def _analyze_with_claude(self, raw_text: str) -> dict:
        """Claude에게 엑셀 데이터 분석을 요청합니다 (요구사항 추출 용도)."""
        result = await self.claude_client.complete_json(
            system_prompt=EXCEL_PARSING_PROMPT,
            user_prompt=f"다음 엑셀 데이터를 분석해주세요:\n\n{raw_text[:8000]}",
            temperature=0.2,
        )
        return result