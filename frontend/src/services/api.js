/**
 * API service for communicating with the backend.
 */

import axios from 'axios';

const API_BASE = '/api';
const BATCH_SIZE = 100;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Upload DICOM files to the server in batches.
 */
export async function uploadFiles(files, onProgress) {
  let totalUploaded = 0;
  let totalFailed = 0;
  const allResults = [];

  for (let i = 0; i < files.length; i += BATCH_SIZE) {
    const batch = files.slice(i, i + BATCH_SIZE);
    const formData = new FormData();

    for (const file of batch) {
      formData.append('files', file);
      formData.append('paths', file.relativePath || file.webkitRelativePath || file.name);
    }

    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      totalUploaded += response.data.uploaded;
      totalFailed += response.data.failed;
      allResults.push(...response.data.files);

      if (onProgress) {
        onProgress(Math.min(i + BATCH_SIZE, files.length), files.length);
      }
    } catch (error) {
      totalFailed += batch.length;
      console.error('Batch upload failed:', error);
    }
  }

  return {
    uploaded: totalUploaded,
    failed: totalFailed,
    files: allResults
  };
}

export async function getStudies() {
  const response = await api.get('/studies');
  return response.data;
}

export async function getStudySeries(studyId) {
  const response = await api.get(`/studies/${encodeURIComponent(studyId)}/series`);
  return response.data;
}

export async function getSeriesSlices(seriesId) {
  const response = await api.get(`/series/${encodeURIComponent(seriesId)}/slices`);
  return response.data;
}

export function getSliceImageUrl(sliceId, options = {}) {
  const params = new URLSearchParams();
  params.append('format', 'png');
  if (options.windowCenter !== undefined && options.windowCenter !== null) {
    params.append('window_center', options.windowCenter);
  }
  if (options.windowWidth !== undefined && options.windowWidth !== null) {
    params.append('window_width', options.windowWidth);
  }
  return `${API_BASE}/slices/${encodeURIComponent(sliceId)}/image?${params.toString()}`;
}

export async function getSliceMetadata(sliceId) {
  const response = await api.get(`/slices/${encodeURIComponent(sliceId)}/metadata`);
  return response.data;
}

/**
 * Get AI interpretation for a series (auto-triggers on series open).
 * Returns cached result if available.
 * @param {string} seriesId - Series ID
 * @param {boolean} refresh - Force refresh (bypass cache)
 */
export async function getSeriesInterpretation(seriesId, refresh = false) {
  const params = refresh ? '?refresh=true' : '';
  const response = await api.get(`/interpret/series/${encodeURIComponent(seriesId)}${params}`);
  return response.data;
}

export async function getInterpretation(sliceIds, options = {}) {
  const response = await api.post('/interpret', {
    slice_ids: sliceIds,
    series_id: options.seriesId,
    context: options.context,
    modality: options.modality || 'MRI',
    sample_count: options.sampleCount || 5,
  });
  return response.data;
}

export async function getSliceInterpretation(sliceId, options = {}) {
  const response = await api.post('/interpret/single', {
    slice_id: sliceId,
    context: options.context,
    modality: options.modality || 'MRI',
  });
  return response.data;
}

export async function getInterpretationStatus() {
  const response = await api.get('/interpret/status');
  return response.data;
}

export default api;
