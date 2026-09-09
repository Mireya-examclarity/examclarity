import streamlit as st
import requests
import re
import random

# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------

st.set_page_config(
    page_title="ExamClarity",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 ExamClarity")
st.caption("Frictionless Study • Built for NASA Stardance")

# ---------------------------------------------------------
# NASA PICTURE OF THE DAY
# ---------------------------------------------------------

st.subheader("🌌 NASA — Picture of the Day")

try:
    data = requests.get(
        "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY",
        timeout=10
    ).json()

    if data.get("media_type") == "image":
        st.image(data["url"], caption=data["title"])
        st.info(data["explanation"][:400] + "...")
    else:
        st.info("Today's NASA post is not an image.")

except Exception:
    st.warning("NASA image unavailable — check your internet connection.")

st.divider()

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.header("⚙️ Study Settings")

difficulty = st.sidebar.select_slider(
    "Quiz Difficulty",
    options=["Easy", "Medium", "Hard"],
    value="Medium"
)

num_questions = st.sidebar.slider(
    "Number of Questions",
    min_value=3,
    max_value=10,
    value=5
)

st.sidebar.info(
    "ExamClarity analyzes your notes and focuses practice "
    "on the areas you may struggle with."
)

# ---------------------------------------------------------
# NOTES INPUT
# ---------------------------------------------------------

st.subheader("📚 Your Study Material")

notes = st.text_area(
    "Paste your long, boring notes:",
    height=250,
    placeholder="Paste your chapter, lecture notes, textbook section, etc..."
)

# ---------------------------------------------------------
# SIMPLE TEXT ANALYSIS
# ---------------------------------------------------------

def analyze_notes(text):
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    word_count = len(words)

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Find repeated important words
    stop_words = {
        "the", "and", "is", "of", "to", "in", "a", "for",
        "on", "that", "with", "as", "are", "was", "this",
        "it", "by", "an", "be", "or", "from", "at", "which"
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

    return {
        "word_count": word_count,
        "sentence_count": len(sentences),
        "important_words": important_words
    }


# ---------------------------------------------------------
# SUMMARY GENERATOR
# ---------------------------------------------------------

def generate_summary(text):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    sentences = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 20
    ]

    if not sentences:
        return ["Not enough text to create a summary."]

    # Pick the first few meaningful sentences
    summary = sentences[:5]

    return summary


# ---------------------------------------------------------
# QUESTION GENERATOR
# ---------------------------------------------------------

def generate_questions(text, difficulty, count):
    analysis = analyze_notes(text)
    topics = analysis["important_words"]

    if not topics:
        topics = ["the main concept"]

    questions = []

    question_templates = {
        "Easy": [
            "What is {topic}?",
            "Define {topic}.",
            "What is the basic idea behind {topic}?"
        ],

        "Medium": [
            "Explain how {topic} works.",
            "Why is {topic} important?",
            "Give an example related to {topic}.",
            "How does {topic} affect the main topic?"
        ],

        "Hard": [
            "Analyze the importance of {topic}.",
            "What would happen if {topic} changed?",
            "Compare {topic} with another major concept.",
            "Justify why {topic} is important."
        ]
    }

    templates = question_templates[difficulty]

    for i in range(count):
        topic = topics[i % len(topics)]
        template = random.choice(templates)

        questions.append({
            "question": template.format(topic=topic),
            "topic": topic,
            "difficulty": difficulty
        })

    return questions


# ---------------------------------------------------------
# FLASHCARD GENERATOR
# ---------------------------------------------------------

def generate_flashcards(text):
    analysis = analyze_notes(text)

    flashcards = []

    for topic in analysis["important_words"][:6]:
        flashcards.append({
            "front": f"What should you remember about {topic}?",
            "back": f"{topic.capitalize()} is an important concept found in your notes. Review the surrounding section for its definition, role, and examples."
        })

    return flashcards


# ---------------------------------------------------------
# STUDY GUIDE
# ---------------------------------------------------------

def create_study_guide(text):
    analysis = analyze_notes(text)
    summary = generate_summary(text)

    return analysis, summary


# ---------------------------------------------------------
# MAIN BUTTON
# ---------------------------------------------------------

if st.button("✨ Analyze My Notes", type="primary"):

    if not notes.strip():
        st.warning("Paste some notes first bro! 😭")

    else:

        with st.spinner("🧠 ExamClarity is analyzing your notes..."):

            analysis, summary = create_study_guide(notes)
            questions = generate_questions(
                notes,
                difficulty,
                num_questions
            )
            flashcards = generate_flashcards(notes)

        st.balloons()

        # -------------------------------------------------
        # DASHBOARD
        # -------------------------------------------------

        st.header("📊 Your Study Dashboard")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Words Analyzed",
                analysis["word_count"]
            )

        with col2:
            st.metric(
                "Important Concepts",
                len(analysis["important_words"])
            )

        with col3:
            st.metric(
                "Quiz Questions",
                len(questions)
            )

        # -------------------------------------------------
        # SUMMARY
        # -------------------------------------------------

        st.divider()

        st.header("🧠 Clean Study Guide")

        st.subheader("📌 Main Ideas")

        for point in summary:
            st.write("• " + point)

        # -------------------------------------------------
        # IMPORTANT CONCEPTS
        # -------------------------------------------------

        st.subheader("🔥 Important Concepts")

        for topic in analysis["important_words"]:
            st.write(f"🎯 **{topic.capitalize()}**")

        # -------------------------------------------------
        # QUIZ
        # -------------------------------------------------

        st.divider()

        st.header("🎯 Adaptive Quiz")

        st.write(
            f"Difficulty: **{difficulty}**"
        )

        score = 0

        for i, q in enumerate(questions):

            st.subheader(
                f"Question {i + 1}"
            )

            st.write(q["question"])

            answer = st.text_input(
                "Your answer:",
                key=f"answer_{i}"
            )

            if answer:

                if len(answer.split()) >= 5:

                    score += 1

                    st.success(
                        "✅ Good attempt! Your answer has enough detail."
                    )

                else:

                    st.warning(
                        "🟡 Try explaining your answer in more detail."
                    )

        # -------------------------------------------------
        # FLASHCARDS
        # -------------------------------------------------

        st.divider()

        st.header("🃏 Smart Flashcards")

        for i, card in enumerate(flashcards):

            with st.expander(
                f"🧠 Flashcard {i + 1}: {card['front']}"
            ):

                st.write(
                    f"**Answer:** {card['back']}"
                )

        # -------------------------------------------------
        # MASTERY
        # -------------------------------------------------

        st.divider()

        st.header("📈 Estimated Mastery")

        if questions:

            mastery = int(
                (score / len(questions)) * 100
            )

            st.progress(
                mastery / 100
            )

            if mastery >= 80:
                st.success(
                    f"🔥 {mastery}% — Excellent! You appear strong in these concepts."
                )

            elif mastery >= 50:
                st.warning(
                    f"🟡 {mastery}% — You're getting there. More practice recommended."
                )

            else:
                st.error(
                    f"🔴 {mastery}% — These topics need more practice."
                )

        # -------------------------------------------------
        # RECOMMENDATION
        # -------------------------------------------------

        st.divider()

        st.header("🎯 ExamClarity Recommendation")

        if analysis["important_words"]:

            weakest_topic = analysis["important_words"][-1]

            st.info(
                f"Based on your notes, spend extra time reviewing "
                f"**{weakest_topic}**."
            )

        st.caption(
            "ExamClarity uses your study material to prioritize "
            "what you should review next."
        )

else:

    st.info(
        "👆 Paste your notes and click **Analyze My Notes** "
        "to build your personalized study session."
    )

import streamlit as st
import requests
import re
import random
import time

#---------------------------------------------------------
#PAGE SETUP + CUSTOM CSS-THIS IS the