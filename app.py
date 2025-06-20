from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from news_fetcher import fetch_live_news, get_available_countries, get_available_categories
from model import predict_fake_news
from animations import add_animation
from gemini_analyze import test_gemini_connection
import os
import json
from datetime import datetime
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "verinews-secure-secret-key-1234567890")

@app.route('/')
def index():
    # Get country and category from query parameters, default to US and general
    country_code = request.args.get('country', 'us')
    category = request.args.get('category', None)
    search_term = request.args.get('q', '')
    page = request.args.get('page', None)
    
    # Fetch news based on selected country and category
    news = fetch_live_news(country_code, category, search_term, page=page)
    
    # Get available countries and categories for the dropdowns
    countries = get_available_countries()
    categories = get_available_categories()
    
    # Check if Gemini is available
    gemini_success, gemini_message = test_gemini_connection()
    gemini_available = gemini_success
    
    # Store next page token if it exists
    next_page = None
    if news and len(news) > 0 and 'next_page' in news[0]:
        next_page = news[0].get('next_page')
    
    return render_template(
        'index.html', 
        news=news, 
        countries=countries,
        categories=categories,
        selected_country=country_code,
        selected_category=category or "",
        search_term=search_term,
        gemini_available=gemini_available,
        gemini_status=gemini_message,
        next_page=next_page
    )

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get form data
        article_id = request.form.get('article_id', '')
        article_title = request.form.get('article_title', '')
        article_content = request.form.get('article_content', '')
        article_source = request.form.get('article_source', '')
        article_url = request.form.get('article_url', '')
        article_image = request.form.get('article_image', '')
        use_gemini = 'use_gemini' in request.form
        
        # Diagnostic information
        analysis_start_time = datetime.now()
        diagnostic_info = {
            'time': analysis_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'content_length': len(article_content),
            'gemini_requested': use_gemini
        }
        
        # Check if Gemini is available if requested
        if use_gemini:
            gemini_success, gemini_message = test_gemini_connection()
            diagnostic_info['gemini_connection_test'] = {
                'success': gemini_success,
                'message': gemini_message
            }
            
            if not gemini_success:
                flash(f"Gemini API issue: {gemini_message}. Using local model instead.", "warning")
                use_gemini = False
        
        # Use a longer text if available
        if not article_content or len(article_content) < 100:
            combined_content = f"{article_title}. This article appears to be from {article_source}. " + article_content
            diagnostic_info['content_enhanced'] = True
            diagnostic_info['original_length'] = len(article_content)
            diagnostic_info['enhanced_length'] = len(combined_content)
            article_content = combined_content
        
        # Predict using the model
        try:
            result, confidence, additional_data = predict_fake_news(
                article_content, 
                title=article_title,
                source=article_source,
                use_gemini=use_gemini
            )
            diagnostic_info['predict_result'] = result
            diagnostic_info['predict_confidence'] = confidence
        except Exception as e:
            error_trace = traceback.format_exc()
            diagnostic_info['error'] = str(e)
            diagnostic_info['traceback'] = error_trace
            result = "Error"
            confidence = 0.5
            additional_data = {"error": str(e)}
            flash(f"Error during analysis: {str(e)}", "error")
        
        # Get appropriate animation
        animation = add_animation(result, confidence)
        
        # Get Gemini data if used
        gemini_data = additional_data.get('gemini', None) if use_gemini else None
        diagnostic_info['gemini_data_received'] = bool(gemini_data)
        
        # Check for Gemini errors and set a flag
        gemini_error = False
        if gemini_data and not gemini_data.get("success", False):
            gemini_error = True
            diagnostic_info['gemini_error'] = gemini_data.get('error', 'Unknown error')
        
        # Save diagnostics to session for troubleshooting
        session['last_analysis_diagnostic'] = diagnostic_info
        
        return render_template(
            'result.html', 
            result=result,
            confidence=round(confidence * 100, 1),
            animation=animation,
            article_title=article_title,
            article_content=article_content,
            article_source=article_source,
            article_url=article_url,
            article_image=article_image,
            gemini_data=gemini_data,
            gemini_available=use_gemini,
            gemini_error=gemini_error,
            use_gemini=use_gemini,
            diagnostics=diagnostic_info
        )
    except Exception as e:
        # Global error handler
        error_trace = traceback.format_exc()
        app.logger.error(f"Error in analyze route: {str(e)}")
        app.logger.error(error_trace)
        flash(f"An error occurred during analysis: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for analyzing news article"""
    data = request.json
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing content field'}), 400
    
    article_content = data.get('content', '')
    article_title = data.get('title', '')
    article_source = data.get('source', '')
    use_gemini = data.get('use_gemini', False)
    
    # Analyze using the model
    try:
        result, confidence, additional_data = predict_fake_news(
            article_content,
            title=article_title,
            source=article_source,
            use_gemini=use_gemini
        )
        
        # Return results as JSON
        return jsonify({
            'result': result,
            'confidence': confidence,
            'additional_data': additional_data
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'result': 'Error',
            'confidence': 0.5
        }), 500

@app.route('/about')
def about():
    """Information about the VeriNews application"""
    return render_template('about.html')

@app.route('/test-gemini')
def test_gemini():
    """Test the Gemini API connection"""
    success, message = test_gemini_connection()
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/diagnostics')
def diagnostics():
    """View the last analysis diagnostic information"""
    diagnostics = session.get('last_analysis_diagnostic', {})
    if not diagnostics:
        flash("No diagnostic information available", "info")
        return redirect(url_for('index'))
    
    return render_template('diagnostics.html', diagnostics=diagnostics)

@app.template_filter('truncate_chars')
def truncate_chars(s, n=300):
    """Truncates a string to n characters with ellipsis"""
    if not s:
        return ""
    if len(s) <= n:
        return s[:n] + '...'

if __name__ == '__main__':
    app.run(debug=True)