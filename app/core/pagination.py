from app.core.config import settings


def normalize_pagination(page: int = 1, page_size: int | None = None) -> tuple[int, int, int]:
    page = max(1, int(page or 1))
    requested_size = settings.DEFAULT_PAGE_SIZE if page_size is None else int(page_size or settings.DEFAULT_PAGE_SIZE)
    page_size = max(1, min(requested_size, settings.MAX_PAGE_SIZE))
    offset = (page - 1) * page_size
    return page, page_size, offset


def build_paginated_response(items, total: int, page: int, page_size: int) -> dict:
    return {
        "items": list(items),
        "total": int(total or 0),
        "page": int(page),
        "page_size": int(page_size),
    }
