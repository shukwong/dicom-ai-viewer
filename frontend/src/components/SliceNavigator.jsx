import { useEffect, useCallback } from 'react';

/**
 * Slice navigation component with slider and prev/next buttons.
 */
function SliceNavigator({ currentIndex, totalSlices, onSliceChange, sliceInfo }) {
  const handlePrevious = useCallback(() => {
    if (currentIndex > 0) {
      onSliceChange(currentIndex - 1);
    }
  }, [currentIndex, onSliceChange]);

  const handleNext = useCallback(() => {
    if (currentIndex < totalSlices - 1) {
      onSliceChange(currentIndex + 1);
    }
  }, [currentIndex, totalSlices, onSliceChange]);

  const handleSliderChange = (e) => {
    onSliceChange(parseInt(e.target.value, 10));
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT') return;

      switch (e.key) {
        case 'ArrowLeft':
        case 'ArrowUp':
          e.preventDefault();
          handlePrevious();
          break;
        case 'ArrowRight':
        case 'ArrowDown':
          e.preventDefault();
          handleNext();
          break;
        case 'Home':
          e.preventDefault();
          onSliceChange(0);
          break;
        case 'End':
          e.preventDefault();
          onSliceChange(totalSlices - 1);
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handlePrevious, handleNext, onSliceChange, totalSlices]);

  if (totalSlices <= 1) {
    return null;
  }

  return (
    <div className="slice-navigator">
      <div className="slice-controls">
        <button onClick={handlePrevious} disabled={currentIndex === 0} title="Previous slice (←)">
          ◀
        </button>

        <input
          type="range"
          className="slice-slider"
          min={0}
          max={totalSlices - 1}
          value={currentIndex}
          onChange={handleSliderChange}
        />

        <button
          onClick={handleNext}
          disabled={currentIndex === totalSlices - 1}
          title="Next slice (→)"
        >
          ▶
        </button>
      </div>

      <div className="slice-info">
        Slice {currentIndex + 1} of {totalSlices}
        {sliceInfo?.slice_location !== undefined && sliceInfo.slice_location !== 0 && (
          <span style={{ marginLeft: '1rem', color: '#666' }}>
            Location: {sliceInfo.slice_location.toFixed(2)} mm
          </span>
        )}
      </div>
    </div>
  );
}

export default SliceNavigator;
