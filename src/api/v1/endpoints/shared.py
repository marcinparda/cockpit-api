from typing import Any
import io
import tempfile
import os

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field
from PIL import Image
import pytesseract

from src.auth.enums.actions import Actions
from src.auth.permission_helpers import get_shared_permissions

router = APIRouter()


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


@router.post(
    "/ocr",
    response_model=OCRResponse,
    responses={
        400: {
            "description": "Bad Request - Invalid file format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File must be an image (JPEG, PNG, TIFF, BMP, etc.)"
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - Image processing failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error processing image: [specific error message]"
                    }
                }
            }
        }
    }
)
async def extract_text_from_image(
    file: UploadFile = File(...),
    _: None = Depends(get_shared_permissions(Actions.READ))
) -> OCRResponse:
    """
    Extract text from an uploaded image using OCR (Optical Character Recognition).

    This endpoint accepts image files in common formats (JPEG, PNG, TIFF, BMP, etc.)
    and uses Tesseract OCR to extract text content from the image.

    The extracted text is automatically cleaned by removing extra whitespace
    and empty lines for better readability.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPEG, PNG, TIFF, BMP, etc.)"
        )

    try:
        # Read the uploaded file
        contents = await file.read()

        # Create a temporary file to store the image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            # Open image with PIL
            image = Image.open(io.BytesIO(contents))

            # Convert to RGB if necessary (for JPEG with transparency or other formats)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Convert to RGB
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()
                                [-1] if image.mode == 'RGBA' else None)
                image = rgb_image

            # Save the image to temporary file
            image.save(temp_file.name, format='PNG')
            temp_file_path = temp_file.name

        try:
            # Extract text using pytesseract
            extracted_text = pytesseract.image_to_string(temp_file_path)

            # Clean up the extracted text (remove extra whitespace)
            cleaned_text = '\n'.join(
                line.strip() for line in extracted_text.split('\n') if line.strip())

            return OCRResponse(
                success=True,
                extracted_text=cleaned_text,
                filename=file.filename,
                content_type=file.content_type
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )
