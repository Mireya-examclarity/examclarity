from flask import Flask, render_template, request, jsonify
import os
import re
import random
import requests

app = Flask(__name__)

# NASA API key
NASA_KEY = os.environ.get("NASA_KEY", "DEMO_KEY")


# Words that are not very useful as keywords
STOP_WORDS = {
    "about", "after", "again", "also", "because", "being",
    "between", "could", "every", "from", "have", "into",
    "more", "other", "should", "their", "there", "these",
    "they", "this", "those", "through", "under", "very",
    "were", "which", "while", "with", "would", "your",
    "that", "what", "when", "where", "then", "than",
    "them", "been", "will", "some", "such", "only"
}


def get_words(text):
    """Get words from the notes."""
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())


def get_sentences(text):
    """Split notes into sentences."""
    parts = re.split(r"[.!?]+", text)

    sentences = []

    for part in parts:
        part = part.strip()

        if len(part) > 10:
            sentences.append(part)

    return sentences


def get_keywords(text):
    """Find words that appear often in the notes."""

    words = get_words(text)
    frequency = {}

    for word in words:

        if len(word) < 5:
            continue

        if word in STOP_WORDS:
            continue

        if word not in frequency:
            frequency[word] = 0

        frequency[word] += 1

    # Sort words by how many times they appear
    keywords = sorted(
        frequency,
        key=frequency.get,
        reverse=True
    )

    return keywords[:10]


def make_summary(sentences, keywords):
    """Choose important sentences from the notes."""

    if not sentences:
        return ["There is not enough text for a summary."]

    scored_sentences = []

    for sentence in sentences:

        score = 0
        lower_sentence = sentence.lower()

        for keyword in keywords:
            if keyword in lower_sentence:
                score += 1

        # Sentences with a normal length get one extra point
        words = sentence.split()

        if len(words) >= 8 and len(words) <= 35:
            score += 1

        scored_sentences.append(
            [sentence, score]
        )

    scored_sentences.sort(
        key=lambda x: x[1],
        reverse=True
    )

    summary = []

    for item in scored_sentences[:3]:
        summary.append(item[0])

    return summary


def find_definitions(sentences):
    """Find simple definition sentences."""

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


def make_questions(keywords, difficulty, amount):
    """Create questions using the keywords."""

    if not keywords:
        keywords = ["the main topic"]

    questions = []

    easy_questions = [
        "What is {topic}?",
        "Define {topic}.",
        "What does {topic} mean?"
    ]

    medium_questions = [
        "Why is {topic} important?",
        "Explain how {topic} works.",
        "Give an example of {topic}.",
        "How would you explain {topic} to a friend?"
    ]

    hard_questions = [
        "Why is {topic} important?",
        "How could {topic} be used in real life?",
        "Compare {topic} with another concept.",
        "What could happen if {topic} changed?"
    ]

    if difficulty == "Easy":
        templates = easy_questions

    elif difficulty == "Hard":
        templates = hard_questions

    else:
        templates = medium_questions

    for i in range(amount):

        topic = keywords[i % len(keywords)]

        question = random.choice(templates)

        question = question.replace(
            "{topic}",
            topic
        )

        questions.append(question)

    return questions


def calculate_score(
    word_count,
    sentence_count,
    keyword_count,
    definition_count
):
    """Calculate a simple study score."""

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

    score += min(keyword_count * 2, 20)

    score += min(definition_count * 3, 20)

    if score > 100:
        score = 100

    return score


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data received."
        }), 400

    text = data.get("text", "").strip()

    if text == "":
        return jsonify({
            "error": "Please enter some notes."
        }), 400

    difficulty = data.get(
        "difficulty",
        "Medium"
    )

    try:
        amount = int(
            data.get("amount", 5)
        )
    except:
        amount = 5

    if amount < 1:
        amount = 1

    if amount > 15:
        amount = 15

    words = get_words(text)

    sentences = get_sentences(text)

    keywords = get_keywords(text)

    summary = make_summary(
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

    score = calculate_score(
        len(words),
        len(sentences),
        len(keywords),
        len(definitions)
    )

    challenges = [
        "Close your notes and explain one topic from memory.",
        "Write three things you remember without looking.",
        "Teach one topic to someone else.",
        "Explain the hardest concept using simple words.",
        "Answer one practice question without checking your notes."
    ]

    challenge = random.choice(challenges)

    return jsonify({
        "wordCount": len(words),
        "sentenceCount": len(sentences),
        "topicCount": len(keywords),
        "keywords": keywords,
        "summary": summary,
        "definitions": definitions,
        "questions": questions,
        "studyScore": score,
        "challenge": challenge
    })


@app.route("/api/nasa")
def nasa():

    try:

        response = requests.get(
            "https://api.nasa.gov/planetary/apod",
            params={
                "api_key": NASA_KEY
            },
            timeout=10
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
            "image": data.get(
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
            )
        })

    except requests.RequestException:

        return jsonify({
            "error": "NASA information is unavailable right now."
        }), 503


@app.errorhandler(404)
def page_not_found(error):

    if request.path.startswith("/api/"):
        return jsonify({
            "error": "API page not found."
        }), 404

    return render_template("index.html")


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
        debug=True
    )



