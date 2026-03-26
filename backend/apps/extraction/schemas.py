from pydantic import BaseModel, Field


class ClaimItem(BaseModel):
    claim_type: str = Field(...)
    claim_text: str = Field(...)
    extraction_confidence: float = Field(...)


class ExtractionResult(BaseModel):
    claims: list[ClaimItem]
