from flask import Flask, render_template, request
import requests
import re
import random
import os
import logging

app = Flask(__name__)

# Students problem: long notes, no time, messy YouTube lectures
# Fix: Turn friction into clarity

logging.basicConfig(level=logging.INFO)

def analyze_notes(text):
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

    stop_words = {"the","and","is","of","to","in","a","for","on","that","with","as","are","was","this","it","by","an","be","or","from","at","which","but","have","has","had","their","they","these","those","can","will","into","than","then","also","its","about"}
    
    freq = {}
    for w in words:
        if w not in stop_words and len(w) > 4:
            freq[w] = freq.get(w, 0) + 1

    important = sorted(freq, key=freq.get, reverse=True)[:10]

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "important_words": important,
        "score": min(100, len(words)//5 + len(sentences)*2)}
    

def generate_summary(text):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if len(s.strip()) > 20]
    if len(sentences) < 2:
        return ["Paste a bit more to get a clean summary 🥺"]

    keywords = analyze_notes(text)["important_words"]
    
    # FIX 3:  Summary
    scored = []
    for idx, s in enumerate(sentences):
        score = sum(2 for k in keywords if k in s.lower())

        # bonus for sentences at start 

        if idx == 0: score += 3
        if idx == 1: score += 1
        # readable length bonus


        if 12 <= len(s.split()) <= 30: score += 2
        # avoid too short

        if len(s.split()) < 8: score -= 5
        scored.append((score, idx, s))
    
    # sort by score, then by original order for natural flow

    scored.sort(key=lambda x: (-x[0], x[1]))
    summary = []
    for _, _, s in scored:
        if s not in summary:
            summary.append(s)
        if len(summary) == 3: break
    
    # return in original order so it reads well

    summary.sort(key=lambda s: sentences.index(s))
    return summary

def generate_questions(text, difficulty, count):
    topics = analyze_notes(text)["important_words"] or ["the main concept"]
    templates = {
        "Easy": ["What is {topic}? 🌱", "Define {topic} in one line."],
        "Medium": ["Explain how {topic} works. 🌤️", "Why is {topic} important?", "Give an example of {topic}."],
        "Hard": ["Analyze the importance of {topic}. 🔥", "Compare {topic} with another concept you studied."]
    }
    t_list = templates.get(difficulty, templates["Medium"])
    return [{"question": random.choice(t_list).format(topic=topics[i % len(topics)]), "topic": topics[i % len(topics)]} for i in range(count)]

def find_definitions(text):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    patterns = [" is ", " are ", " refers to ", " means ", "defined as", "known as"]
    defs = []
    for s in sentences:
        for p in patterns:
            if p in s.lower() and len(s) > 30 and s not in defs:
                defs.append(s.strip()); break
    return defs[:6]

def get_apod():
    # FIX 2: No more bare except: pass

    try:
        r = requests.get(
            "https://api.nasa.gov/planetary/apod",
            params={"api_key": os.environ.get("NASA_API_KEY","DEMO_KEY")},
            timeout=10)
        
        r.raise_for_status()
        data = r.json()
        if data.get("media_type") == "image":
            return data
        else:
            logging.warning(f"APOD not image today: {data.get('media_type')}")
            return {"url": data.get("url",""), "title": data.get("title","Space 🚀"), "explanation": data.get("explanation","")}
            
    except requests.exceptions.Timeout:
        logging.error("NASA APOD timeout")
    except requests.exceptions.ConnectionError:
        logging.error("NASA APOD connection failed")
    except requests.exceptions.HTTPError as e:
        logging.error(f"NASA APOD HTTP error: {e}")
    except Exception as e:
        logging.error(f"NASA APOD unexpected error: {e}")

    # fallback always works

    return {"url":"https://apod.nasa.gov/apod/image/2308/M31_HubbleSpitzer_960.jpg","title":"Space is motivation 🚀","explanation":"NASA image for study motivation - fallback image"}

@app.route("/", methods=["GET", "POST"])
def home():
    apod = get_apod()
    result = None
    notes_text = ""
    difficulty = "Medium"
    num = 5

    challenges = [
        "Explain this chapter to a 10-year-old in 3 lines ✏️",
        "Write 5 keywords from memory without seeing notes 🧠",
        "Make 1 hard question and answer it 🎯",
        "Close notes, write what you remember in 2 mins ⏰"]
    

    if request.method == "POST":
        notes_text = request.form.get("notes","")
        difficulty = request.form.get("difficulty","Medium") or "Medium"
        
        # FIX 4: Safe input validation - no Value error crash

        raw_num = request.form.get("num","5")
        try:
            num = int(raw_num)
        except (ValueError, TypeError):
            logging.warning(f"Invalid num input: {raw_num}, using default 5")
            num = 5
        
        num = max(1, min(num, 20))  # limit 1-20

        if notes_text.strip():
            result ={ 
                "analysis": analyze_notes(notes_text),
                "summary": generate_summary(notes_text),
                "questions": generate_questions(notes_text, difficulty, num),
                "definitions": find_definitions(notes_text),
                "challenge": random.choice(challenges)}
            


    return render_template("index.html", apod=apod, result=result, notes_text=notes_text, difficulty=difficulty, num=num)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    # FIX 1: debug=False for production, only True locally

    is_prod = os.environ.get("RENDER") or os.environ.get("PORT")
    app.run(host="0.0.0.0", port=port, debug=not is_prod)


