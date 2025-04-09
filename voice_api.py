from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import base64
from voice_to_text import VoiceToText
import speech_recognition as sr
import wave
import io

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the VoiceToText converter
vtt = VoiceToText()

@app.route('/api/microphones', methods=['GET'])
def get_microphones():
    """Get a list of available microphones."""
    microphones = vtt.list_microphones()
    return jsonify(microphones)

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio from a file or base64 data."""
    try:
        # Check if audio data is provided
        if 'audio' not in request.files and 'audio_data' not in request.form:
            return jsonify({"error": "No audio data provided"}), 400
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_filename = temp_file.name
            
            # Handle file upload
            if 'audio' in request.files:
                audio_file = request.files['audio']
                audio_file.save(temp_filename)
            
            # Handle base64 data
            elif 'audio_data' in request.form:
                audio_data = request.form['audio_data']
                # Remove the data URL prefix if present
                if audio_data.startswith('data:audio/wav;base64,'):
                    audio_data = audio_data.replace('data:audio/wav;base64,', '')
                
                # Decode base64 and write to file
                with open(temp_filename, 'wb') as f:
                    f.write(base64.b64decode(audio_data))
        
        # Process the audio file
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_filename) as source:
            audio = recognizer.record(source)
        
        # Try to recognize the speech
        result = {
            "success": False,
            "text": None,
            "error": None
        }
        
        # Try Google's service first
        try:
            text = recognizer.recognize_google(audio)
            result["success"] = True
            result["text"] = text
        except sr.UnknownValueError:
            result["error"] = "Could not understand audio"
        except sr.RequestError as e:
            result["error"] = f"Google Speech Recognition service error: {e}"
        
        # Clean up the temporary file
        os.unlink(temp_filename)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/record', methods=['POST'])
def record_audio():
    """Record audio using the specified microphone."""
    try:
        # Get microphone index from request
        mic_index = request.json.get('mic_index')
        if mic_index is not None:
            mic_index = int(mic_index)
        
        # Convert speech to text
        result = vtt.convert_speech_to_text(mic_index=mic_index)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 