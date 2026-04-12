from pydantic import BaseModel
from typing import Optional

class ExportResponse(BaseModel):
    download_url: str
    format: str
