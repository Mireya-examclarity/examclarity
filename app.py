from flask import Flask, render_template, request
import re
import random
import requests
import os

app = Flask(__name__)


# -----------------------------
# Analyze Notes
# -----------------------------

def analyze_notes(text):

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    sentences = [
        s.strip()
        for s in re.split(r"[.!?]+", text)
        if s.strip()
    ]

    stop_words = {
        "the", "and", "is", "of", "to", "in",
        "a", "for", "on", "that", "with", "as",
        "are", "was", "this", "it", "by", "an",
        "be", "or", "from", "at", "which", "but",
        "have", "has", "had", "their", "they",
        "these", "those", "can", "will", "into",
        "than", "then", "also", "its", "about"
    }

    frequency = {}

    for word in words:

        if word not in stop_words and len(word) > 4:

            frequency[word] = frequency.get(word, 0) + 1

    important_words = sorted(
        frequency,
        key=frequency.get,
        reverse=True
    )[:8]

    # Simple study score
    score = 0

    if len(words) >= 50:
        score += 25

    if len(words) >= 150:
        score += 25

    if len(sentences) >= 5:
        score += 25

    if len(important_words) >= 5:
        score += 25

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "important_words": important_words,
        "score": score
    }


# -----------------------------
# Summary
# -----------------------------

def generate_summary(text):

    sentences = [
        s.strip()
        for s in re.split(
            r"(?<=[.!?])\s+",
            text.strip()
        )
        if len(s.strip()) > 20
    ]

    if not sentences:
        return ["Not enough text for a summary."]

    analysis = analyze_notes(text)

    keywords = analysis["important_words"]

    scored = []

    for sentence in sentences:

        score = 0

        for keyword in keywords:

            if keyword in sentence.lower():
                score += 1

        if 10 <= len(sentence.split()) <= 35:
            score += 1

        scored.append(
            (score, sentence)
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        sentence
        for score, sentence in scored[:3]
    ]


# -----------------------------
# Questions
# -----------------------------

def generate_questions(text, difficulty, count):

    analysis = analyze_notes(text)

    topics = analysis["important_words"]

    if not topics:
        topics = ["the main topic"]

    question_templates = {

        "Easy": [
            "What is {topic}?",
            "Define {topic}.",
            "What does {topic} mean?"
        ],

        "Medium": [
            "Why is {topic} important?",
            "Explain how {topic} works.",
            "Give an example of {topic}.",
            "How would you explain {topic} to a friend?"
        ],

        "Hard": [
            "Why is {topic} important in real life?",
            "How could {topic} be applied to another situation?",
            "Compare {topic} with another concept.",
            "What could happen if {topic} changed?"
        ]
    }

    templates = question_templates.get(
        difficulty,
        question_templates["Medium"]
    )

    questions = []

    for i in range(count):

        topic = random.choice(topics)

        question = random.choice(
            templates
        ).format(topic=topic)

        questions.append({
            "question": question,
            "topic": topic
        })

    return questions


# -----------------------------
# Definitions
# -----------------------------

def find_definitions(text):

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    patterns = [
        " is ",
        " are ",
        " means ",
        " refers to ",
        "defined as",
        "known as"
    ]

    definitions = []

    for sentence in sentences:

        if len(sentence) < 30:
            continue

        for pattern in patterns:

            if pattern in sentence.lower():

                if sentence not in definitions:
                    definitions.append(
                        sentence.strip()
                    )

                break

        if len(definitions) == 5:
            break

    return definitions


# -----------------------------
# Study Challenge
# -----------------------------

def get_challenge():

    challenges = [
        "Explain one topic without looking at your notes.",
        "Write down three things you remember.",
        "Teach one concept to an imaginary class.",
        "Try answering one question in 30 seconds.",
        "Explain the hardest topic using simple words."
    ]

    return random.choice(challenges)


# -----------------------------
# NASA
# -----------------------------

def get_nasa():

    try:

        api_key = os.environ.get(
            "NASA_API_KEY",
            "DEMO_KEY"
        )

        response = requests.get(
            "https://api.nasa.gov/planetary/apod",
            params={
                "api_key": api_key
            },
            timeout=8
        )

        response.raise_for_status()

        data = response.json()

        if data.get("media_type") == "image":
            return data

    except requests.RequestException:
        return None

    return None


# -----------------------------
# Home Page
# -----------------------------

@app.route("/", methods=["GET", "POST"])
def home():

    result = None
    notes = ""
    difficulty = "Medium"
    number = 5

    nasa = get_nasa()

    if request.method == "POST":

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        difficulty = request.form.get(
            "difficulty",
            "Medium"
        )

        try:

            number = int(
                request.form.get(
                    "number",
                    5
                )
            )

        except ValueError:

            number = 5

        number = max(
            1,
            min(number, 20)
        )

        if notes:

            analysis = analyze_notes(
                notes
            )

            result = {

                "analysis": analysis,

                "summary": generate_summary(
                    notes
                ),

                "questions": generate_questions(
                    notes,
                    difficulty,
                    number
                ),

                "definitions": find_definitions(
                    notes
                ),

                "challenge": get_challenge()
            }

    return render_template(
        "index.html",
        result=result,
        notes=notes,
        difficulty=difficulty,
        number=number,
        nasa=nasa
    )


# -----------------------------
# Run App
# -----------------------------

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
    