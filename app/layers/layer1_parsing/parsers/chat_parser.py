"""Chat/Messenger log parser."""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from app.models import InputType, ParsedContent, InputMetadata
from ..base_parser import BaseParser
from ..prompts.parsing_prompts import CHAT_PARSING_PROMPT


class ChatParser(BaseParser):
    """Parser for chat/messenger conversation logs."""

    @property
    def supported_types(self) -> list[InputType]:
        return [InputType.CHAT]

    @property
    def supported_extensions(self) -> list[str]:
        return [".json", ".txt"]

    async def parse(
        self,
        file_path: Path,
        metadata: Optional[dict] = None
    ) -> ParsedContent:
        """Parse chat log file."""
        ext = file_path.suffix.lower()

        # Read file
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Parse based on format
        if ext == ".json":
            messages = self._parse_json_chat(content)
        else:
            messages = self._parse_text_chat(content)

        # Build raw text
        raw_text = self._build_raw_text(messages)

        # Extract participants
        participants = list(set(m.get("sender", "Unknown") for m in messages))

        # Build metadata
        file_metadata = await self.extract_metadata(file_path)
        file_metadata.participants = participants

        # Build structured data
        structured_data = {
            "message_count": len(messages),
            "participants": participants,
            "messages": messages[:100],  # Limit for storage
        }

        # Use Claude for intelligent analysis
        if self.claude_client:
            try:
                analysis = await self._analyze_with_claude(raw_text)
                structured_data["ai_analysis"] = analysis
            except Exception as e:
                print(f"Claude chat analysis failed: {e}")

        # Build sections
        sections = self._build_sections(messages)

        return ParsedContent(
            raw_text=raw_text,
            structured_data=structured_data,
            metadata=file_metadata,
            sections=sections,
        )

    def _parse_json_chat(self, content: str) -> list:
        """Parse JSON format chat export (common for Slack, Discord, etc.)."""
        try:
            data = json.loads(content)

            # Handle different JSON structures
            if isinstance(data, list):
                messages = data
            elif isinstance(data, dict):
                # Try common keys
                for key in ["messages", "data", "conversations", "chat"]:
                    if key in data:
                        messages = data[key]
                        break
                else:
                    messages = [data]
            else:
                return []

            # Normalize message format
            normalized = []
            for msg in messages:
                if isinstance(msg, dict):
                    normalized.append({
                        "sender": msg.get("sender") or msg.get("user") or msg.get("from") or msg.get("author") or "Unknown",
                        "content": msg.get("content") or msg.get("text") or msg.get("message") or str(msg),
                        "timestamp": msg.get("timestamp") or msg.get("time") or msg.get("date") or "",
                    })
                elif isinstance(msg, str):
                    normalized.append({
                        "sender": "Unknown",
                        "content": msg,
                        "timestamp": "",
                    })

            return normalized

        except json.JSONDecodeError:
            return self._parse_text_chat(content)

    def _parse_text_chat(self, content: str) -> list:
        """Parse plain text chat format."""
        messages = []
        lines = content.split("\n")

        # Common patterns for chat logs
        import re
        patterns = [
            # [timestamp] sender: message
            r'\[([^\]]+)\]\s*([^:]+):\s*(.+)',
            # timestamp - sender: message
            r'(\d{4}[-/]\d{2}[-/]\d{2}[T\s]\d{2}:\d{2}(?::\d{2})?)\s*[-–]\s*([^:]+):\s*(.+)',
            # sender (timestamp): message
            r'([^(]+)\s*\(([^)]+)\):\s*(.+)',
            # Simple: sender: message
            r'^([^:]{1,30}):\s*(.+)$',
        ]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            matched = False
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        messages.append({
                            "timestamp": groups[0],
                            "sender": groups[1].strip(),
                            "content": groups[2].strip(),
                        })
                    elif len(groups) == 2:
                        messages.append({
                            "sender": groups[0].strip(),
                            "content": groups[1].strip(),
                            "timestamp": "",
                        })
                    matched = True
                    break

            if not matched and line:
                # Append to previous message or create new
                if messages:
                    messages[-1]["content"] += "\n" + line
                else:
                    messages.append({
                        "sender": "Unknown",
                        "content": line,
                        "timestamp": "",
                    })

        return messages

    def _build_raw_text(self, messages: list) -> str:
        """Build raw text from messages."""
        parts = []
        for msg in messages:
            timestamp = f"[{msg['timestamp']}] " if msg.get('timestamp') else ""
            parts.append(f"{timestamp}{msg['sender']}: {msg['content']}")
        return "\n".join(parts)

    def _build_sections(self, messages: list) -> list:
        """Build sections from messages (group by topic/time)."""
        if not messages:
            return []

        # Simple approach: group by time gaps or topic changes
        sections = []
        current_section = {
            "title": "대화 시작",
            "messages": [],
        }

        for msg in messages:
            current_section["messages"].append(msg)

            # Start new section every 20 messages (simple heuristic)
            if len(current_section["messages"]) >= 20:
                sections.append({
                    "title": current_section["title"],
                    "content": "\n".join([
                        f"{m['sender']}: {m['content']}"
                        for m in current_section["messages"]
                    ]),
                })
                current_section = {
                    "title": f"대화 계속 ({len(sections) + 1})",
                    "messages": [],
                }

        # Add remaining messages
        if current_section["messages"]:
            sections.append({
                "title": current_section["title"],
                "content": "\n".join([
                    f"{m['sender']}: {m['content']}"
                    for m in current_section["messages"]
                ]),
            })

        return sections

    async def _analyze_with_claude(self, raw_text: str) -> dict:
        """Use Claude to analyze chat for requirements."""
        result = await self.claude_client.complete_json(
            system_prompt=CHAT_PARSING_PROMPT,
            user_prompt=f"다음 대화 내용을 분석해주세요:\n\n{raw_text[:8000]}",
            temperature=0.2,
        )
        return result
