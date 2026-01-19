"""DICOM file processing service."""

import os
import io
import uuid
import base64
from typing import Dict, List, Optional, Any
from pathlib import Path

import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut
import numpy as np
from PIL import Image


class DicomService:
    """Service for handling DICOM file operations."""

    def __init__(self, upload_dir: str):
        """Initialize the DICOM service."""
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # In-memory storage for study/series/slice metadata
        self.studies: Dict[str, Dict] = {}
        self.series: Dict[str, Dict] = {}
        self.slices: Dict[str, Dict] = {}

    def save_uploaded_file(self, file_content: bytes, filename: str, relative_path: str = None) -> str:
        """Save an uploaded file and return its slice ID.

        Args:
            file_content: Raw bytes of the DICOM file
            filename: Original filename
            relative_path: Relative path including folder structure (patient/body_location/file.dcm)

        Returns:
            Slice ID for the saved file
        """
        slice_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{slice_id}.dcm"

        with open(file_path, "wb") as f:
            f.write(file_content)

        # Parse folder structure from relative path
        folder_info = self._parse_folder_structure(relative_path or filename)

        # Parse and index the DICOM file
        self._index_dicom_file(file_path, slice_id, filename, folder_info)

        return slice_id

    def _parse_folder_structure(self, relative_path: str) -> Dict[str, str]:
        """Parse folder structure to extract patient and body location.

        Expected structure: patient_name/body_location/filename.dcm
        """
        parts = relative_path.replace("\\", "/").split("/")

        if len(parts) >= 3:
            # patient/body_location/file.dcm
            return {
                "patient_folder": parts[0],
                "body_location": parts[1],
                "subfolder": "/".join(parts[1:-1]) if len(parts) > 3 else parts[1]
            }
        elif len(parts) == 2:
            # patient_or_location/file.dcm
            return {
                "patient_folder": parts[0],
                "body_location": parts[0],
                "subfolder": parts[0]
            }
        else:
            return {
                "patient_folder": "Unknown",
                "body_location": "Unknown",
                "subfolder": ""
            }

    def _index_dicom_file(self, file_path: Path, slice_id: str, filename: str, folder_info: Dict) -> None:
        """Parse DICOM file and add to index."""
        try:
            ds = pydicom.dcmread(file_path, force=True)

            # Use folder structure for study/series if DICOM metadata is missing
            patient_name = str(getattr(ds, "PatientName", "")) or folder_info.get("patient_folder", "Unknown")
            body_location = folder_info.get("body_location", "")

            # Create study ID from patient folder or DICOM StudyInstanceUID
            dicom_study_uid = getattr(ds, "StudyInstanceUID", None)
            study_uid = str(dicom_study_uid) if dicom_study_uid else f"study_{folder_info.get('patient_folder', slice_id)}"

            if study_uid not in self.studies:
                self.studies[study_uid] = {
                    "id": study_uid,
                    "patient_name": patient_name,
                    "patient_id": getattr(ds, "PatientID", folder_info.get("patient_folder", "Unknown")),
                    "study_date": getattr(ds, "StudyDate", "Unknown"),
                    "study_description": getattr(ds, "StudyDescription", "") or f"Patient: {patient_name}",
                    "modality": getattr(ds, "Modality", "MR"),
                    "series_ids": []
                }

            # Create series ID from body location folder or DICOM SeriesInstanceUID
            dicom_series_uid = getattr(ds, "SeriesInstanceUID", None)
            series_uid = str(dicom_series_uid) if dicom_series_uid else f"series_{folder_info.get('subfolder', slice_id)}"

            if series_uid not in self.series:
                series_desc = getattr(ds, "SeriesDescription", "") or body_location or "Series"
                self.series[series_uid] = {
                    "id": series_uid,
                    "study_id": study_uid,
                    "series_number": getattr(ds, "SeriesNumber", 1),
                    "series_description": series_desc,
                    "body_part": getattr(ds, "BodyPartExamined", body_location) or body_location,
                    "slice_ids": []
                }
                if series_uid not in self.studies[study_uid]["series_ids"]:
                    self.studies[study_uid]["series_ids"].append(series_uid)

            # Extract slice info
            instance_number = getattr(ds, "InstanceNumber", None)
            if instance_number is None:
                instance_number = len(self.series[series_uid]["slice_ids"]) + 1

            slice_location = getattr(ds, "SliceLocation", 0.0)

            self.slices[slice_id] = {
                "id": slice_id,
                "series_id": series_uid,
                "study_id": study_uid,
                "instance_number": int(instance_number),
                "slice_location": float(slice_location) if slice_location else 0.0,
                "filename": filename,
                "file_path": str(file_path),
                "rows": getattr(ds, "Rows", 0),
                "columns": getattr(ds, "Columns", 0),
            }

            if slice_id not in self.series[series_uid]["slice_ids"]:
                self.series[series_uid]["slice_ids"].append(slice_id)
                # Sort slices by instance number or slice location
                self.series[series_uid]["slice_ids"].sort(
                    key=lambda sid: (
                        self.slices[sid]["instance_number"],
                        self.slices[sid]["slice_location"]
                    )
                )

        except Exception as e:
            print(f"Error indexing DICOM file {filename}: {e}")
            # Store with minimal info if parsing fails
            study_uid = f"study_{folder_info.get('patient_folder', slice_id)}"
            series_uid = f"series_{folder_info.get('subfolder', slice_id)}"

            if study_uid not in self.studies:
                self.studies[study_uid] = {
                    "id": study_uid,
                    "patient_name": folder_info.get("patient_folder", "Unknown"),
                    "study_description": "Uploaded Study",
                    "series_ids": [series_uid]
                }

            if series_uid not in self.series:
                self.series[series_uid] = {
                    "id": series_uid,
                    "study_id": study_uid,
                    "series_description": folder_info.get("body_location", "Uploaded Series"),
                    "slice_ids": []
                }
                if series_uid not in self.studies[study_uid]["series_ids"]:
                    self.studies[study_uid]["series_ids"].append(series_uid)

            self.slices[slice_id] = {
                "id": slice_id,
                "series_id": series_uid,
                "study_id": study_uid,
                "instance_number": len(self.series[series_uid]["slice_ids"]) + 1,
                "filename": filename,
                "file_path": str(file_path),
                "error": str(e)
            }

            if slice_id not in self.series[series_uid]["slice_ids"]:
                self.series[series_uid]["slice_ids"].append(slice_id)

    def get_studies(self) -> List[Dict]:
        """Get all studies."""
        return list(self.studies.values())

    def get_series_for_study(self, study_id: str) -> List[Dict]:
        """Get all series for a study."""
        if study_id not in self.studies:
            return []
        series_ids = self.studies[study_id].get("series_ids", [])
        return [self.series[sid] for sid in series_ids if sid in self.series]

    def get_slices_for_series(self, series_id: str) -> List[Dict]:
        """Get all slices for a series."""
        if series_id not in self.series:
            return []
        slice_ids = self.series[series_id].get("slice_ids", [])
        return [self.slices[sid] for sid in slice_ids if sid in self.slices]

    def get_slice_metadata(self, slice_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific slice."""
        if slice_id not in self.slices:
            return None

        slice_info = self.slices[slice_id]
        file_path = slice_info.get("file_path")

        if not file_path or not os.path.exists(file_path):
            return slice_info

        try:
            ds = pydicom.dcmread(file_path, force=True)

            metadata = {
                "id": slice_id,
                "patient": {
                    "name": str(getattr(ds, "PatientName", "Unknown")),
                    "id": getattr(ds, "PatientID", "Unknown"),
                    "birth_date": getattr(ds, "PatientBirthDate", "Unknown"),
                    "sex": getattr(ds, "PatientSex", "Unknown"),
                },
                "study": {
                    "date": getattr(ds, "StudyDate", "Unknown"),
                    "time": getattr(ds, "StudyTime", "Unknown"),
                    "description": getattr(ds, "StudyDescription", "Unknown"),
                    "id": getattr(ds, "StudyID", "Unknown"),
                },
                "series": {
                    "number": getattr(ds, "SeriesNumber", "Unknown"),
                    "description": getattr(ds, "SeriesDescription", "Unknown"),
                    "modality": getattr(ds, "Modality", "Unknown"),
                    "body_part": getattr(ds, "BodyPartExamined", "Unknown"),
                },
                "image": {
                    "rows": getattr(ds, "Rows", 0),
                    "columns": getattr(ds, "Columns", 0),
                    "instance_number": getattr(ds, "InstanceNumber", 0),
                    "slice_location": float(getattr(ds, "SliceLocation", 0)) if hasattr(ds, "SliceLocation") else 0,
                    "slice_thickness": float(getattr(ds, "SliceThickness", 0)) if hasattr(ds, "SliceThickness") else 0,
                    "pixel_spacing": list(getattr(ds, "PixelSpacing", [1, 1])) if hasattr(ds, "PixelSpacing") else [1, 1],
                },
                "acquisition": {
                    "magnetic_field_strength": float(getattr(ds, "MagneticFieldStrength", 0)) if hasattr(ds, "MagneticFieldStrength") else 0,
                    "sequence_name": getattr(ds, "SequenceName", "Unknown"),
                    "repetition_time": float(getattr(ds, "RepetitionTime", 0)) if hasattr(ds, "RepetitionTime") else 0,
                    "echo_time": float(getattr(ds, "EchoTime", 0)) if hasattr(ds, "EchoTime") else 0,
                }
            }

            return metadata

        except Exception as e:
            return {**slice_info, "error": str(e)}

    def get_slice_image(
        self,
        slice_id: str,
        format: str = "png",
        window_center: Optional[float] = None,
        window_width: Optional[float] = None
    ) -> Optional[bytes]:
        """Get slice image as PNG or JPEG bytes."""
        if slice_id not in self.slices:
            return None

        file_path = self.slices[slice_id].get("file_path")
        if not file_path or not os.path.exists(file_path):
            return None

        try:
            ds = pydicom.dcmread(file_path, force=True)

            # Decompress if needed
            try:
                ds.decompress()
            except Exception:
                pass

            # Get pixel array
            if not hasattr(ds, 'PixelData'):
                return None

            pixel_array = ds.pixel_array.astype(np.float64)

            # Handle photometric interpretation
            photometric = getattr(ds, "PhotometricInterpretation", "MONOCHROME2")
            if photometric == "MONOCHROME1":
                # Invert for MONOCHROME1
                pixel_array = pixel_array.max() - pixel_array

            # Apply rescale slope/intercept if present
            slope = float(getattr(ds, "RescaleSlope", 1))
            intercept = float(getattr(ds, "RescaleIntercept", 0))
            pixel_array = pixel_array * slope + intercept

            # Apply windowing
            if window_center is not None and window_width is not None:
                min_val = window_center - window_width / 2
                max_val = window_center + window_width / 2
                pixel_array = np.clip(pixel_array, min_val, max_val)
            else:
                # Try to apply VOI LUT from DICOM, or use auto-windowing
                try:
                    # Check for window center/width in DICOM
                    wc = getattr(ds, "WindowCenter", None)
                    ww = getattr(ds, "WindowWidth", None)
                    if wc is not None and ww is not None:
                        # Handle multi-valued window settings
                        if hasattr(wc, '__iter__') and not isinstance(wc, str):
                            wc = float(wc[0])
                        else:
                            wc = float(wc)
                        if hasattr(ww, '__iter__') and not isinstance(ww, str):
                            ww = float(ww[0])
                        else:
                            ww = float(ww)
                        min_val = wc - ww / 2
                        max_val = wc + ww / 2
                        pixel_array = np.clip(pixel_array, min_val, max_val)
                except Exception:
                    pass

            # Normalize to 0-255
            pmin, pmax = pixel_array.min(), pixel_array.max()
            if pmax > pmin:
                pixel_array = (pixel_array - pmin) / (pmax - pmin) * 255
            else:
                pixel_array = np.zeros_like(pixel_array)

            pixel_array = pixel_array.astype(np.uint8)

            # Handle multi-frame or color images
            if len(pixel_array.shape) == 3:
                if pixel_array.shape[2] in [3, 4]:
                    # RGB or RGBA
                    image = Image.fromarray(pixel_array)
                else:
                    # Multi-frame - take first frame
                    image = Image.fromarray(pixel_array[0], mode='L')
            else:
                image = Image.fromarray(pixel_array, mode='L')

            # Convert to bytes
            buffer = io.BytesIO()
            image_format = "PNG" if format.lower() == "png" else "JPEG"
            if image_format == "JPEG" and image.mode != "RGB":
                image = image.convert("RGB")
            image.save(buffer, format=image_format, quality=95)
            buffer.seek(0)

            return buffer.getvalue()

        except Exception as e:
            print(f"Error converting DICOM to image: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_slice_image_base64(
        self,
        slice_id: str,
        format: str = "png",
        window_center: Optional[float] = None,
        window_width: Optional[float] = None
    ) -> Optional[str]:
        """Get slice image as base64 encoded string."""
        image_bytes = self.get_slice_image(slice_id, format, window_center, window_width)
        if image_bytes:
            return base64.b64encode(image_bytes).decode('utf-8')
        return None


# Global instance
dicom_service: Optional[DicomService] = None


def get_dicom_service() -> DicomService:
    """Get the global DICOM service instance."""
    global dicom_service
    if dicom_service is None:
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        dicom_service = DicomService(upload_dir)
    return dicom_service
