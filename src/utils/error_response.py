from typing import Dict, Any

ERROR_RESPONSES: Dict[int | str, Dict[str, Any]] = {
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Invalid token"}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Missing Authorization header"}}}}
}