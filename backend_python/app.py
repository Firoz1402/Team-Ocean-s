# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from detoxify import Detoxify
from dotenv import load_dotenv
import re
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)  # Enable CORS if needed
model = Detoxify('original')

@app.route('/quick-score', methods=['POST'])
def quick_toxicity():
    """Fast endpoint for real-time toxicity percentage"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        scores = model.predict(text)
        toxicity_percent = round(max(scores.values()) * 100, 1)
        
        return jsonify({
            'status': 'success',
            'toxicity_percent': toxicity_percent
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/analyze', methods=['POST'])
def detailed_analysis():
    """Detailed analysis with explanations"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        analysis = analyze_text(text)
        return jsonify({
            'status': 'success',
            'result': analysis
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def analyze_text(text):
    """Main analysis function"""
    # Get base predictions
    base_scores = {k: float(v) for k, v in model.predict(text).items()}

    # Identify top 2 toxic categories
    top_categories = sorted(base_scores.items(), key=lambda x: x[1], reverse=True)[:2]

    # Generate explanations in parallel
    with ThreadPoolExecutor() as executor:
        explanations = list(executor.map(
            lambda cat: get_category_explanation(text, cat[0], cat[1]),
            top_categories
        ))

    return {
        'overall_toxicity': round(100 * max(base_scores.values()), 1),
        'category_breakdown': [
            {
                'name': cat[0],
                'score': round(cat[1], 3),
                'percentage': round(100 * cat[1], 1)
            } for cat in top_categories
        ],
        'explanations': {
            cat[0]: explanations[i]
            for i, cat in enumerate(top_categories)
        }
    }

def get_category_explanation(text, category, original_score):
    """Explain contributions for a specific category"""
    # Extract meaningful phrases (1-2 word n-grams)
    words = re.findall(r'\b\w{3,}\b', text.lower())
    phrases = words + [
        ' '.join(words[i:i+2])
        for i in range(len(words)-1)
    ]

    # Calculate phrase impacts
    impacts = {}
    for phrase in set(phrases):
        modified = re.sub(rf'\b{re.escape(phrase)}\b', '', text, flags=re.I)
        new_score = model.predict(modified)[category]
        impact = original_score - new_score
        if impact > 0.01:
            impacts[phrase] = round(impact, 3)

    # Select top unique contributors
    sorted_impacts = sorted(impacts.items(), key=lambda x: x[1], reverse=True)
    unique_contributors = []
    seen_words = set()

    for phrase, impact in sorted_impacts:
        phrase_words = set(phrase.split())
        if not phrase_words & seen_words:
            unique_contributors.append({
                'phrase': phrase,
                'impact': impact,
                'contribution_percent': round(100 * impact / original_score)
            })
            seen_words.update(phrase_words)
        if len(unique_contributors) >= 3:
            break

    return unique_contributors


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, threaded=True)