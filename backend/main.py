"""FastAPI backend for MRI DICOM Viewer."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import dicom, interpret

app = FastAPI(
    title="MRI DICOM Viewer API",
    description="API for uploading, viewing, and interpreting MRI DICOM images",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dicom.router, prefix="/api", tags=["DICOM"])
app.include_router(interpret.router, prefix="/api", tags=["Interpretation"])

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "MRI DICOM Viewer API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
