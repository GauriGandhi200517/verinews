import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import numpy as np
from gemini_analyze import analyze_with_gemini

def load_model():
    try:
        # Use a valid pretrained model for text classification
        # roberta-base is a well-established model that definitely exists
        model_name = "roberta-base"
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = TFAutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
        
        print("Loaded pretrained model successfully")
        return model, tokenizer
    except Exception as e:
        print(f"Error loading model: {e}")
        # Fallback to a simple rule-based classifier if the model fails
        return create_fallback_model()

def create_fallback_model():
    """Creates a simple fallback mechanism when the main model fails to load"""
    print("Using fallback classification mechanism")
    
    # Define a simple keyword-based classifier
    fake_indicators = ['clickbait', 'shocking', 'you won\'t believe', 
                      'secret', 'conspiracy', 'they don\'t want you to know']
                      
    # Create simple classifier functions to mimic the expected interface
    class SimpleClassifier:
        def __call__(self, inputs):
            class Outputs:
                def __init__(self, logits):
                    self.logits = logits
            return Outputs(tf.constant([[0.0, 0.0]]))
    
    class SimpleTokenizer:
        def __call__(self, text, **kwargs):
            # Count how many fake indicators are in the text
            count = sum(1 for word in fake_indicators if word.lower() in text.lower())
            # Store this count for later use during prediction
            self.fake_count = count
            return {"fake_count": count}
    
    return SimpleClassifier(), SimpleTokenizer()

model, tokenizer = load_model()

def predict_fake_news(article, title=None, source=None, use_gemini=False):
    """
    Analyze news article for credibility using both the local model and optionally Google Gemini.
    
    Args:
        article (str): The article text to analyze
        title (str, optional): The title of the article
        source (str, optional): The source of the article
        use_gemini (bool): Whether to use Gemini API for enhanced analysis
        
    Returns:
        tuple: (result, confidence, additional_data)
            - result: 'Fake', 'Real', or 'Uncertain'
            - confidence: 0.0-1.0 confidence score
            - additional_data: Dictionary containing additional analysis information
    """
    result = "Uncertain"
    confidence = 0.5
    additional_data = {}
    
    # First, use the local model
    local_result, local_confidence = _predict_with_local_model(article)
    additional_data["local_model"] = {
        "result": local_result,
        "confidence": local_confidence
    }
    
    # If Gemini is requested, use it and combine results
    if use_gemini:
        gemini_analysis = analyze_with_gemini(article, title, source)
        additional_data["gemini"] = gemini_analysis
        
        # Convert Gemini's 1-10 score to a 0-1 range, inverting since 
        # high score from Gemini means "real" but high confidence in our system means "fake"
        gemini_confidence = 1 - (gemini_analysis["credibility_score"] / 10.0)
        
        # Combine local model and Gemini (weighted average)
        # Give Gemini higher weight if it succeeded
        if gemini_analysis["success"]:
            combined_confidence = (local_confidence * 0.3) + (gemini_confidence * 0.7)
        else:
            # If Gemini analysis failed, rely more on local model
            combined_confidence = local_confidence
            
        confidence = combined_confidence
        # Set result based on combined confidence
        if confidence > 0.7:
            result = "Fake"
        elif confidence < 0.3:
            result = "Real"
        else:
            result = "Uncertain"
    else:
        # Use only local model results if Gemini is not requested
        result = local_result
        confidence = local_confidence
    
    return result, confidence, additional_data

def _predict_with_local_model(article):
    """Internal helper to get prediction from local model only"""
    if model is None or tokenizer is None:
        return "Error", 0.0
    
    try:
        # Handle fallback simple model
        if hasattr(tokenizer, 'fake_count'):
            # Simple rule-based prediction based on keyword matching
            fake_count = sum(1 for word in ['clickbait', 'shocking', 'conspiracy'] 
                            if word.lower() in article.lower())
            fake_prob = min(fake_count * 0.2, 0.9)  # Scale probability based on matches
            result = 'Fake' if fake_prob > 0.5 else 'Real'
            confidence = fake_prob if result == 'Fake' else 1 - fake_prob
            return result, confidence
            
        # Normal model prediction flow
        max_length = 512
        inputs = tokenizer(article, return_tensors="tf", max_length=max_length, 
                          truncation=True, padding="max_length")
        
        outputs = model(inputs)
        logits = outputs.logits.numpy()
        
        # Convert logits to probabilities
        probabilities = tf.nn.softmax(logits, axis=-1).numpy()[0]
        
        # For binary classification: Index 1 typically indicates positive class probability
        fake_prob = float(probabilities[1])
        
        result = 'Fake' if fake_prob > 0.7 else 'Real'
        confidence = fake_prob if result == 'Fake' else 1 - fake_prob
        
        return result, confidence
        
    except Exception as e:
        print(f"Error during prediction: {e}")
        # Ultimate fallback
        return "Uncertain", 0.5