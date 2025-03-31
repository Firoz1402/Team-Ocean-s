from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai

import os
import json

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)
CORS(app)

# toxicity_analyzer.py
from detoxify import Detoxify
import re
import numpy as np
from concurrent.futures import ThreadPoolExecutor

model = Detoxify('original')

def analyze_text(text):
    """Main analysis function"""
    
    # Get base predictions
    base_scores = {k: float(v) for k, v in model.predict(text).items()}

    # Identify top 2 toxic categories
    top_categories = sorted(base_scores.items(), key=lambda x: x[1], reverse=True)[:2]

    return {
        'overall_toxicity': round(100 * max(base_scores.values()), 1),
        'category_breakdown': [
            {
                'name': cat[0],
                'score': round(cat[1], 3),
                'percentage': round(100 * cat[1], 1)
            } for cat in top_categories
        ],
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

def print_results(analysis):
    """Console-friendly output"""
    print(f"Overall Toxicity: {analysis['overall_toxicity']}%")
    print("\nTop Categories:")
    for cat in analysis['category_breakdown']:
        print(f" - {cat['name'].title()}: {cat['percentage']}%")

    print("\nExplanations:")
    for category, explanation in analysis['explanations'].items():
        print(f"\n{category.title()}:")
        for item in explanation:
            print(f"  - '{item['phrase']}': Contributed {item['contribution_percent']}%")

@app.route("/detoxify", methods=["GET"])
def generate_clean_speech():

    text = request.args.get("text")

    analysis = analyze_text(text)

    content = f"""You will convert a hate speech text into a non-hate speech text by
    modifying only the text spans which contain hate speech. Do not
    change the meaning of the original text. If you cannot convert the
    original text into a non-hate speech text, just convert it into a text
    with reduced hate intensity.

    Below are some demonstrations:

    Hate Speech: It is incredible what we did in these years. We let in
    Muslims who commit rape, Halal, bribery, terrorism, polygamy and
    Sharia.
    Non-hate Speech: It is incredible what we did in these years. We let
    in some muslims who commit crimes.
    Hate Speech: If they love Sharia law so much, why do not they go off
    and live in a Muslim country?
    Non-hate Speech: If they love Sharia law so much, why do not they
    live in another country?
    Hate Speech: Islam=evil. Islam is invading us and trying to take over
    countries. It does not follow the scriptures that say ’you shall not envy
    anyone anything’ Stop islam!
    Non-hate Speech: Some Muslims who misinterpret their scriptures are
    invading us and trying to control our countries. They do not follow
    the scriptures that say ’you shall not envy anyone anything’

    After converting the text into non-hate speech, you will form a JSON object which two distinct keys.
    The first key would be called `toxic_words`, whose value will be an array of all the words from the hate speech that are considered as toxic.
    The second key would be called `reasons`, whose value will also be an array, containing the reason behind what makes the toxic_words as toxic, each index of the reasons
    array will contain the reason behind the toxicity of the word in the same index in the toxic_words array

    Hate speech: Someone is a fucking idiot!
    Toxic words: fucking, idiot

    Now, you will convert the following text into non-hate speech and also list out the words that were profane, offensive, obscene or explicit, and provide the reasons in a
    well formed JSON object with the keys that are stated. Plus, add the new non-hate speech to a new key in that same JSON object. The key name will be `cleaned_speech`

    In case, you don't recognise any hate speech return a JSON with the keys `toxic_words` and `reasons` as empty arrays, and the same input speech as the `cleaned_speech` values.

    Do not return any extra text or content, just the JSON object.

    Hate Speech: {text}
    Non-hate Speech:"""

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=content
    )

    result = json.loads(response.text[7:-4])
    result["analysis"] = analysis

    print("RESULT: ", result)

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True) 