"""Excel and CSV file parser."""

from pathlib import Path
from typing import Optional
import pandas as pd

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser
from ..prompts.parsing_prompts import EXCEL_PARSING_PROMPT


class ExcelParser(BaseParser):
    """Parser for Excel and CSV files."""

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
        """Parse Excel/CSV file and extract structured content."""
        ext = file_path.suffix.lower()

        # Read file based on type
        if ext == ".csv":
            df_dict = {"Sheet1": pd.read_csv(file_path)}
            sheet_names = ["Sheet1"]
        else:
            # Excel file - read all sheets
            xlsx = pd.ExcelFile(file_path)
            sheet_names = xlsx.sheet_names
            df_dict = {name: pd.read_excel(xlsx, sheet_name=name) for name in sheet_names}

        # Build raw text representation
        raw_text = self._build_raw_text(df_dict)

        # Extract structured data
        structured_data = self._extract_structured_data(df_dict)

        # Build metadata
        file_metadata = await self.extract_metadata(file_path)
        file_metadata.sheet_names = sheet_names

        # Build sections (one per sheet)
        sections = []
        for sheet_name, df in df_dict.items():
            sections.append({
                "title": sheet_name,
                "content": df.to_string(),
                "columns": list(df.columns),
                "row_count": len(df),
            })

        # Use Claude for intelligent analysis if available
        if self.claude_client:
            try:
                analysis = await self._analyze_with_claude(raw_text)
                structured_data["ai_analysis"] = analysis
            except Exception as e:
                print(f"Claude Excel analysis failed: {e}")

        return ParsedContent(
            raw_text=raw_text,
            structured_data=structured_data,
            metadata=file_metadata,
            sections=sections,
        )

    def _build_raw_text(self, df_dict: dict) -> str:
        """Build raw text from dataframes."""
        parts = []

        for sheet_name, df in df_dict.items():
            parts.append(f"=== 시트: {sheet_name} ===")
            parts.append(f"컬럼: {', '.join(df.columns.astype(str))}")
            parts.append(f"행 수: {len(df)}")
            parts.append("")

            # Convert to markdown table format
            parts.append(df.to_markdown(index=False) if hasattr(df, 'to_markdown') else df.to_string())
            parts.append("")

        return "\n".join(parts)

    def _extract_structured_data(self, df_dict: dict) -> dict:
        """Extract structured data from dataframes."""
        sheets_info = {}

        for sheet_name, df in df_dict.items():
            # Analyze columns
            columns_info = []
            for col in df.columns:
                col_data = df[col]
                col_info = {
                    "name": str(col),
                    "dtype": str(col_data.dtype),
                    "non_null_count": int(col_data.notna().sum()),
                    "unique_count": int(col_data.nunique()),
                }

                # Sample values
                sample = col_data.dropna().head(5).tolist()
                col_info["sample_values"] = [str(v) for v in sample]

                # Detect potential requirement-related columns
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
        """Use Claude to analyze Excel content for requirements."""
        result = await self.claude_client.complete_json(
            system_prompt=EXCEL_PARSING_PROMPT,
            user_prompt=f"다음 엑셀 데이터를 분석해주세요:\n\n{raw_text[:8000]}",
            temperature=0.2,
        )
        return result
