/**
 * AI interpretation panel component.
 * Displays auto-triggered interpretations when a series is opened.
 */
function InterpretPanel({ interpretation, loading, aiAvailable, seriesId, onRefresh }) {
  if (!aiAvailable) {
    return (
      <>
        <h3>AI Analysis</h3>
        <div className="interpretation-content">
          <div className="interpretation-placeholder">
            <p style={{ color: '#e94560' }}>AI service unavailable</p>
            <p style={{ fontSize: '0.75rem', marginTop: '0.5rem' }}>
              Set ANTHROPIC_API_KEY environment variable to enable AI interpretations.
            </p>
          </div>
        </div>
      </>
    );
  }

  if (!seriesId) {
    return (
      <>
        <h3>AI Analysis</h3>
        <div className="interpretation-content">
          <div className="interpretation-placeholder">
            <p>No series selected</p>
            <p style={{ fontSize: '0.75rem', marginTop: '0.5rem' }}>
              Select a series to view AI interpretation.
            </p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <h3>
        AI Analysis
        {loading && <span className="loading-spinner" style={{ marginLeft: '0.5rem' }}></span>}
        {interpretation?.from_cache && (
          <span style={{ fontSize: '0.7rem', color: '#888', marginLeft: '0.5rem' }}>(cached)</span>
        )}
      </h3>

      <div className="interpretation-content">
        {loading && (
          <div className="interpretation-placeholder">
            <div className="loading-spinner" style={{ margin: '0 auto 1rem' }}></div>
            <p>Analyzing images...</p>
          </div>
        )}

        {!loading && interpretation?.success === false && (
          <div
            style={{
              padding: '0.75rem',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '4px',
              color: '#ef4444',
              fontSize: '0.875rem',
            }}
          >
            {interpretation.error || 'Failed to get interpretation'}
          </div>
        )}

        {!loading && interpretation?.success && (
          <>
            <div className="interpretation-result">{interpretation.interpretation}</div>

            <div className="interpretation-disclaimer">{interpretation.disclaimer}</div>

            <div
              style={{
                marginTop: '0.5rem',
                fontSize: '0.75rem',
                color: '#666',
              }}
            >
              {interpretation.generated_at && (
                <div>Generated: {new Date(interpretation.generated_at).toLocaleTimeString()}</div>
              )}
              {interpretation.usage && !interpretation.from_cache && (
                <div>Tokens: {interpretation.usage.input_tokens + interpretation.usage.output_tokens}</div>
              )}
            </div>
          </>
        )}

        {!loading && interpretation?.success && (
          <button
            className="btn btn-secondary"
            style={{ width: '100%', marginTop: '1rem' }}
            onClick={onRefresh}
            disabled={loading}
          >
            Re-analyze
          </button>
        )}
      </div>
    </>
  );
}

export default InterpretPanel;
