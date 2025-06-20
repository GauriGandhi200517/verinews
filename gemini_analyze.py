import google.generativeai as genai
import os
import json
import re
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API with improved error handling
def configure_gemini():
    """Configure the Gemini API with proper error handling"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            print("WARNING: Gemini API key not found or using placeholder value")
            return False
        
        # Test the API key format (basic validation)
        if not api_key.startswith("AIza"):
            print("WARNING: Gemini API key appears to be in incorrect format")
            return False
            
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return False

# Initialize the configuration
gemini_configured = configure_gemini()

def analyze_with_gemini(article_text, article_title=None, article_source=None, max_retries=2):
    """
    Analyze article content using Google Gemini AI with improved error handling.
    
    Args:
        article_text (str): The article content to analyze
        article_title (str, optional): The title of the article
        article_source (str, optional): The source of the article
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        dict: Results of the analysis including credibility score, reasoning, and recommendations
    """
    # Check if Gemini is properly configured
    if not gemini_configured:
        return {
            "success": False,
            "error": "Gemini API not properly configured",
            "credibility_score": 5,
            "reasoning": "Unable to analyze without a valid Gemini API key. Please add your API key to the .env file.",
            "recommendations": "Consider manual fact-checking through trusted sources."
        }
        
    # Clean and prepare the article text
    max_length = 30000  # Gemini 2.0 has a higher context limit than 1.0
    if article_text:
        # Make sure the article text isn't too short for meaningful analysis
        if len(article_text.strip()) < 50:
            return {
                "success": False,
                "error": "Article text too short for meaningful analysis",
                "credibility_score": 5,
                "reasoning": "The article content is too brief for AI analysis. Consider providing more context.",
                "recommendations": "This content is too short to analyze. Please provide a longer article."
            }
        article_text = article_text[:max_length] 
    else:
        return {
            "success": False,
            "error": "No article content provided",
            "credibility_score": 5,
            "reasoning": "No article content was provided for analysis.",
            "recommendations": "Please provide article content for analysis."
        }
    
    if not article_title:
        article_title = "Unknown title"
    
    if not article_source:
        article_source = "Unknown source"
            
    # Format the context for Gemini with structured prompt
    prompt = f"""
You are FactVerifier, an advanced AI tool for news article analysis.

ARTICLE INFORMATION:
Title: {article_title}
Source: {article_source}
Content: {article_text}

TASK:
Please analyze this news article for credibility and provide:

1. A credibility score from 1-10 (1=completely false, 10=highly credible)
2. Detailed reasoning for your assessment (identify potential misinformation, bias, factual claims)
3. Recommendations for how a reader should interpret this information

FORMAT YOUR RESPONSE IN THIS EXACT JSON STRUCTURE:
{{
  "credibility_score": [number between 1-10],
  "reasoning": "[your detailed analysis]",
  "recommendations": "[specific guidance for readers]"
}}
"""
    
    # Implement retry logic
    for attempt in range(max_retries + 1):
        try:
            # Generate response from Gemini with safety settings
            # Try with the newer model first
            try:
                model = genai.GenerativeModel(
                    'gemini-2.0-flash-exp',  # Using the newer, more powerful model
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                    ],
                    generation_config={
                        "temperature": 0.1,  # Lower temperature for more factual responses
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 4096,  # Higher output token limit for Gemini 2.0
                    }
                )
                
                # Generate content WITHOUT response_mime_type parameter which is causing the error
                response = model.generate_content(prompt)
                model_used = "gemini-2.0-flash-exp"
            except Exception as model_error:
                print(f"Error with gemini-2.0-flash-exp model: {model_error}")
                # Fall back to gemini-pro
                model = genai.GenerativeModel(
                    'gemini-pro',
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                    ],
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 2048,
                    }
                )
                # Generate content WITHOUT response_mime_type parameter
                response = model.generate_content(prompt)
                model_used = "gemini-pro"
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")
                
            response_text = response.text.strip()
            
            # Process the response text using multiple parsing methods
            result = parse_gemini_response(response_text)
            
            if result:
                result["model"] = model_used  # Add model info to response
                if model_used == "gemini-pro":
                    result["fallback"] = True
                return result
                
            # If we reach here, all parsing attempts failed
            if attempt < max_retries:
                print(f"Parsing failed on attempt {attempt+1}, retrying...")
                time.sleep(1)  # Wait before retrying
                continue
            else:
                return {
                    "success": False,
                    "error": "Failed to parse Gemini response after multiple attempts",
                    "credibility_score": 5,
                    "reasoning": "The AI generated a response but it couldn't be properly parsed.",
                    "recommendations": "Please try again or use manual fact-checking methods.",
                    "raw_response": response_text[:500],  # Include part of the raw response for debugging
                    "model": model_used
                }
                
        except Exception as api_error:
            print(f"Gemini API error on attempt {attempt+1}: {api_error}")
            
            if attempt < max_retries:
                print("Retrying...")
                time.sleep(1.5)  # Wait before retrying
                continue
            else:
                return {
                    "success": False,
                    "error": f"Gemini API error after {max_retries+1} attempts: {str(api_error)}",
                    "credibility_score": 5,
                    "reasoning": "The AI service encountered persistent errors during analysis.",
                    "recommendations": "Please try again later or use alternative fact-checking methods."
                }
    
    # This should not be reached, but just in case
    return {
        "success": False,
        "error": "Unexpected error in Gemini analysis flow",
        "credibility_score": 5,
        "reasoning": "An unexpected error occurred during analysis.",
        "recommendations": "Please try again or verify the information through trusted news sources."
    }

# Rest of the file remains the same
def parse_gemini_response(response_text):
    """
    Parse the Gemini API response using multiple methods
    
    Args:
        response_text (str): Text response from Gemini API
        
    Returns:
        dict: Parsed response or None if parsing failed
    """
    # Method 1: Direct JSON parsing
    try:
        # Clean up response text by finding JSON block
        json_match = re.search(r'({[\s\S]*})', response_text)
        if json_match:
            json_str = json_match.group(1)
            # Fix common JSON formatting issues
            json_str = json_str.replace('\n', ' ').replace('\\', '\\\\')
            analysis_data = json.loads(json_str)
            
            # Validate and ensure all required fields
            credibility_score = int(float(analysis_data.get("credibility_score", 5)))
            # Ensure score is within range
            credibility_score = max(1, min(10, credibility_score))
            
            return {
                "success": True,
                "credibility_score": credibility_score,
                "reasoning": analysis_data.get("reasoning", "Analysis completed successfully."),
                "recommendations": analysis_data.get("recommendations", "Consider cross-referencing with trusted sources."),
                "parse_method": "json"
            }
    except Exception as json_error:
        print(f"JSON parsing failed: {json_error}")
    
    # Method 2: Regex parsing
    try:
        # Extract score using regex
        score_match = re.search(r'credibility[\s_]score["\s:]*(\d+(?:\.\d+)?)', response_text, re.IGNORECASE)
        if score_match:
            score = int(float(score_match.group(1)))
            
            # Extract reasoning - look for reasoning section with flexible pattern matching
            reasoning_pattern = r'reasoning["\s:]*(.*?)(?:recommendations|$)'
            reasoning_match = re.search(reasoning_pattern, response_text, re.IGNORECASE | re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "Analysis completed, detailed reasoning unavailable."
            
            # Extract recommendations - be flexible with pattern matching
            rec_pattern = r'recommendations["\s:]*(.*?)(?:$|\})'
            rec_match = re.search(rec_pattern, response_text, re.IGNORECASE | re.DOTALL)
            recommendations = rec_match.group(1).strip() if rec_match else "Consider cross-referencing with trusted sources."
            
            # Clean up any lingering quotes or formatting
            reasoning = re.sub(r'^["\s]+|["\s]+$', '', reasoning)
            recommendations = re.sub(r'^["\s]+|["\s]+$', '', recommendations)
            
            return {
                "success": True,
                "credibility_score": max(1, min(10, score)),
                "reasoning": reasoning,
                "recommendations": recommendations,
                "parse_method": "regex"
            }
    except Exception as regex_error:
        print(f"Regex parsing failed: {regex_error}")
    
    # Method 3: Line-by-line extraction
    try:
        lines = response_text.split('\n')
        score = 5
        reasoning = ""
        recommendations = ""
        
        for line in lines:
            line = line.strip()
            if "credibility score" in line.lower() or "credibility_score" in line.lower():
                # Extract numbers from this line
                numbers = re.findall(r'\d+(?:\.\d+)?', line)
                if numbers:
                    score = int(float(numbers[0]))
            elif "reasoning" in line.lower() and ":" in line:
                reasoning = line.split(":", 1)[1].strip()
            elif "recommendation" in line.lower() and ":" in line:
                recommendations = line.split(":", 1)[1].strip()
                
        # If we found at least a score, return what we have
        if reasoning or recommendations:
            return {
                "success": True,
                "credibility_score": max(1, min(10, score)),
                "reasoning": reasoning or "Analysis completed, detailed reasoning unavailable.",
                "recommendations": recommendations or "Consider cross-referencing with trusted sources.",
                "parse_method": "line-by-line"
            }
    except Exception as line_error:
        print(f"Line-by-line parsing failed: {line_error}")
        
    # All parsing methods failed
    return None


def test_gemini_connection():
    """Test if the Gemini API connection is working properly"""
    if not gemini_configured:
        return False, "Gemini API key not configured"
    
    try:
        # Try with gemini-2.0-flash-exp first
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            # Remove response_mime_type parameter
            response = model.generate_content(
                "Respond with only the text 'Connection successful' if you can read this message."
            )
            
            if response and response.text and "Connection successful" in response.text:
                return True, "Gemini 2.0 Flash API connection successful"
        except Exception as e:
            print(f"Gemini 2.0 Flash test failed, falling back to gemini-pro: {e}")
            # If the newer model fails, try gemini-pro as fallback
            model = genai.GenerativeModel('gemini-pro')
            # Remove response_mime_type parameter
            response = model.generate_content(
                "Respond with only the text 'Connection successful' if you can read this message."
            )
            
            if response and response.text and "Connection successful" in response.text:
                return True, "Gemini Pro API connection successful (Flash model unavailable)"
            else:
                return False, f"Unexpected response from Gemini API: {response.text[:50]}..."
    except Exception as e:
        error_message = str(e)
        if "invalid api key" in error_message.lower():
            return False, "Invalid Gemini API key"
        return False, f"Gemini API connection failed: {error_message}"


if __name__ == "__main__":
    # Test connection if run directly
    success, message = test_gemini_connection()
    print(f"Connection test: {message}")
    if success:
        print("Testing analysis with a sample article...")
        sample = "Scientists have discovered a new species of butterfly in the Amazon rainforest. The discovery was made by a team from the University of Brazil during their annual expedition. The butterfly, named Amazonia brilliantis, features stunning blue wings and is believed to be endangered due to habitat loss."
        result = analyze_with_gemini(sample, "New Butterfly Species Discovered", "Science Daily")
        print(f"Analysis result: {json.dumps(result, indent=2)}")