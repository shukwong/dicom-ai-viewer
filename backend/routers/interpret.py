"""AI interpretation endpoints."""

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from services.ai_service import get_ai_service
from services.dicom_service import get_dicom_service

router = APIRouter()


class InterpretSeriesRequest(BaseModel):
    """Request model for series interpretation."""
    series_id: str
    context: Optional[str] = None
    modality: str = "MRI"
    sample_count: int = 5


class InterpretRequest(BaseModel):
    """Request model for AI interpretation."""
    slice_ids: List[str]
    series_id: Optional[str] = None
    context: Optional[str] = None
    modality: str = "MRI"
    sample_count: int = 5


class InterpretSingleRequest(BaseModel):
    """Request model for single image interpretation."""
    slice_id: str
    context: Optional[str] = None
    modality: str = "MRI"


@router.get("/interpret/series/{series_id}")
async def get_series_interpretation(series_id: str, refresh: bool = False):
    """Get cached interpretation for a series, or trigger new interpretation."""
    ai_service = get_ai_service()
    dicom_service = get_dicom_service()

    # Check cache first (unless refresh requested)
    if not refresh:
        cached = ai_service.get_cached_interpretation(series_id)
        if cached:
            cached_copy = cached.copy()
            cached_copy["from_cache"] = True
            return cached_copy

    # If not cached and AI available, generate interpretation
    if not ai_service.is_available():
        return {
            "success": False,
            "error": "AI service not available",
            "from_cache": False
        }

    # Get slices for the series
    slices = dicom_service.get_slices_for_series(series_id)
    if not slices:
        return {
            "success": False,
            "error": "No slices found for series",
            "from_cache": False
        }

    # Get images
    slice_images = []
    for s in slices:
        img = dicom_service.get_slice_image_base64(s["id"])
        if img:
            slice_images.append(img)

    if not slice_images:
        return {
            "success": False,
            "error": "Could not load images",
            "from_cache": False
        }

    # Generate interpretation
    result = await ai_service.interpret_series(
        slice_images=slice_images,
        sample_count=5,
        series_id=series_id,
        refresh=refresh
    )

    return result


@router.post("/interpret")
async def interpret_slices(request: InterpretRequest):
    """Get AI interpretation for a set of DICOM slices."""
    ai_service = get_ai_service()
    dicom_service = get_dicom_service()

    # Check cache if series_id provided
    if request.series_id:
        cached = ai_service.get_cached_interpretation(request.series_id)
        if cached:
            cached_copy = cached.copy()
            cached_copy["from_cache"] = True
            return cached_copy

    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Please set ANTHROPIC_API_KEY environment variable."
        )

    slice_images = []
    for slice_id in request.slice_ids:
        image_b64 = dicom_service.get_slice_image_base64(slice_id)
        if image_b64:
            slice_images.append(image_b64)

    if not slice_images:
        raise HTTPException(
            status_code=404,
            detail="No valid images found for the provided slice IDs."
        )

    result = await ai_service.interpret_series(
        slice_images=slice_images,
        sample_count=request.sample_count,
        context=request.context,
        modality=request.modality,
        series_id=request.series_id
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Unknown error during interpretation")
        )

    return result


@router.post("/interpret/series")
async def interpret_series(request: InterpretSeriesRequest):
    """Get AI interpretation for a series by series_id."""
    ai_service = get_ai_service()
    dicom_service = get_dicom_service()

    # Check cache first
    cached = ai_service.get_cached_interpretation(request.series_id)
    if cached:
        cached_copy = cached.copy()
        cached_copy["from_cache"] = True
        return cached_copy

    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Please set ANTHROPIC_API_KEY environment variable."
        )

    # Get slices for the series
    slices = dicom_service.get_slices_for_series(request.series_id)
    if not slices:
        raise HTTPException(
            status_code=404,
            detail="Series not found or has no slices."
        )

    # Get images
    slice_images = []
    for s in slices:
        img = dicom_service.get_slice_image_base64(s["id"])
        if img:
            slice_images.append(img)

    if not slice_images:
        raise HTTPException(
            status_code=404,
            detail="Could not load images for series."
        )

    result = await ai_service.interpret_series(
        slice_images=slice_images,
        sample_count=request.sample_count,
        context=request.context,
        modality=request.modality,
        series_id=request.series_id
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Unknown error during interpretation")
        )

    return result


@router.post("/interpret/single")
async def interpret_single_slice(request: InterpretSingleRequest):
    """Get AI interpretation for a single DICOM slice."""
    ai_service = get_ai_service()
    dicom_service = get_dicom_service()

    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Please set ANTHROPIC_API_KEY environment variable."
        )

    image_b64 = dicom_service.get_slice_image_base64(request.slice_id)
    if not image_b64:
        raise HTTPException(
            status_code=404,
            detail="Slice not found or could not be converted to image."
        )

    images = [{"data": image_b64, "media_type": "image/png"}]
    result = await ai_service.interpret_images(
        images=images,
        context=request.context,
        modality=request.modality
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Unknown error during interpretation")
        )

    return result


@router.get("/interpret/status")
async def get_interpretation_status():
    """Check if AI interpretation service is available."""
    ai_service = get_ai_service()
    return {
        "available": ai_service.is_available(),
        "message": "AI service is ready" if ai_service.is_available() else "ANTHROPIC_API_KEY not configured"
    }
