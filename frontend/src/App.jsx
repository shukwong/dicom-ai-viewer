import { useState, useEffect, useCallback } from 'react';
import FileUpload from './components/FileUpload';
import DicomViewer from './components/DicomViewer';
import SliceNavigator from './components/SliceNavigator';
import InterpretPanel from './components/InterpretPanel';
import {
  getStudies,
  getStudySeries,
  getSeriesSlices,
  getSeriesInterpretation,
  getInterpretationStatus,
} from './services/api';

function App() {
  const [studies, setStudies] = useState([]);
  const [selectedStudy, setSelectedStudy] = useState(null);
  const [series, setSeries] = useState([]);
  const [selectedSeries, setSelectedSeries] = useState(null);
  const [slices, setSlices] = useState([]);
  const [currentSliceIndex, setCurrentSliceIndex] = useState(0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [aiAvailable, setAiAvailable] = useState(false);

  // AI interpretation state
  const [interpretation, setInterpretation] = useState(null);
  const [interpretLoading, setInterpretLoading] = useState(false);

  const [windowSettings, setWindowSettings] = useState({
    center: null,
    width: null,
  });

  useEffect(() => {
    loadStudies();
    checkAiStatus();
  }, []);

  const checkAiStatus = async () => {
    try {
      const status = await getInterpretationStatus();
      setAiAvailable(status.available);
    } catch (err) {
      setAiAvailable(false);
    }
  };

  const loadStudies = async () => {
    try {
      const data = await getStudies();
      setStudies(data.studies || []);
    } catch (err) {
      console.error('Failed to load studies:', err);
    }
  };

  const handleUploadComplete = useCallback(async (result) => {
    await loadStudies();

    if (result.files && result.files.length > 0) {
      const firstFile = result.files.find((f) => f.success);
      if (firstFile && firstFile.study_id) {
        handleStudySelect(firstFile.study_id);
      }
    }
  }, []);

  const handleStudySelect = async (studyId) => {
    setSelectedStudy(studyId);
    setSelectedSeries(null);
    setSlices([]);
    setCurrentSliceIndex(0);
    setInterpretation(null);
    setLoading(true);

    try {
      const data = await getStudySeries(studyId);
      setSeries(data.series || []);

      if (data.series && data.series.length > 0) {
        handleSeriesSelect(data.series[0].id);
      }
    } catch (err) {
      setError('Failed to load series');
      setSeries([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSeriesSelect = async (seriesId) => {
    setSelectedSeries(seriesId);
    setSlices([]);
    setCurrentSliceIndex(0);
    setInterpretation(null);
    setLoading(true);

    try {
      const data = await getSeriesSlices(seriesId);
      setSlices(data.slices || []);
      setCurrentSliceIndex(0);

      // Auto-trigger AI interpretation when series is opened
      if (aiAvailable && data.slices && data.slices.length > 0) {
        fetchInterpretation(seriesId);
      }
    } catch (err) {
      setError('Failed to load slices');
      setSlices([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchInterpretation = async (seriesId, refresh = false) => {
    setInterpretLoading(true);
    try {
      const result = await getSeriesInterpretation(seriesId, refresh);
      setInterpretation(result);
    } catch (err) {
      console.error('Failed to get interpretation:', err);
      setInterpretation({
        success: false,
        error: err.response?.data?.detail || 'Failed to get interpretation'
      });
    } finally {
      setInterpretLoading(false);
    }
  };

  const handleSliceChange = (index) => {
    if (index >= 0 && index < slices.length) {
      setCurrentSliceIndex(index);
    }
  };

  const currentSlice = slices[currentSliceIndex] || null;

  return (
    <div className="app">
      <header className="header">
        <h1>MRI DICOM Viewer</h1>
        <div className="status">
          {aiAvailable ? (
            <span style={{ color: '#4ade80' }}>AI Ready</span>
          ) : (
            <span style={{ color: '#888' }}>AI Unavailable</span>
          )}
        </div>
      </header>

      <div className="main-content">
        <aside className="sidebar">
          <FileUpload onUploadComplete={handleUploadComplete} />

          <div className="studies-section">
            <h3>Studies</h3>
            {studies.length === 0 ? (
              <p style={{ color: '#666', fontSize: '0.875rem' }}>
                No studies uploaded yet
              </p>
            ) : (
              studies.map((study) => (
                <div
                  key={study.id}
                  className={`study-item ${selectedStudy === study.id ? 'selected' : ''}`}
                  onClick={() => handleStudySelect(study.id)}
                >
                  <h4>{study.patient_name || 'Unknown Patient'}</h4>
                  <p>{study.study_description || 'MRI Study'}</p>
                  <p>{study.study_date || ''}</p>

                  {selectedStudy === study.id && series.length > 0 && (
                    <div className="series-list">
                      {series.map((s) => (
                        <div
                          key={s.id}
                          className={`series-item ${selectedSeries === s.id ? 'selected' : ''}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSeriesSelect(s.id);
                          }}
                        >
                          {s.series_description || s.body_part || `Series ${s.series_number}`}
                          <span style={{ color: '#666', marginLeft: '0.5rem' }}>
                            ({s.slice_ids?.length || 0})
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </aside>

        <main className="viewer-container">
          {error && (
            <div className="error-message">
              {error}
              <button
                onClick={() => setError(null)}
                style={{ marginLeft: '1rem' }}
                className="btn btn-secondary"
              >
                Dismiss
              </button>
            </div>
          )}

          <DicomViewer
            slice={currentSlice}
            windowSettings={windowSettings}
            onWindowChange={setWindowSettings}
            loading={loading}
          />

          {slices.length > 0 && (
            <SliceNavigator
              currentIndex={currentSliceIndex}
              totalSlices={slices.length}
              onSliceChange={handleSliceChange}
              sliceInfo={currentSlice}
            />
          )}
        </main>

        <aside className="interpretation-panel">
          <InterpretPanel
            interpretation={interpretation}
            loading={interpretLoading}
            aiAvailable={aiAvailable}
            seriesId={selectedSeries}
            onRefresh={() => selectedSeries && fetchInterpretation(selectedSeries, true)}
          />
        </aside>
      </div>
    </div>
  );
}

export default App;
