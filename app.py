from flask import Flask, render_template, request, jsonify
import os
import random
import re
import requests

app = Flask(__name__)

# Set NASA_KEY as an environment variable when deploying.
# DEMO_KEY is useful for basic testing but has rate limits.
NASA_KEY = os.environ.get("NASA_KEY", "DEMO_KEY")


STOP_WORDS = {
    "about", "after", "again", "also", "because",
    "being", "between", "could", "every", "from",
    "have", "into", "more", "other", "should",
    "their", "there", "these", "they", "this",
    "those", "through", "under", "very", "were",
    "which", "while", "with", "would", "your",
    "that", "what", "when", "where", "then",
    "than", "them", "been", "will", "some",
    "such", "only", "over", "does", "using"
}


def get_sentences(text):
    sentences = re.split(r"[.!?]+", text)

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 10
    ]


def get_keywords(text):
    words = re.findall(
        r"\b[a-zA-Z]+\b",
        text.lower()
    )

    frequency = {}

    for word in words:

        if (
            len(word) > 4
            and word not in STOP_WORDS
        ):
            frequency[word] = (
                frequency.get(word, 0) + 1
            )

    return sorted(
        frequency,
        key=frequency.get,
        reverse=True
    )[:10]


def create_summary(sentences, keywords):

    if not sentences:
        return [
            "Not enough text to create a summary."
        ]

    scored = []

    for sentence in sentences:

        score = 0
        lower_sentence = sentence.lower()

        for word in keywords:

            if word in lower_sentence:
                score += 1

        word_count = len(sentence.split())

        if 8 <= word_count <= 35:
            score += 1

        scored.append({
            "sentence": sentence,
            "score": score
        })

    scored.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return [
        item["sentence"]
        for item in scored[:3]
    ]


def find_definitions(sentences):

    definitions = []

    for sentence in sentences:

        lower = sentence.lower()

        if (
            " is " in lower
            or " are " in lower
            or " means " in lower
            or " refers to " in lower
            or "defined as" in lower
        ):

            if sentence not in definitions:
                definitions.append(sentence)

    return definitions[:6]


def make_questions(
    keywords,
    difficulty,
    amount
):

    if not keywords:
        keywords = ["the main concept"]

    templates = {

        "Easy": [
            "What is {topic}?",
            "Define {topic}.",
            "What does {topic} mean?"
        ],

        "Medium": [
            "Why is {topic} important?",
            "Explain how {topic} works.",
            "Give an example involving {topic}.",
            "How would you explain {topic} to a friend?"
        ],

        "Hard": [
            "Why is {topic} important?",
            "How could {topic} be used in real life?",
            "Compare {topic} with another concept.",
            "What could happen if {topic} changed?"
        ]
    }

    template_list = templates.get(
        difficulty,
        templates["Medium"]
    )

    questions = []

    for i in range(amount):

        topic = keywords[
            i % len(keywords)
        ]

        template = random.choice(
            template_list
        )

        questions.append(
            template.replace(
                "{topic}",
                topic
            )
        )

    return questions


# ==========================================
# STUDY SCORE
# ==========================================

def get_study_score(
    word_count,
    sentence_count,
    keywords,
    definitions
):

    score = 0

    if word_count >= 300:
        score += 40
    elif word_count >= 200:
        score += 30
    elif word_count >= 100:
        score += 20
    elif word_count >= 50:
        score += 10

    if sentence_count >= 10:
        score += 20
    elif sentence_count >= 5:
        score += 15
    elif sentence_count >= 2:
        score += 10

    score += min(
        len(keywords) * 2,
        20
    )

    score += min(
        len(definitions) * 3,
        20
    )

    if score > 100:
        score = 100

    return score


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# NOTES ANALYZER API
# ==========================================

@app.route(
    "/api/analyze",
    methods=["POST"]
)
def analyze():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error": "No data received."
        }), 400

    text = data.get(
        "text",
        ""
    ).strip()

    if not text:

        return jsonify({
            "error": "Please provide some notes."
        }), 400

    difficulty = data.get(
        "difficulty",
        "Medium"
    )

    try:

        amount = int(
            data.get(
                "amount",
                5
            )
        )

    except (
        ValueError,
        TypeError
    ):

        amount = 5

    if amount < 1:
        amount = 5

    amount = min(
        amount,
        15
    )

    words = re.findall(
        r"\b[a-zA-Z]+\b",
        text
    )

    sentences = get_sentences(text)

    keywords = get_keywords(text)

    summary = create_summary(
        sentences,
        keywords
    )

    definitions = find_definitions(
        sentences
    )

    questions = make_questions(
        keywords,
        difficulty,
        amount
    )

    # Study Score
    study_score = get_study_score(
        len(words),
        len(sentences),
        keywords,
        definitions
    )

    challenges = [

        "Close your notes and explain one topic from memory.",

        "Write down three things you remember without looking.",

        "Teach one of these topics to someone else.",

        "Explain the hardest concept using simple words.",

        "Answer one practice question without checking your notes."
    ]

    challenge = random.choice(
        challenges
    )

    return jsonify({

        # Notes Analyzer
        "wordCount": len(words),

        "sentenceCount": len(sentences),

        "topicCount": len(keywords),

        "keywords": keywords,

        # Automatic Summary
        "summary": summary,

        # Definition Finder
        "definitions": definitions,

        # Question Generator
        "questions": questions,

        # Study Score
        "studyScore": study_score,

        # Study Challenge
        "challenge": challenge
    })


# ==========================================
# NASA APOD API
# ==========================================

@app.route("/api/nasa")
def nasa():

    try:

        response = requests.get(

            "https://api.nasa.gov/planetary/apod",

            params={
                "api_key": NASA_KEY
            },

            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        return jsonify({

            "title": data.get(
                "title",
                "NASA Picture of the Day"
            ),

            "explanation": data.get(
                "explanation",
                ""
            ),

            "media_type": data.get(
                "media_type",
                "image"
            ),

            "url": data.get(
                "url",
                ""
            ),

            "hdurl": data.get(
                "hdurl",
                data.get("url", "")
            ),

            "date": data.get(
                "date",
                ""
            ),

            "copyright": data.get(
                "copyright",
                ""
            )
        })

    except requests.RequestException as error:

        print(
            "NASA API error:",
            error
        )

        return jsonify({

            "error":
                "NASA Picture of the Day is currently unavailable."

        }), 503


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(error):

    if request.path.startswith("/api/"):

        return jsonify({
            "error": "API endpoint not found."
        }), 404

    return render_template(
        "index.html"
    )


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True)



