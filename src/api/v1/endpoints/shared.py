from typing import Any
import io
import tempfile
import os
import numpy as np
import cv2

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

from src.auth.enums.actions import Actions
from src.auth.permission_helpers import get_shared_permissions
from src.schemas.ocr import OCRResponse

router = APIRouter()


def preprocess_receipt_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image specifically for receipt OCR to improve text recognition.

    Applies various enhancement techniques including:
    - Noise reduction
    - Contrast enhancement
    - Sharpening
    - Deskewing
    - Binarization
    """
    # Convert PIL Image to OpenCV format
    img_array = np.array(image)
    if len(img_array.shape) == 3:
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    else:
        img_cv = img_array

    # Convert to grayscale
    if len(img_cv.shape) == 3:
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_cv

    # Apply noise reduction
    denoised = cv2.medianBlur(gray, 3)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)

    # Apply sharpening kernel
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(blurred, -1, kernel)

    # Apply adaptive threshold for binarization
    # This works better than simple threshold for receipts with varying lighting
    binary = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Morphological operations to clean up the image
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    # Convert back to PIL Image
    return Image.fromarray(cleaned)


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
    and uses Tesseract OCR to extract text content from the image with support for
    both Polish and English characters.

    ⚠️ **Important Notes:**
    - **Processing Time**: This endpoint performs intensive image processing and 
      may take several seconds to complete, especially for large images.
    - **Quality Requirements**: Best results are achieved with clear, high-quality 
      images with good contrast and minimal blur. Poor quality images may result 
      in inaccurate text extraction.

    The endpoint includes specialized preprocessing for receipt images including:
    - Noise reduction and denoising
    - Contrast enhancement using CLAHE
    - Image sharpening
    - Adaptive binarization for varying lighting conditions
    - Morphological operations for text cleanup

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

            # Preprocess the image specifically for receipt OCR
            processed_image = preprocess_receipt_image(image)

            # Save the processed image to temporary file
            processed_image.save(temp_file.name, format='PNG')
            temp_file_path = temp_file.name

        try:
            # Extract text using pytesseract with optimized settings for receipts
            # Use multiple PSM (Page Segmentation Mode) options for better results
            config = (
                '--psm 6 '  # Uniform block of text
                '-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄąĆćĘęŁłŃńÓóŚśŹźŻż.,:-+()[]{}€$£¥₹₽ '
                '--oem 3'  # Use both legacy and LSTM OCR engines
            )

            extracted_text = pytesseract.image_to_string(
                temp_file_path,
                lang='pol+eng',
                config=config
            )

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
