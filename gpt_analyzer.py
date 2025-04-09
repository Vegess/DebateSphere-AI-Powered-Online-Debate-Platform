import openai
from typing import Dict, List, Optional
import os
from datetime import datetime
import json

class GPTAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the GPT analyzer with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.use_gpt = bool(self.api_key)
        
        if self.use_gpt:
            openai.api_key = self.api_key
        else:
            print("Warning: No OpenAI API key found. Running in fallback mode with simulated responses.")
    
    def analyze_text(self, text: str, analysis_type: str = "general") -> Dict:
        """
        Analyze text using GPT-4 for various types of analysis.
        
        Args:
            text: The text to analyze
            analysis_type: Type of analysis to perform (general, claims, sentiment, etc.)
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.use_gpt:
            return self._fallback_analysis(text, analysis_type)
            
        # Prepare the prompt based on analysis type
        prompt = self._get_analysis_prompt(text, analysis_type)
        
        try:
            # Call GPT-4 API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert fact-checker and text analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse the response
            analysis = self._parse_gpt_response(response.choices[0].message.content)
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "results": analysis,
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-4"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _fallback_analysis(self, text: str, analysis_type: str) -> Dict:
        """Provide fallback analysis when GPT is not available."""
        # Simple fallback analysis
        words = text.split()
        word_count = len(words)
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        sentence_count = len(sentences)
        
        if analysis_type == "claims":
            # Simulate claim extraction
            claims = []
            for i, sentence in enumerate(sentences[:3]):  # Take first 3 sentences as claims
                claims.append({
                    "text": sentence,
                    "verifiable": i % 2 == 0,  # Alternate between verifiable and not
                    "confidence": 0.7 + (i * 0.1),
                    "suggested_sources": ["Wikipedia", "News articles", "Academic papers"]
                })
            
            return {
                "success": True,
                "analysis_type": "claims",
                "results": {"claims": claims},
                "timestamp": datetime.now().isoformat(),
                "model": "fallback"
            }
            
        elif analysis_type == "sentiment":
            # Simulate sentiment analysis
            sentiment = "positive" if "good" in text.lower() or "great" in text.lower() else "negative"
            
            return {
                "success": True,
                "analysis_type": "sentiment",
                "results": {
                    "overall_sentiment": sentiment,
                    "emotions": ["joy", "trust"],
                    "intensity": 0.7,
                    "bias_indicators": []
                },
                "timestamp": datetime.now().isoformat(),
                "model": "fallback"
            }
            
        else:  # general analysis
            return {
                "success": True,
                "analysis_type": "general",
                "results": {
                    "topics": ["Topic 1", "Topic 2"],
                    "key_points": ["Point 1", "Point 2"],
                    "style": "informative",
                    "biases": [],
                    "credibility": "medium"
                },
                "timestamp": datetime.now().isoformat(),
                "model": "fallback"
            }
    
    def _get_analysis_prompt(self, text: str, analysis_type: str) -> str:
        """Generate the appropriate prompt based on analysis type."""
        base_prompt = f"Please analyze the following text:\n\n{text}\n\n"
        
        if analysis_type == "claims":
            return base_prompt + """
            Please identify and analyze any factual claims in the text. For each claim:
            1. Extract the exact claim
            2. Assess its verifiability
            3. Provide a confidence score (0-1)
            4. Suggest potential sources for verification
            
            Format your response as a JSON object with a 'claims' array containing objects with:
            - text: the claim text
            - verifiable: boolean
            - confidence: number
            - suggested_sources: array of strings
            """
        
        elif analysis_type == "sentiment":
            return base_prompt + """
            Please analyze the sentiment and emotional content of the text. Include:
            1. Overall sentiment (positive/negative/neutral)
            2. Key emotions expressed
            3. Intensity of emotions
            4. Any bias indicators
            
            Format your response as a JSON object with sentiment analysis results.
            """
        
        else:  # general analysis
            return base_prompt + """
            Please provide a comprehensive analysis of the text, including:
            1. Main topics and themes
            2. Key arguments or points
            3. Writing style and tone
            4. Potential biases or limitations
            5. Overall credibility assessment
            
            Format your response as a JSON object with the analysis results.
            """
    
    def _parse_gpt_response(self, response: str) -> Dict:
        """Parse the GPT response into a structured format."""
        try:
            # The response should be in JSON format
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            # If response is not valid JSON, return it as raw text
            return {"raw_analysis": response}
    
    def verify_claim(self, claim: str) -> Dict:
        """
        Verify a specific claim using GPT-4.
        
        Args:
            claim: The claim to verify
            
        Returns:
            Dictionary containing verification results
        """
        if not self.use_gpt:
            # Fallback verification
            return {
                "success": True,
                "claim": claim,
                "verification": {
                    "status": "inconclusive",
                    "confidence": 0.6,
                    "evidence": "Simulated evidence for testing",
                    "sources": ["Wikipedia", "News articles"],
                    "caveats": ["This is a simulated response"]
                },
                "timestamp": datetime.now().isoformat(),
                "model": "fallback"
            }
            
        prompt = f"""
        Please verify the following claim: "{claim}"
        
        Provide:
        1. Verification status (true/false/inconclusive)
        2. Confidence score (0-1)
        3. Supporting evidence
        4. Potential sources
        5. Any caveats or limitations
        
        Format your response as a JSON object with verification results.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert fact-checker."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            verification = self._parse_gpt_response(response.choices[0].message.content)
            
            return {
                "success": True,
                "claim": claim,
                "verification": verification,
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-4"
            }
            
        except Exception as e:
            return {
                "success": False,
                "claim": claim,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            } 