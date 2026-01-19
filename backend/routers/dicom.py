"""DICOM file handling endpoints."""

from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import Response

from services.dicom_service import get_dicom_service

router = APIRouter()


@router.post("/upload")
async def upload_dicom_files(
    files: List[UploadFile] = File(...),
    paths: List[str] = Form(default=[])
):
    """Upload one or more DICOM files with optional folder paths.

    The paths parameter contains relative paths for each file,
    preserving folder structure (patient/body_location/file.dcm).
    """
    dicom_service = get_dicom_service()
    results = []

    for i, file in enumerate(files):
        try:
            content = await file.read()
            # Get relative path if provided
            relative_path = paths[i] if i < len(paths) else (file.filename or "unknown.dcm")
            slice_id = dicom_service.save_uploaded_file(content, file.filename or "unknown.dcm", relative_path)
            slice_info = dicom_service.slices.get(slice_id, {})
            results.append({
                "success": True,
                "filename": file.filename,
                "relative_path": relative_path,
                "slice_id": slice_id,
                "study_id": slice_info.get("study_id"),
                "series_id": slice_info.get("series_id"),
            })
        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e)
            })

    return {
        "uploaded": len([r for r in results if r.get("success")]),
        "failed": len([r for r in results if not r.get("success")]),
        "files": results
    }


@router.get("/studies")
async def list_studies():
    """List all uploaded studies."""
    dicom_service = get_dicom_service()
    studies = dicom_service.get_studies()
    return {"studies": studies}


@router.get("/studies/{study_id:path}/series")
async def get_study_series(study_id: str):
    """Get all series in a study."""
    dicom_service = get_dicom_service()
    series = dicom_service.get_series_for_study(study_id)
    if not series:
        raise HTTPException(status_code=404, detail="Study not found")
    return {"series": series}


@router.get("/series/{series_id:path}/slices")
async def get_series_slices(series_id: str):
    """Get all slices in a series."""
    dicom_service = get_dicom_service()
    slices = dicom_service.get_slices_for_series(series_id)
    if not slices:
        raise HTTPException(status_code=404, detail="Series not found")
    return {"slices": slices}


@router.get("/slices/{slice_id}/image")
async def get_slice_image(
    slice_id: str,
    format: str = Query(default="png", pattern="^(png|jpeg)$"),
    window_center: Optional[float] = Query(default=None),
    window_width: Optional[float] = Query(default=None)
):
    """Get a slice as a PNG or JPEG image."""
    dicom_service = get_dicom_service()
    image_bytes = dicom_service.get_slice_image(
        slice_id, format, window_center, window_width
    )

    if image_bytes is None:
        raise HTTPException(status_code=404, detail="Slice not found or could not be converted")

    media_type = "image/png" if format == "png" else "image/jpeg"
    return Response(
        content=image_bytes,
        media_type=media_type,
        headers={"Cache-Control": "max-age=3600"}
    )


@router.get("/slices/{slice_id}/metadata")
async def get_slice_metadata(slice_id: str):
    """Get DICOM metadata for a slice."""
    dicom_service = get_dicom_service()
    metadata = dicom_service.get_slice_metadata(slice_id)

    if metadata is None:
        raise HTTPException(status_code=404, detail="Slice not found")

    return {"metadata": metadata}


@router.get("/slices/{slice_id}/image-base64")
async def get_slice_image_base64(
    slice_id: str,
    format: str = Query(default="png", pattern="^(png|jpeg)$"),
    window_center: Optional[float] = Query(default=None),
    window_width: Optional[float] = Query(default=None)
):
    """Get a slice as a base64-encoded image."""
    dicom_service = get_dicom_service()
    image_b64 = dicom_service.get_slice_image_base64(
        slice_id, format, window_center, window_width
    )

    if image_b64 is None:
        raise HTTPException(status_code=404, detail="Slice not found")

    media_type = "image/png" if format == "png" else "image/jpeg"
    return {
        "image": image_b64,
        "media_type": media_type,
        "format": format
    }
