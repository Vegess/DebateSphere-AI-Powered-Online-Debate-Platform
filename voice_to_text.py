# voice_to_text.py

import speech_recognition as sr
import time
import os
from typing import Optional, Dict, Any

# Check if Sphinx is available
SPHINX_AVAILABLE = False
try:
    import pocketsphinx
    SPHINX_AVAILABLE = True
except ImportError:
    print("Note: PocketSphinx not available. Offline recognition will be disabled.")

class VoiceToText:
    def __init__(self, language: str = "en-US", timeout: int = 5, phrase_time_limit: int = 10):
        """
        Initialize the VoiceToText converter.
        
        Args:
            language: Language code for speech recognition (default: "en-US")
            timeout: How long to wait for a phrase to start (default: 5 seconds)
            phrase_time_limit: Maximum length of recording (default: 10 seconds)
        """
        self.recognizer = sr.Recognizer()
        self.language = language
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        
        # Configure recognizer settings
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 4000  # Adjust based on your microphone
        
    def list_microphones(self) -> Dict[int, str]:
        """List all available microphones."""
        return {i: name for i, name in enumerate(sr.Microphone.list_microphone_names())}
    
    def convert_speech_to_text(self, mic_index: Optional[int] = None) -> Dict[str, Any]:
        """
        Convert speech to text using the specified microphone.
        
        Args:
            mic_index: Index of the microphone to use (None for default)
            
        Returns:
            Dictionary with transcription result and status
        """
        result = {
            "success": False,
            "text": None,
            "error": None
        }
        
        try:
            # Use specified microphone or default
            mic = sr.Microphone(device_index=mic_index) if mic_index is not None else sr.Microphone()
            
            print("🎤 Speak now... (Recording)")
            with mic as source:
                # Adjust for ambient noise
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Listen for audio
                audio = self.recognizer.listen(
                    source, 
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit
                )
            
            print("⏳ Processing your speech...")
            
            # Try multiple recognition services
            text = None
            error = None
            
            # Try Google's service first
            try:
                text = self.recognizer.recognize_google(audio, language=self.language)
                print(f"📝 Transcription: {text}")
            except sr.UnknownValueError:
                error = "Could not understand audio"
            except sr.RequestError as e:
                error = f"Google Speech Recognition service error: {e}"
                
            # If Google fails and Sphinx is available, try Sphinx (offline recognition)
            if text is None and SPHINX_AVAILABLE:
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    print(f"📝 Transcription (Sphinx): {text}")
                except Exception as e:
                    error = f"Sphinx recognition failed: {e}"
            
            if text:
                result["success"] = True
                result["text"] = text
            else:
                result["error"] = error
                
        except Exception as e:
            result["error"] = f"Error during speech recognition: {e}"
            
        return result
    
    def save_audio(self, audio_data, filename: str = "recorded_audio.wav"):
        """Save recorded audio to a file."""
        try:
            with open(filename, "wb") as f:
                f.write(audio_data.get_wav_data())
            print(f"✅ Audio saved to {filename}")
            return True
        except Exception as e:
            print(f"❌ Failed to save audio: {e}")
            return False

# For testing this file directly
if __name__ == "__main__":
    # Create an instance with default settings
    vtt = VoiceToText()
    
    # List available microphones
    print("Available microphones:")
    for idx, name in vtt.list_microphones().items():
        print(f"  {idx}: {name}")
    
    # Ask user to select a microphone
    try:
        mic_index = int(input("\nEnter microphone index to use (or press Enter for default): ") or -1)
        if mic_index == -1:
            mic_index = None
    except ValueError:
        print("Invalid input. Using default microphone.")
        mic_index = None
    
    # Convert speech to text
    result = vtt.convert_speech_to_text(mic_index=mic_index)
    
    # Print result
    if result["success"]:
        print(f"Transcription: {result['text']}")
    else:
        print(f"Error: {result['error']}")
