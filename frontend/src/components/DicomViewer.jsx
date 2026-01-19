import { useState, useEffect, useRef } from 'react';
import { getSliceImageUrl, getSliceMetadata } from '../services/api';

/**
 * DICOM image viewer component.
 * Uses server-rendered images for simplicity and compatibility.
 */
function DicomViewer({ slice, windowSettings, onWindowChange, loading }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [activeTool, setActiveTool] = useState('pan');

  const containerRef = useRef(null);
  const imageRef = useRef(null);

  // Load image when slice changes
  useEffect(() => {
    if (slice?.id) {
      const url = getSliceImageUrl(slice.id, {
        windowCenter: windowSettings.center,
        windowWidth: windowSettings.width,
      });
      setImageUrl(url);

      // Load metadata
      getSliceMetadata(slice.id)
        .then((data) => setMetadata(data.metadata))
        .catch(() => setMetadata(null));
    } else {
      setImageUrl(null);
      setMetadata(null);
    }
  }, [slice?.id, windowSettings.center, windowSettings.width]);

  // Reset view when slice changes
  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [slice?.id]);

  const handleMouseDown = (e) => {
    if (activeTool === 'pan') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    } else if (activeTool === 'window') {
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;

    if (activeTool === 'pan') {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    } else if (activeTool === 'window') {
      const deltaX = e.clientX - dragStart.x;
      const deltaY = e.clientY - dragStart.y;

      const newWidth = Math.max(1, (windowSettings.width || 400) + deltaX * 2);
      const newCenter = (windowSettings.center || 200) - deltaY;

      onWindowChange({
        width: newWidth,
        center: newCenter,
      });

      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((prev) => Math.min(Math.max(0.1, prev * delta), 10));
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    onWindowChange({ center: null, width: null });
  };

  if (!slice) {
    return (
      <div className="viewer-area">
        <div className="viewer-placeholder">
          <h2>No Image Selected</h2>
          <p>Upload DICOM files and select a series to view</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Toolbar */}
      <div className="toolbar">
        <button
          className={`tool-btn ${activeTool === 'pan' ? 'active' : ''}`}
          onClick={() => setActiveTool('pan')}
          title="Pan (drag to move)"
        >
          ✥
        </button>
        <button
          className={`tool-btn ${activeTool === 'window' ? 'active' : ''}`}
          onClick={() => setActiveTool('window')}
          title="Window/Level (drag to adjust)"
        >
          ◐
        </button>
        <button className="tool-btn" onClick={() => setZoom((z) => z * 1.2)} title="Zoom In">
          +
        </button>
        <button className="tool-btn" onClick={() => setZoom((z) => z / 1.2)} title="Zoom Out">
          −
        </button>
        <button className="tool-btn" onClick={resetView} title="Reset View">
          ⟲
        </button>

        <div style={{ marginLeft: 'auto', fontSize: '0.75rem', color: '#888' }}>
          Zoom: {Math.round(zoom * 100)}%
          {windowSettings.center !== null && (
            <span style={{ marginLeft: '1rem' }}>
              W: {Math.round(windowSettings.width)} C: {Math.round(windowSettings.center)}
            </span>
          )}
        </div>
      </div>

      {/* Image Viewer */}
      <div
        ref={containerRef}
        className="viewer-area"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        style={{ cursor: isDragging ? 'grabbing' : activeTool === 'pan' ? 'grab' : 'crosshair' }}
      >
        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
          </div>
        )}

        {imageUrl && (
          <img
            ref={imageRef}
            src={imageUrl}
            alt="DICOM slice"
            className="dicom-image"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transition: isDragging ? 'none' : 'transform 0.1s',
            }}
            draggable={false}
          />
        )}
      </div>

      {/* Metadata Display */}
      {metadata && (
        <div className="metadata-section">
          <h4>Image Info</h4>
          <dl className="metadata-grid">
            <dt>Size</dt>
            <dd>
              {metadata.image?.columns} × {metadata.image?.rows}
            </dd>
            <dt>Slice</dt>
            <dd>#{metadata.image?.instance_number}</dd>
            {metadata.image?.slice_thickness > 0 && (
              <>
                <dt>Thickness</dt>
                <dd>{metadata.image.slice_thickness} mm</dd>
              </>
            )}
            {metadata.series?.modality && (
              <>
                <dt>Modality</dt>
                <dd>{metadata.series.modality}</dd>
              </>
            )}
          </dl>
        </div>
      )}
    </>
  );
}

export default DicomViewer;
