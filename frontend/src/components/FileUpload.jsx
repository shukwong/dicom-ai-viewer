import { useState, useRef } from 'react';
import { uploadFiles } from '../services/api';

/**
 * File upload component for DICOM files and folders.
 */
function FileUpload({ onUploadComplete }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragOver(false);

    const items = e.dataTransfer.items;
    const files = [];

    const processEntry = async (entry, path = '') => {
      if (entry.isFile) {
        return new Promise((resolve) => {
          entry.file((file) => {
            file.relativePath = path + file.name;
            files.push(file);
            resolve();
          });
        });
      } else if (entry.isDirectory) {
        const reader = entry.createReader();
        return new Promise((resolve) => {
          const readEntries = () => {
            reader.readEntries(async (entries) => {
              if (entries.length === 0) {
                resolve();
              } else {
                for (const subEntry of entries) {
                  await processEntry(subEntry, path + entry.name + '/');
                }
                readEntries();
              }
            });
          };
          readEntries();
        });
      }
    };

    const promises = [];
    for (const item of items) {
      const entry = item.webkitGetAsEntry?.();
      if (entry) {
        promises.push(processEntry(entry));
      }
    }
    await Promise.all(promises);

    if (files.length > 0) {
      await handleUpload(files);
    }
  };

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files).map((file) => {
      file.relativePath = file.webkitRelativePath || file.name;
      return file;
    });
    if (files.length > 0) {
      await handleUpload(files);
    }
    e.target.value = '';
  };

  const handleUpload = async (files) => {
    // Filter for DICOM files
    const dicomFiles = files.filter((f) => {
      const name = f.name.toLowerCase();
      return (
        name.endsWith('.dcm') ||
        name.endsWith('.dicom') ||
        !name.includes('.') ||
        /^\d+$/.test(name)
      );
    });

    if (dicomFiles.length === 0) {
      setUploadStatus({
        type: 'error',
        message: 'No DICOM files found.',
      });
      return;
    }

    setUploading(true);
    setUploadStatus(null);
    setUploadProgress({ current: 0, total: dicomFiles.length });

    try {
      const result = await uploadFiles(dicomFiles, (current, total) => {
        setUploadProgress({ current, total });
      });

      setUploadStatus({
        type: result.failed > 0 ? 'warning' : 'success',
        message: `Uploaded ${result.uploaded} file(s)${result.failed > 0 ? `, ${result.failed} failed` : ''}`,
      });

      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Upload failed',
      });
    } finally {
      setUploading(false);
      setUploadProgress({ current: 0, total: 0 });
    }
  };

  const progressPercent = uploadProgress.total > 0
    ? Math.round((uploadProgress.current / uploadProgress.total) * 100)
    : 0;

  return (
    <div className="upload-section">
      <div
        className={`upload-zone ${isDragOver ? 'dragover' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".dcm,.DCM,.dicom,*"
          multiple
          onChange={handleFileSelect}
        />
        <input
          ref={folderInputRef}
          type="file"
          webkitdirectory=""
          directory=""
          multiple
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />

        {uploading ? (
          <>
            <div className="loading-spinner"></div>
            <p>Uploading... {progressPercent}%</p>
            <p style={{ fontSize: '0.75rem', color: '#888' }}>
              {uploadProgress.current} / {uploadProgress.total} files
            </p>
          </>
        ) : (
          <>
            <div className="upload-icon">+</div>
            <p>Drop DICOM files or folders</p>
            <p style={{ fontSize: '0.75rem' }}>or click to browse</p>
          </>
        )}
      </div>

      <button
        className="btn btn-secondary"
        style={{ width: '100%', marginTop: '0.5rem' }}
        onClick={(e) => {
          e.stopPropagation();
          folderInputRef.current?.click();
        }}
        disabled={uploading}
      >
        Upload Folder
      </button>

      {uploadStatus && (
        <div
          style={{
            marginTop: '0.5rem',
            padding: '0.5rem',
            borderRadius: '4px',
            fontSize: '0.875rem',
            background:
              uploadStatus.type === 'error'
                ? 'rgba(239, 68, 68, 0.1)'
                : uploadStatus.type === 'warning'
                  ? 'rgba(234, 179, 8, 0.1)'
                  : 'rgba(34, 197, 94, 0.1)',
            color:
              uploadStatus.type === 'error'
                ? '#ef4444'
                : uploadStatus.type === 'warning'
                  ? '#eab308'
                  : '#22c55e',
          }}
        >
          {uploadStatus.message}
        </div>
      )}
    </div>
  );
}

export default FileUpload;
