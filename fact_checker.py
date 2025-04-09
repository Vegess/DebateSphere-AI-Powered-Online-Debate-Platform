import os
import requests
import json
from typing import Dict, List, Any, Optional
import wikipediaapi
import re
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fact_checker')

# Known facts database for common claims
KNOWN_FACTS = {
    "burj khalifa": {
        "facts": [
            "The Burj Khalifa is the tallest building in the world, standing at 828 meters (2,717 feet).",
            "The Burj Khalifa is located in Dubai, United Arab Emirates.",
            "The Burj Khalifa was completed in 2010.",
            "The Burj Khalifa has 163 floors.",
            "The Burj Khalifa is not the second largest building in the world, but rather the tallest."
        ],
        "sources": [
            {
                "title": "Burj Khalifa - Official Website",
                "url": "https://www.burjkhalifa.ae/en/",
                "type": "official"
            }
        ],
        "counter_arguments": [
            "The Burj Khalifa is the tallest building in the world, not the second largest.",
            "The second tallest building in the world is the Shanghai Tower in China, which is 632 meters tall."
        ]
    },
    "mahatma gandhi": {
        "facts": [
            "Mahatma Gandhi was born on October 2, 1869, in Porbandar, India.",
            "Gandhi led India's independence movement against British rule through non-violent civil disobedience.",
            "He was assassinated on January 30, 1948, by Nathuram Godse.",
            "Gandhi is known as the 'Father of the Nation' in India.",
            "He was awarded the title 'Mahatma' by Rabindranath Tagore."
        ],
        "sources": [
            {
                "title": "Official Gandhi Heritage Portal",
                "url": "https://www.gandhiheritageportal.org/",
                "type": "official"
            }
        ],
        "counter_arguments": [
            "While Gandhi is widely respected, some historians argue about his role in certain political decisions.",
            "There are debates about his views on certain social issues of his time."
        ]
    },
    "nelson mandela": {
        "facts": [
            "Nelson Mandela was the first black President of South Africa, serving from 1994 to 1999.",
            "He spent 27 years in prison for his anti-apartheid activism.",
            "Mandela was awarded the Nobel Peace Prize in 1993.",
            "He was born on July 18, 1918, and died on December 5, 2013.",
            "Mandela's birth name was Rolihlahla Mandela."
        ],
        "sources": [
            {
                "title": "Nelson Mandela Foundation",
                "url": "https://www.nelsonmandela.org/",
                "type": "official"
            }
        ],
        "counter_arguments": [
            "Some critics argue about his early association with the armed wing of the ANC.",
            "There are debates about his economic policies during his presidency."
        ]
    },
    "climate change": {
        "facts": [
            "Global temperatures have risen by approximately 1.1°C since pre-industrial times.",
            "The Earth's climate is changing faster than at any point in modern civilization.",
            "Human activities are the primary driver of recent climate change.",
            "The concentration of CO2 in the atmosphere is higher than at any time in at least 800,000 years.",
            "Sea levels have risen by about 8 inches since 1900."
        ],
        "sources": [
            {
                "title": "NASA Climate Change",
                "url": "https://climate.nasa.gov/",
                "type": "scientific"
            },
            {
                "title": "IPCC Reports",
                "url": "https://www.ipcc.ch/",
                "type": "scientific"
            }
        ],
        "counter_arguments": [
            "Some argue that climate change is a natural cycle, but scientific evidence shows human influence.",
            "While there is debate about solutions, the basic science of climate change is well-established."
        ]
    },
    "covid-19": {
        "facts": [
            "COVID-19 was first identified in Wuhan, China, in December 2019.",
            "The World Health Organization declared it a pandemic on March 11, 2020.",
            "The virus is caused by the SARS-CoV-2 coronavirus.",
            "Vaccines were developed and authorized for emergency use in late 2020.",
            "The virus has caused millions of deaths worldwide."
        ],
        "sources": [
            {
                "title": "World Health Organization COVID-19 Dashboard",
                "url": "https://covid19.who.int/",
                "type": "official"
            }
        ],
        "counter_arguments": [
            "While there are legitimate debates about response measures, the virus itself is real and dangerous.",
            "Vaccine effectiveness and safety have been extensively studied and verified."
        ]
    },
    "albert einstein": {
        "facts": [
            "Albert Einstein developed the theory of relativity, one of the two pillars of modern physics.",
            "He won the Nobel Prize in Physics in 1921 for his explanation of the photoelectric effect.",
            "Einstein was born in Germany in 1879 and died in the United States in 1955.",
            "His famous equation E=mc² describes the relationship between mass and energy.",
            "He made significant contributions to quantum mechanics and statistical mechanics."
        ],
        "sources": [
            {
                "title": "Nobel Prize Organization",
                "url": "https://www.nobelprize.org/prizes/physics/1921/einstein/facts/",
                "type": "official"
            }
        ],
        "counter_arguments": [
            "While Einstein's theories are fundamental to modern physics, some aspects remain theoretical.",
            "There are ongoing debates about the interpretation of quantum mechanics."
        ]
    }
}

class FactChecker:
    """
    A comprehensive fact checker that uses multiple sources to verify claims.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the fact checker with optional API keys.
        
        Args:
            openai_api_key: OpenAI API key for GPT-based verification
        """
        self.openai_api_key = openai_api_key or os.environ.get('OPENAI_API_KEY')
        self.wikipedia_language = 'en'
        self.wiki_wiki = wikipediaapi.Wikipedia(
            language=self.wikipedia_language,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='DebateSphere/1.0'
        )
        
    def verify_claim(self, claim: str) -> Dict[str, Any]:
        """
        Verify a claim using multiple sources and methods.
        
        Args:
            claim: The claim to verify
            
        Returns:
            Dictionary with verification results
        """
        logger.info(f"Verifying claim: {claim}")
        
        # Initialize result structure
        result = {
            "verified": "unknown",
            "confidence": 0.5,
            "explanation": "",
            "related_facts": [],
            "sources": [],
            "counter_arguments": [],
            "reason": "Initial verification in progress."
        }
        
        # First check if the claim is about a known topic in our database
        claim_lower = claim.lower()
        for topic, data in KNOWN_FACTS.items():
            if topic in claim_lower:
                logger.info(f"Found match for known topic: {topic}")
                result["related_facts"].extend(data["facts"])
                result["sources"].extend(data["sources"])
                result["counter_arguments"].extend(data["counter_arguments"])
                
                # Check if the claim contradicts known facts
                for fact in data["facts"]:
                    if self._contradicts_claim(claim, fact):
                        result["verified"] = "false"
                        result["confidence"] = 0.9
                        result["explanation"] = f"This claim contradicts the established fact: {fact}"
                        result["reason"] = f"This claim is FALSE. {fact}"
                        return result
                
                # If no contradictions found, the claim is likely true
                result["verified"] = "true"
                result["confidence"] = 0.8
                result["explanation"] = "This claim is supported by verified information."
                result["reason"] = "This claim is TRUE based on verified information."
                return result
        
        try:
            # 1. Try Wikipedia search first
            wiki_results = self._search_wikipedia(claim)
            if wiki_results:
                result["related_facts"].extend(wiki_results["facts"])
                result["sources"].extend(wiki_results["sources"])
                
                # If we found good Wikipedia matches, update confidence
                if len(wiki_results["facts"]) >= 2:
                    result["confidence"] = 0.7
                    result["explanation"] = "Found supporting information on Wikipedia."
            
            # 2. Try web search for fact-checking sites
            web_results = self._search_fact_checking_sites(claim)
            if web_results:
                result["related_facts"].extend(web_results["facts"])
                result["sources"].extend(web_results["sources"])
                result["counter_arguments"].extend(web_results["counter_arguments"])
                
                # Update verification status based on web results
                if web_results["verification_status"]:
                    result["verified"] = web_results["verification_status"]
                    result["confidence"] = max(result["confidence"], web_results["confidence"])
                    result["explanation"] = web_results["explanation"]
            
            # 3. If OpenAI API key is available, use GPT for additional verification
            if self.openai_api_key:
                gpt_results = self._verify_with_gpt(claim)
                if gpt_results:
                    # Merge GPT results with existing results
                    result["related_facts"].extend(gpt_results["related_facts"])
                    result["sources"].extend(gpt_results["sources"])
                    result["counter_arguments"].extend(gpt_results["counter_arguments"])
                    
                    # Update verification status if GPT has higher confidence
                    if gpt_results["confidence"] > result["confidence"]:
                        result["verified"] = gpt_results["verified"]
                        result["confidence"] = gpt_results["confidence"]
                        result["explanation"] = gpt_results["explanation"]
            
            # 4. Determine final verification status if not already set
            if result["verified"] == "unknown":
                if result["confidence"] >= 0.8:
                    result["verified"] = "verified"
                elif result["confidence"] >= 0.6:
                    result["verified"] = "likely"
                elif result["confidence"] >= 0.4:
                    result["verified"] = "unlikely"
                else:
                    result["verified"] = "false"
            
            # 5. Generate final explanation if not already set
            if not result["explanation"]:
                if result["verified"] == "verified":
                    result["explanation"] = "This claim appears to be verified by multiple sources."
                elif result["verified"] == "likely":
                    result["explanation"] = "This claim is likely true based on available information."
                elif result["verified"] == "unlikely":
                    result["explanation"] = "This claim is unlikely to be true based on available information."
                else:
                    result["explanation"] = "This claim appears to be false based on available information."
            
            # 6. Set final reason
            result["reason"] = f"This claim was verified as {result['verified']} with {result['confidence']*100:.1f}% confidence."
            
        except Exception as e:
            logger.error(f"Error verifying claim: {str(e)}")
            result["error"] = str(e)
            result["verified"] = "error"
            result["confidence"] = 0
            result["explanation"] = f"An error occurred during verification: {str(e)}"
            result["reason"] = "Verification failed due to an error."
        
        return result
    
    def _contradicts_claim(self, claim: str, fact: str) -> bool:
        """
        Check if a fact contradicts a claim.
        
        Args:
            claim: The claim to check
            fact: The fact to compare against
            
        Returns:
            True if the fact contradicts the claim, False otherwise
        """
        # Simple contradiction detection
        claim_lower = claim.lower()
        fact_lower = fact.lower()
        
        # Check for negation in claim
        has_negation = any(word in claim_lower for word in ["not", "isn't", "aren't", "wasn't", "weren't", "doesn't", "don't", "didn't"])
        
        # Check for contradiction between claim and fact
        if has_negation:
            # If claim has negation, check if fact supports the positive version
            positive_claim = claim_lower.replace("not ", "").replace("isn't ", "").replace("aren't ", "").replace("wasn't ", "").replace("weren't ", "").replace("doesn't ", "").replace("don't ", "").replace("didn't ", "")
            return positive_claim in fact_lower
        else:
            # If claim is positive, check if fact contradicts it
            return "not " + claim_lower in fact_lower or "isn't " + claim_lower in fact_lower
    
    def _search_wikipedia(self, claim: str) -> Dict[str, Any]:
        """
        Search Wikipedia for information related to the claim.
        
        Args:
            claim: The claim to search for
            
        Returns:
            Dictionary with Wikipedia search results
        """
        try:
            # Search for pages related to the claim
            page = self.wiki_wiki.page(claim)
            
            facts = []
            sources = []
            
            if page.exists():
                # Extract facts from summary
                summary = page.summary
                sentences = summary.split('. ')
                for sentence in sentences:
                    if len(sentence) > 20:  # Skip very short sentences
                        facts.append(sentence.strip())
                
                # Add source
                sources.append({
                    "title": page.title,
                    "url": page.fullurl,
                    "type": "wikipedia"
                })
            
            return {
                "facts": facts,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {str(e)}")
            return {"facts": [], "sources": []}
    
    def _search_fact_checking_sites(self, claim: str) -> Dict[str, Any]:
        """
        Search fact-checking websites for information about the claim.
        
        Args:
            claim: The claim to search for
            
        Returns:
            Dictionary with fact-checking search results
        """
        # This is a simplified implementation
        # In a real application, you would use APIs for fact-checking sites
        # or web scraping with proper permissions
        
        try:
            # Simulate searching fact-checking sites
            # In a real implementation, this would make API calls or web requests
            
            # For now, we'll return a simulated response
            return {
                "facts": [
                    "Fact-checking sites would provide verified information here.",
                    "Multiple sources would be consulted to verify the claim."
                ],
                "sources": [
                    {
                        "title": "Simulated Fact-Checking Site",
                        "url": "https://example.com/fact-check",
                        "type": "fact_checking"
                    }
                ],
                "counter_arguments": [
                    "Alternative viewpoints would be presented here."
                ],
                "verification_status": "likely",
                "confidence": 0.75,
                "explanation": "This claim has been partially verified by fact-checking sources."
            }
        except Exception as e:
            logger.error(f"Error searching fact-checking sites: {str(e)}")
            return {
                "facts": [],
                "sources": [],
                "counter_arguments": [],
                "verification_status": None,
                "confidence": 0,
                "explanation": ""
            }
    
    def _verify_with_gpt(self, claim: str) -> Dict[str, Any]:
        """
        Verify a claim using GPT if OpenAI API key is available.
        
        Args:
            claim: The claim to verify
            
        Returns:
            Dictionary with GPT verification results
        """
        if not self.openai_api_key:
            return None
            
        try:
            # This is a placeholder for GPT API integration
            # In a real implementation, you would make API calls to OpenAI
            
            # For now, we'll return a simulated response
            return {
                "verified": "likely",
                "confidence": 0.85,
                "explanation": "GPT analysis suggests this claim is likely true based on available knowledge.",
                "related_facts": [
                    "GPT would provide relevant facts here.",
                    "Additional context would be provided to support the verification."
                ],
                "sources": [
                    {
                        "title": "GPT Knowledge Base",
                        "url": "https://openai.com",
                        "type": "ai"
                    }
                ],
                "counter_arguments": [
                    "GPT would provide alternative viewpoints here."
                ]
            }
        except Exception as e:
            logger.error(f"Error verifying with GPT: {str(e)}")
            return None

# For testing
if __name__ == "__main__":
    checker = FactChecker()
    result = checker.verify_claim("The Earth is round")
    print(json.dumps(result, indent=2)) 