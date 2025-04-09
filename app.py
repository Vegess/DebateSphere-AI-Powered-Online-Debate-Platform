import os
import sys
import json
import tempfile
import base64
import speech_recognition as sr
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import nltk
from nltk.tokenize import sent_tokenize
import re
from pydub import AudioSegment
import io
import random
import string
from database import Database
from gpt_analyzer import GPTAnalyzer
from fact_checker import FactChecker

# Download required NLTK data
print("Initializing NLTK...")
try:
    nltk.data.find('tokenizers/punkt')
    print("NLTK punkt tokenizer already downloaded.")
except LookupError:
    print("Downloading NLTK punkt tokenizer...")
    try:
        nltk.download('punkt', quiet=True)
        print("NLTK punkt tokenizer downloaded successfully.")
    except Exception as e:
        print(f"Error downloading NLTK punkt tokenizer: {str(e)}")
        print("The application may not function correctly without the punkt tokenizer.")

# Add the frontend directory to the path so we can import our VoiceToText class
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))
from voice_to_text import VoiceToText

# Download required NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

app = Flask(__name__, static_folder='../frontend/public', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize the VoiceToText converter
vtt = VoiceToText()

# Initialize database and GPT analyzer
db = Database()
gpt_analyzer = GPTAnalyzer()

# Import our new fact checker
fact_checker = FactChecker()

# Sample fact database - in a real application, this would be a comprehensive database
FACT_DATABASE = {
    "climate change": {
        "facts": [
            "The Earth's average temperature has increased by approximately 1.1°C since the pre-industrial era.",
            "The concentration of CO2 in the atmosphere has increased from about 280 ppm in 1750 to over 400 ppm today.",
            "The Arctic is warming at twice the global average rate.",
            "Global sea levels have risen by about 8 inches since 1900.",
            "The last seven years have been the warmest on record.",
            "Extreme weather events have become more frequent and intense due to climate change."
        ],
        "sources": ["IPCC", "NASA", "NOAA", "World Meteorological Organization"],
        "counter_arguments": [
            "Climate change is a natural cycle and not caused by human activities.",
            "The Earth has been warmer in the past, so current warming is not concerning.",
            "Climate models are unreliable and exaggerate future warming.",
            "CO2 is a plant food and more of it is beneficial for agriculture."
        ]
    },
    "vaccination": {
        "facts": [
            "Vaccines have eradicated smallpox and nearly eliminated polio worldwide.",
            "Vaccines undergo rigorous safety testing before approval for public use.",
            "Herd immunity requires a high percentage of the population to be vaccinated.",
            "Vaccines do not cause autism - this claim was based on a fraudulent study.",
            "The benefits of vaccination far outweigh the risks of side effects.",
            "Vaccines contain only trace amounts of preservatives like thimerosal."
        ],
        "sources": ["WHO", "CDC", "NIH", "American Academy of Pediatrics"],
        "counter_arguments": [
            "Vaccines cause autism and other developmental disorders.",
            "Vaccines contain dangerous levels of mercury and other toxins.",
            "Natural immunity is better than vaccine-induced immunity.",
            "Vaccines are part of a conspiracy to control the population."
        ]
    },
    "covid-19": {
        "facts": [
            "COVID-19 is caused by the SARS-CoV-2 virus.",
            "The virus primarily spreads through respiratory droplets.",
            "Multiple effective vaccines have been developed against COVID-19.",
            "Face masks help reduce the spread of the virus when worn correctly.",
            "COVID-19 is more severe than seasonal influenza for many people.",
            "Asymptomatic people can still spread the virus to others."
        ],
        "sources": ["WHO", "CDC", "NIH", "European Centre for Disease Prevention and Control"],
        "counter_arguments": [
            "COVID-19 is no worse than the flu.",
            "The virus was created in a laboratory as a bioweapon.",
            "Face masks don't work and can cause health problems.",
            "The vaccines were developed too quickly and are unsafe."
        ]
    },
    "democracy": {
        "facts": [
            "India is the world's largest democracy with over 900 million eligible voters.",
            "The first democratic elections in India were held in 1951-52.",
            "The Indian Constitution guarantees universal adult suffrage.",
            "India has a multi-party system with regular elections at various levels.",
            "The Election Commission of India is responsible for conducting free and fair elections.",
            "India has successfully conducted elections even during the COVID-19 pandemic."
        ],
        "sources": ["Election Commission of India", "Constitution of India", "International Institute for Democracy and Electoral Assistance"],
        "counter_arguments": [
            "India's democracy is flawed due to money power and criminalization of politics.",
            "Electoral reforms are needed to make Indian democracy more representative.",
            "Voter turnout in India has been declining in recent years.",
            "The first-past-the-post system leads to disproportionate representation."
        ]
    },
    "education": {
        "facts": [
            "India has one of the largest higher education systems in the world.",
            "The Right to Education Act (RTE) was passed in 2009.",
            "India has over 1000 universities and 40,000 colleges.",
            "The National Education Policy 2020 aims to transform India's education system.",
            "India produces the largest number of STEM graduates globally.",
            "The literacy rate in India has increased from 18.33% in 1951 to 77.7% in 2018."
        ],
        "sources": ["MHRD", "UGC", "NEP 2020", "UNESCO"],
        "counter_arguments": [
            "The quality of education in India is declining despite increased enrollment.",
            "There is a significant digital divide in access to online education.",
            "Rote learning is still prevalent in Indian education system.",
            "Higher education in India is not aligned with industry requirements."
        ]
    },
    "economy": {
        "facts": [
            "India is the world's fifth-largest economy by nominal GDP.",
            "India's GDP growth rate averaged around 7% from 2014 to 2019.",
            "The service sector contributes the largest share to India's GDP.",
            "India has implemented significant economic reforms since 1991.",
            "India is one of the fastest-growing major economies in the world.",
            "The Indian government has launched several initiatives to promote entrepreneurship and innovation."
        ],
        "sources": ["World Bank", "IMF", "Reserve Bank of India", "Ministry of Finance"],
        "counter_arguments": [
            "India's economic growth has slowed down in recent years.",
            "Income inequality has increased in India despite economic growth.",
            "The informal sector employs a large portion of India's workforce.",
            "India faces challenges in creating enough jobs for its growing workforce."
        ]
    },
    "technology": {
        "facts": [
            "India is one of the largest IT services exporters in the world.",
            "India has the second-largest number of internet users globally.",
            "The Indian government has launched the Digital India initiative.",
            "India has one of the lowest data costs in the world.",
            "India is a major hub for software development and IT services.",
            "The Indian startup ecosystem has grown significantly in recent years."
        ],
        "sources": ["NASSCOM", "Ministry of Electronics and Information Technology", "World Bank", "GSMA"],
        "counter_arguments": [
            "Digital divide persists in India, especially in rural areas.",
            "India's technology sector is dependent on foreign markets.",
            "Cybersecurity concerns are growing with increased digital adoption.",
            "India lacks sufficient investment in research and development."
        ]
    }
}

# Keywords that often indicate a claim
CLAIM_INDICATORS = [
    'is', 'are', 'was', 'were', 'should', 'must', 'need', 'always', 'never', 
    'every', 'all', 'none', 'fact', 'prove', 'evidence', 'study', 'research', 
    'data', 'statistics', 'shows', 'demonstrates', 'indicates', 'suggests',
    'concludes', 'finds', 'reveals', 'claims', 'asserts', 'maintains', 'argues',
    'contends', 'believes', 'thinks', 'says', 'states', 'declares', 'announces',
    'reports', 'according to', 'based on', 'according to research', 'studies show',
    'experts say', 'scientists say', 'research shows', 'data shows', 'evidence shows'
]

def extract_claims(text):
    """
    Extract claims from text using NLTK for sentence tokenization and
    pattern matching for claim identification.
    """
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    claims = []
    
    for sentence in sentences:
        # Skip very short sentences
        if len(sentence.split()) < 3:
            continue
            
        # Check if the sentence contains claim indicators
        sentence_lower = sentence.lower()
        if any(indicator in sentence_lower for indicator in CLAIM_INDICATORS):
            claims.append(sentence.strip())
            
    return claims

def calculate_claim_percentages(claims):
    """
    Calculate the percentage of claims found in the text.
    """
    total_claims = len(claims)
    if total_claims == 0:
        return []
    
    percentages = []
    for i, claim in enumerate(claims):
        percentage = ((i + 1) / total_claims) * 100
        percentages.append({
            'claim': claim,
            'percentage': round(percentage, 2)
        })
    return percentages

def find_relevant_facts(claim, topic):
    """
    Find facts from the database that are relevant to the claim.
    """
    if topic not in FACT_DATABASE:
        return []
        
    facts = FACT_DATABASE[topic]["facts"]
    claim_lower = claim.lower()
    
    # Simple relevance scoring based on word overlap
    relevant_facts = []
    for fact in facts:
        fact_lower = fact.lower()
        # Count common words between claim and fact
        claim_words = set(claim_lower.split())
        fact_words = set(fact_lower.split())
        common_words = claim_words.intersection(fact_words)
        
        # If there's significant overlap, consider the fact relevant
        if len(common_words) >= 3:
            relevant_facts.append(fact)
            
    return relevant_facts

def find_counter_arguments(claim, topic):
    """
    Find counter arguments from the database that are relevant to the claim.
    """
    if topic not in FACT_DATABASE or "counter_arguments" not in FACT_DATABASE[topic]:
        return []
        
    counter_args = FACT_DATABASE[topic]["counter_arguments"]
    claim_lower = claim.lower()
    
    # Find counter arguments that directly contradict the claim
    relevant_counter_args = []
    for arg in counter_args:
        arg_lower = arg.lower()
        # Check for contradiction indicators
        if any(word in claim_lower and word in arg_lower for word in ["is", "are", "was", "were"]):
            relevant_counter_args.append(arg)
            
    return relevant_counter_args

def generate_reason(claim, verification_status, relevant_facts, counter_arguments, topic):
    """
    Generate a detailed reason for the verification status.
    """
    if verification_status == "true":
        if relevant_facts:
            return f"This claim is TRUE. {relevant_facts[0]} Additionally, {relevant_facts[1] if len(relevant_facts) > 1 else 'scientific evidence supports this statement.'}"
        else:
            return f"This claim about {topic} appears to be TRUE based on available information, though specific supporting facts are not found in our database."
    
    elif verification_status == "false":
        if counter_arguments:
            return f"This claim is FALSE. {counter_arguments[0]} In fact, {relevant_facts[0] if relevant_facts else 'available evidence contradicts this statement.'}"
        else:
            return f"This claim about {topic} appears to be FALSE based on available information, though specific contradicting facts are not found in our database."
    
    elif verification_status == "partially true":
        if relevant_facts and counter_arguments:
            return f"This claim is PARTIALLY TRUE. While {relevant_facts[0]}, it's important to note that {counter_arguments[0]}"
        else:
            return f"This claim about {topic} is PARTIALLY TRUE. It contains some accurate information but also includes inaccuracies or oversimplifications."
    
    elif verification_status == "misleading":
        if counter_arguments:
            return f"This claim is MISLEADING. {counter_arguments[0]} The claim presents a distorted or incomplete view of the facts."
        else:
            return f"This claim about {topic} is MISLEADING. It presents information in a way that could lead to incorrect conclusions."
    
    else:  # unknown
        return f"We cannot verify this claim about {topic} with sufficient confidence. More information or context would be needed to determine its accuracy."

def verify_claim(claim):
    """
    Verify a claim against the fact database and generate a detailed response.
    """
    # Use our new fact checker for real-world verification
    return fact_checker.verify_claim(claim)

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/test_fact_checker.html')
def test_fact_checker():
    return send_from_directory(app.static_folder, 'test_fact_checker.html')

@app.route('/test.html')
def test():
    return send_from_directory(app.static_folder, 'test.html')

@app.route('/api/analyze/claims', methods=['POST'])
def analyze_claims():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
            
        text = data['text']
        print(f"Received text for analysis: {text[:100]}...")  # Debug log
        
        # Extract claims and calculate percentages
        try:
            claims = extract_claims(text)
            print(f"Extracted {len(claims)} claims")  # Debug log
            if not claims:
                print("No claims were extracted from the text")
                return jsonify({
                    'claims': [],
                    'total_claims': 0,
                    'message': 'No claims were found in the provided text.'
                })
        except Exception as e:
            import traceback
            print(f"Error extracting claims: {str(e)}")
            print(traceback.format_exc())  # Print full traceback
            return jsonify({"error": f"Error extracting claims: {str(e)}"}), 500
            
        try:
            claim_percentages = calculate_claim_percentages(claims)
            print(f"Calculated claim percentages: {claim_percentages}")  # Debug log
        except Exception as e:
            import traceback
            print(f"Error calculating claim percentages: {str(e)}")
            print(traceback.format_exc())  # Print full traceback
            return jsonify({"error": f"Error calculating claim percentages: {str(e)}"}), 500
        
        # Verify each claim
        verified_claims = []
        for claim_data in claim_percentages:
            try:
                claim = claim_data['claim']
                verification = fact_checker.verify_claim(claim)
                
                verified_claims.append({
                    'claim': claim,
                    'percentage': claim_data['percentage'],
                    'verification': verification
                })
            except Exception as e:
                import traceback
                print(f"Error verifying claim '{claim}': {str(e)}")
                print(traceback.format_exc())  # Print full traceback
                verified_claims.append({
                    'claim': claim,
                    'percentage': claim_data['percentage'],
                    'verification': {
                        "verified": "error",
                        "confidence": 0,
                        "explanation": f"Error during verification: {str(e)}",
                        "related_facts": [],
                        "sources": [],
                        "counter_arguments": [],
                        "reason": "An error occurred during verification."
                    }
                })
        
        return jsonify({
            'claims': verified_claims,
            'total_claims': len(claims)
        })
    except Exception as e:
        import traceback
        print(f"Error in analyze_claims: {str(e)}")
        print(traceback.format_exc())  # Print full traceback
        return jsonify({"error": str(e)}), 500

@app.route('/api/microphones', methods=['GET'])
def get_microphones():
    """Get a list of available microphones."""
    microphones = vtt.list_microphones()
    return jsonify(microphones)

@app.route('/api/voice-to-text', methods=['POST'])
def voice_to_text():
    temp_file = None
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']
        
        # Create a temporary file with a .wav extension
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_path = temp_file.name
        temp_file.close()
        
        # Save the uploaded file
        audio_file.save(temp_path)
        
        # Process the audio file using our VoiceToText class
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Record the audio
            audio_data = recognizer.record(source)
            
            # Try to recognize the speech
            result = {
                "success": False,
                "text": None,
                "error": None
            }
            
            # Try Google's service first
            try:
                text = recognizer.recognize_google(audio_data, language="en-US")
                result["success"] = True
                result["text"] = text
                result["service"] = "google"
            except sr.UnknownValueError:
                result["error"] = "Speech recognition could not understand the audio. Please speak more clearly."
            except sr.RequestError as e:
                result["error"] = f"Google Speech Recognition service error: {e}"
                
            # If Google fails and Sphinx is available, try Sphinx (offline recognition)
            if not result["success"] and hasattr(vtt, 'SPHINX_AVAILABLE') and vtt.SPHINX_AVAILABLE:
                try:
                    text = recognizer.recognize_sphinx(audio_data)
                    result["success"] = True
                    result["text"] = text
                    result["service"] = "sphinx"
                except Exception as e:
                    result["error"] = f"Sphinx recognition failed: {e}"
            
            if result["success"]:
                return jsonify(result)
            else:
                return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"Error processing audio: {str(e)}"}), 500
    finally:
        # Clean up the temporary file
        if temp_file and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """Analyze text using GPT and store results in database."""
    try:
        data = request.json
        text = data.get('text')
        analysis_type = data.get('analysis_type', 'general')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Analyze text using GPT
        analysis_result = gpt_analyzer.analyze_text(text, analysis_type)
        
        if analysis_result['success']:
            # Save to database
            analysis_id = db.save_analysis(
                text=text,
                analysis_type=analysis_type,
                results=analysis_result['results'],
                source='gpt-4',
                confidence_score=analysis_result.get('confidence_score')
            )
            
            # Add database ID to response
            analysis_result['analysis_id'] = analysis_id
            
            return jsonify(analysis_result)
        else:
            return jsonify({"error": analysis_result['error']}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify-claim', methods=['POST'])
def verify_claim_endpoint():
    """Verify a specific claim using GPT."""
    try:
        data = request.json
        claim = data.get('claim')
        
        if not claim:
            return jsonify({"error": "No claim provided"}), 400
        
        # Verify claim using GPT
        verification_result = gpt_analyzer.verify_claim(claim)
        
        if verification_result['success']:
            # Save to database
            analysis_id = db.save_analysis(
                text=claim,
                analysis_type='claim_verification',
                results=verification_result['verification'],
                source='gpt-4',
                confidence_score=verification_result['verification'].get('confidence_score')
            )
            
            # Add database ID to response
            verification_result['analysis_id'] = analysis_id
            
            return jsonify(verification_result)
        else:
            return jsonify({"error": verification_result['error']}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Retrieve a specific analysis by ID."""
    try:
        analysis = db.get_analysis(analysis_id)
        
        if analysis:
            return jsonify(analysis)
        else:
            return jsonify({"error": "Analysis not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recent-analyses', methods=['GET'])
def get_recent_analyses():
    """Get recent analyses."""
    try:
        limit = request.args.get('limit', default=10, type=int)
        analyses = db.get_recent_analyses(limit)
        return jsonify(analyses)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)