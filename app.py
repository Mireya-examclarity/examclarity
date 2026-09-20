      from flask import Flask, render_template, request
import requests
import re
import random
import os

app = Flask(__name__)


# -----------------------------
# NOTE ANALYSIS
# -----------------------------

def analyze_notes(text):
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    word_count = len(words)

    sentences = [
        s.strip()
        for s in re.split(r"[.!?]+", text)
        if s.strip()
    ]

    stop_words = {
        "the", "and", "is", "of", "to", "in", "a", "for", "on",
        "that", "with", "as", "are", "was", "this", "it", "by",
        "an", "be", "or", "from", "at", "which", "but", "have",
        "has", "had", "their", "they", "these", "those", "can",
        "will", "into", "than", "then", "also", "its", "about"
    }

    frequency = {}

    for word in words:
        if word not in stop_words and len(word) > 4:
            frequency[word] = frequency.get(word, 0) + 1

    important_words = sorted(
        frequency,
        key=frequency.get,
        reverse=True
    )[:10]

    return {
        "word_count": word_count,
        "sentence_count": len(sentences),
        "important_words": important_words
    }


# -----------------------------
# SUMMARY
# -----------------------------

def generate_summary(text):
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", text.strip())
        if len(s.strip()) > 20
    ]

    if not sentences:
        return ["Not enough text to create a summary."]

    analysis = analyze_notes(text)
    keywords = analysis["important_words"]

    scored = []

    for sentence in sentences:
        score = sum(
            1 for keyword in keywords
            if keyword in sentence.lower()
        )

        if 10 <= len(sentence.split()) <= 35:
            score += 1

        scored.append((score, sentence))

    scored.sort(key=lambda x: x[0], reverse=True)

    summary = []

    for score, sentence in scored:
        if sentence not in summary:
            summary.append(sentence)

        if len(summary) == 3:
            break

    return summary


# -----------------------------
# QUESTIONS
# -----------------------------

def generate_questions(text, difficulty, count):
    analysis = analyze_notes(text)

    topics = analysis["important_words"] or ["the main concept"]

    question_templates = {
        "Easy": [
            "What is {topic}?",
            "Define {topic}."
        ],

        "Medium": [
            "Explain how {topic} works.",
            "Why is {topic} important?",
            "Give an example involving {topic}."
        ],

        "Hard": [
            "Analyze the importance of {topic}.",
            "Compare {topic} with another major concept."
        ]
    }

    templates = question_templates.get(
        difficulty,
        question_templates["Medium"]
    )

    questions = []

    for i in range(count):
        topic = topics[i % len(topics)]
        template = random.choice(templates)

        questions.append({
            "question": template.format(topic=topic),
            "topic": topic
        })

    return questions


# -----------------------------
# DEFINITIONS
# -----------------------------

def find_definitions(text):
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    definitions = []

    patterns = [
        " is ",
        " are ",
        " refers to ",
        " means ",
        "defined as",
        "known as"
    ]

    for sentence in sentences:

        for pattern in patterns:

            if (
                pattern in sentence.lower()
                and len(sentence) > 30
                and sentence not in definitions
            ):
                definitions.append(sentence.strip())
                break

    return definitions[:10]


# -----------------------------
# NASA APOD
# -----------------------------

def get_apod():

    try:
        response = requests.get(
            "https://api.nasa.gov/planetary/apod",
            params={
                "api_key": os.environ.get(
                    "NASA_API_KEY",
                    "DEMO_KEY"
                )
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data.get("media_type") == "image":
            return data

    except requests.RequestException:
        pass

    return None


# -----------------------------
# HOME PAGE
# -----------------------------

@app.route("/", methods=["GET", "POST"])
def home():

    apod = get_apod()

    result = None
    notes_text = ""
    difficulty = "Medium"
    num = 5

    if request.method == "POST":

        notes_text = request.form.get(
            "notes",
            ""
        )

        difficulty = request.form.get(
            "difficulty",
            "Medium"
        )

        try:
            num = int(
                request.form.get("num", 5)
            )
        except ValueError:
            num = 5

        # Prevent unreasonable values
        num = max(1, min(num, 20))

        if notes_text.strip():

            analysis = analyze_notes(
                notes_text
            )

            result = {
                "analysis": analysis,

                "summary": generate_summary(
                    notes_text
                ),

                "questions": generate_questions(
                    notes_text,
                    difficulty,
                    num
                ),

                "definitions": find_definitions(
                    notes_text
                )
            }

    return render_template(
        "index.html",
        apod=apod,
        result=result,
        notes_text=notes_text,
        difficulty=difficulty,
        num=num
    )


if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
