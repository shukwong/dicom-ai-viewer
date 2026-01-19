# MRI DICOM Viewer

A web application for browsing MRI images in DICOM format with AI-powered interpretations.

## Features

- Upload and view DICOM files
- Navigate through MRI slices with slider and keyboard controls
- Zoom, pan, and window/level adjustment tools
- AI-powered image interpretation using Claude API
- Study and series organization

## Prerequisites

- Python 3.9+
- Node.js 18+
- Anthropic API key (optional, for AI interpretations)

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key for AI features (optional)
export ANTHROPIC_API_KEY="your-api-key"

# Start the server
python main.py
```

The backend will run at http://localhost:8000

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will run at http://localhost:5173

## Usage

1. Open http://localhost:5173 in your browser
2. Drop DICOM files onto the upload zone (or click to browse)
3. Select a study and series from the left sidebar
4. Use the viewer tools to navigate and adjust the image:
   - **Pan**: Drag to move the image
   - **Window/Level**: Adjust contrast and brightness
   - **Zoom**: Use mouse wheel or +/- buttons
   - **Slice Navigation**: Use slider or arrow keys
5. Request AI interpretation in the right panel (requires API key)

## Keyboard Shortcuts

- `←` / `↑` - Previous slice
- `→` / `↓` - Next slice
- `Home` - First slice
- `End` - Last slice
- Mouse wheel - Zoom in/out

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload DICOM files |
| GET | `/api/studies` | List uploaded studies |
| GET | `/api/studies/{id}/series` | Get series in a study |
| GET | `/api/series/{id}/slices` | Get slice list |
| GET | `/api/slices/{id}/image` | Get slice as image |
| GET | `/api/slices/{id}/metadata` | Get DICOM metadata |
| POST | `/api/interpret` | Get AI interpretation |
| POST | `/api/interpret/single` | Interpret single slice |

## Project Structure

```
MRI_reader/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── routers/
│   │   ├── dicom.py         # DICOM file endpoints
│   │   └── interpret.py     # AI interpretation endpoints
│   ├── services/
│   │   ├── dicom_service.py # DICOM processing logic
│   │   └── ai_service.py    # Claude API integration
│   ├── uploads/             # Uploaded DICOM files
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DicomViewer.jsx    # Main viewer component
│   │   │   ├── FileUpload.jsx     # Upload interface
│   │   │   ├── SliceNavigator.jsx # Slice browsing controls
│   │   │   └── InterpretPanel.jsx # AI interpretation display
│   │   ├── services/
│   │   │   └── api.js       # Backend API calls
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Disclaimer

This application is for educational and research purposes only. AI interpretations should NOT be used for clinical decision-making. Always consult qualified medical professionals for diagnosis and treatment.

## License

MIT
