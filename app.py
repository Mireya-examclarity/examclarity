import streamlit as st
import requests

st.set_page_config(page_title="ExamClarity", page_icon="🚀")

st.title("🚀 ExamClarity - Frictionless Study")
st.caption("Made in Neyyattinkara | For NASA Stardance")

st.subheader("🌌 NASA - Picture of the Day")
try:
    data = requests.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", timeout=10).json()
    st.image(data['url'], caption=data['title'])
    st.info(data['explanation'][:300] + "...")
except:
    st.warning("NASA image will load when internet is on - showing demo moon image")
    st.image("https://apod.nasa.gov/apod/image/2408/MoonMars_Belur_960.jpg")

st.divider()

notes = st.text_area("Paste long boring notes:", height=150, placeholder="Paste chapter here...")

if st.button("Make it Frictionless ✨"):
    if notes:
        st.balloons()
        st.subheader("✅ Clean Summary:")
        st.write("1. Main idea: " + notes[:80])
        st.write("2. Important point to remember for exam")
        st.write("3. Simple example to understand better")
        st.subheader("📝 Quick Quiz:")
        st.write("Q1. What is the main topic?")
        st.write("Q2. Explain point 2 in your words?")
    else:
        st.warning("Paste notes first bro!")