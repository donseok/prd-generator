"""PRD document endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models import PRDDocument
from app.services import get_file_storage

router = APIRouter()


@router.get("/{prd_id}")
async def get_prd(prd_id: str) -> dict:
    """Get PRD document by ID."""
    storage = get_file_storage()
    prd = await storage.get_prd(prd_id)

    if not prd:
        raise HTTPException(status_code=404, detail="PRD를 찾을 수 없습니다")

    return prd.model_dump()


@router.get("/{prd_id}/export")
async def export_prd(
    prd_id: str,
    format: str = "markdown"
) -> Response:
    """
    Export PRD in specified format.

    Supported formats: markdown, json, html
    """
    storage = get_file_storage()
    prd = await storage.get_prd(prd_id)

    if not prd:
        raise HTTPException(status_code=404, detail="PRD를 찾을 수 없습니다")

    if format == "markdown":
        content = prd.to_markdown()
        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{prd.title}.md"'
            }
        )
    elif format == "json":
        content = prd.model_dump_json(indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{prd.title}.json"'
            }
        )
    elif format == "html":
        # Generate HTML from markdown
        md_content = prd.to_markdown()
        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{prd.title}</title>
    <style>
        body {{ font-family: 'Pretendard', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a1a1a; border-bottom: 2px solid #e5e5e5; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        h3 {{ color: #555; }}
        pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        code {{ background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }}
        .confidence {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
<pre>{md_content}</pre>
</body>
</html>"""
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f'attachment; filename="{prd.title}.html"'
            }
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 형식입니다: {format}"
        )


@router.get("")
async def list_prds(
    skip: int = 0,
    limit: int = 20,
    status: str = None
) -> dict:
    """List all PRD documents with pagination."""
    storage = get_file_storage()
    prds = await storage.list_prds(skip=skip, limit=limit, status=status)

    return {
        "total": len(prds),
        "prds": [
            {
                "id": prd.id,
                "title": prd.title,
                "status": prd.metadata.status,
                "overall_confidence": prd.metadata.overall_confidence,
                "requires_pm_review": prd.metadata.requires_pm_review,
                "created_at": prd.metadata.created_at.isoformat() if prd.metadata.created_at else None,
                "requirements_count": (
                    len(prd.functional_requirements) +
                    len(prd.non_functional_requirements) +
                    len(prd.constraints)
                ),
            }
            for prd in prds
        ],
    }


@router.delete("/{prd_id}")
async def delete_prd(prd_id: str) -> dict:
    """Delete a PRD document."""
    storage = get_file_storage()

    deleted = await storage.delete_prd(prd_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="PRD를 찾을 수 없습니다")

    return {"message": "PRD가 삭제되었습니다", "id": prd_id}
