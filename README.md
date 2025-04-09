# Voice-to-Text Web Application

This application allows you to record audio from your microphone and convert it to text using speech recognition.

## Features

- Record audio from your microphone
- Select from available microphones
- Convert speech to text using Google's Speech Recognition API
- Fallback to offline recognition using PocketSphinx
- Modern, responsive web interface

## Setup Instructions

### Prerequisites

- Python 3.6 or higher
- A microphone connected to your computer
- Internet connection (for Google Speech Recognition)

### Installation

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. If you encounter issues installing PyAudio, you may need to install it separately:

- **Windows**: `pip install pipwin` followed by `pipwin install pyaudio`
- **macOS**: `brew install portaudio` followed by `pip install pyaudio`
- **Linux**: `sudo apt-get install python3-pyaudio` or equivalent for your distribution

### Running the Application

1. Start the Flask server:

```bash
python voice_api.py
```

2. Open the HTML file in your web browser:

- Navigate to the `backend/frontend` directory
- Open `voice_recorder.html` in your web browser

## Usage

1. Select a microphone from the dropdown menu (or use the default)
2. Click "Start Recording" to begin recording audio
3. Speak into your microphone
4. Click "Stop Recording" when you're done
5. Wait for the transcription to appear

## API Endpoints

The application provides the following API endpoints:

- `GET /api/microphones` - Get a list of available microphones
- `POST /api/transcribe` - Transcribe audio from a file or base64 data
- `POST /api/record` - Record audio using the specified microphone

## Troubleshooting

- If you encounter issues with microphone access, make sure your browser has permission to access your microphone
- If transcription fails, check your internet connection (for Google Speech Recognition)
- If you see errors related to PocketSphinx, you may need to install additional dependencies

## License

This project is open source and available under the MIT License. 