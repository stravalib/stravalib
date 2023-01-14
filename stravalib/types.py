from typing import Dict, TypedDict


class PhotoData(TypedDict):
    uri: str  # S3 pre-signed URI
    header: Dict  # Content-Type, Content-Length, etc.
    method: str  # HTTP method PUT
    max_size: int
