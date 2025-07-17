from pydantic import BaseModel, Field


class OCRResponse(BaseModel):
    """Response model for OCR text extraction."""

    success: bool = Field(
        description="Indicates whether the OCR operation was successful"
    )
    extracted_text: str = Field(
        description="The text extracted from the image, cleaned and formatted"
    )
    filename: str | None = Field(
        description="The original filename of the uploaded image"
    )
    content_type: str = Field(
        description="The MIME type of the uploaded image file"
    )
