"""Image preprocessing for better OCR accuracy."""

import logging
from typing import Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def pil_to_cv2(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV format."""
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def cv2_to_pil(image: np.ndarray) -> Image.Image:
    """Convert OpenCV image to PIL format."""
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def deskew(image: np.ndarray) -> np.ndarray:
    """
    Deskew an image by detecting text rotation.

    Args:
        image: OpenCV image (BGR format)

    Returns:
        Deskewed image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect edges
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Detect lines using Hough transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    if lines is None:
        logger.debug("No lines detected for deskewing")
        return image

    # Calculate most common angle
    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90
        # Only consider angles close to horizontal
        if abs(angle) < 45:
            angles.append(angle)

    if not angles:
        logger.debug("No horizontal lines found")
        return image

    # Use median angle
    median_angle = np.median(angles)

    if abs(median_angle) < 0.5:
        # Already straight enough
        return image

    logger.debug(f"Deskewing by {median_angle:.2f} degrees")

    # Rotate image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    return rotated


def sharpen(image: np.ndarray) -> np.ndarray:
    """
    Sharpen an image using unsharp mask.

    Args:
        image: OpenCV image

    Returns:
        Sharpened image
    """
    # Gaussian blur
    blurred = cv2.GaussianBlur(image, (0, 0), 3)

    # Unsharp mask
    sharpened = cv2.addWeighted(image, 1.5, blurred, -0.5, 0)

    return sharpened


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).

    Args:
        image: OpenCV image

    Returns:
        Contrast-enhanced image
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    # Split channels
    l, a, b = cv2.split(lab)

    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)

    # Merge channels
    lab_enhanced = cv2.merge([l_enhanced, a, b])

    # Convert back to BGR
    enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    return enhanced


def remove_noise(image: np.ndarray) -> np.ndarray:
    """
    Remove noise using non-local means denoising.

    Args:
        image: OpenCV image

    Returns:
        Denoised image
    """
    denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    return denoised


def preprocess_for_ocr(
    image: Image.Image,
    deskew_enabled: bool = True,
    sharpen_enabled: bool = True,
    contrast_enabled: bool = True,
    denoise_enabled: bool = False,
) -> Image.Image:
    """
    Apply preprocessing pipeline to improve OCR accuracy.

    Args:
        image: PIL Image
        deskew_enabled: Apply deskewing
        sharpen_enabled: Apply sharpening
        contrast_enabled: Apply contrast enhancement
        denoise_enabled: Apply denoising (slow)

    Returns:
        Preprocessed PIL Image
    """
    # Convert to OpenCV
    cv_image = pil_to_cv2(image)

    # Apply preprocessing steps
    if denoise_enabled:
        logger.debug("Removing noise...")
        cv_image = remove_noise(cv_image)

    if deskew_enabled:
        logger.debug("Deskewing...")
        cv_image = deskew(cv_image)

    if contrast_enabled:
        logger.debug("Enhancing contrast...")
        cv_image = enhance_contrast(cv_image)

    if sharpen_enabled:
        logger.debug("Sharpening...")
        cv_image = sharpen(cv_image)

    # Convert back to PIL
    return cv2_to_pil(cv_image)
