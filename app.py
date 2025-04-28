import streamlit as st
from dotenv import load_dotenv
import os
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

# Load environment variables
load_dotenv('env.env')
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompts
summary_prompt = """You are a YouTube video summarizer. Summarize the given transcript into key points within 250 words. Present them pointwise. Provide the summary of the text below: """
question_prompt = """Based on the following summary, generate 5-6 simple follow-up questions in a numbered list format that users might want to ask to explore the topic further:
"""

# Function to extract YouTube transcript
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

        transcript = ""
        for i in transcript_text:
            transcript += " " + i["text"]

        return transcript
    except Exception as e:
        raise e

# Function to generate content using Google Gemini
def generate_gemini_content(text, prompt):
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    response = model.generate_content(prompt + text)
    return response.text

# Initialize Session State
if "video_id" not in st.session_state:
    st.session_state.video_id = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "follow_up_questions" not in st.session_state:
    st.session_state.follow_up_questions = []
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None
if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None
if "transcript" not in st.session_state:
    st.session_state.transcript = ""

# Callback function for handling question selection
def select_question(idx):
    st.session_state.selected_question = st.session_state.follow_up_questions[idx]
    st.session_state.selected_answer = generate_gemini_content(
        st.session_state.transcript, st.session_state.selected_question
    )

# Streamlit App
st.title("YouTube Transcript to Notes with Q&A")

# URL Input Field
youtube_link = st.text_input("Enter YouTube Video Link:")

# Automatically display thumbnail if URL is entered
if youtube_link:
    try:
        st.session_state.video_id = youtube_link.split("=")[1]
    except IndexError:
        st.error("Invalid YouTube URL. Please enter a valid link.")

# Show thumbnail and "Get Notes & Questions" button if video ID is valid
if st.session_state.video_id:
    st.image(f"http://img.youtube.com/vi/{st.session_state.video_id}/0.jpg", use_container_width=True)
    if st.button("Get Notes & Questions"):
        try:
            # Extract transcript
            transcript_text = extract_transcript_details(youtube_link)
            st.session_state.transcript = transcript_text
            if transcript_text:
                # Generate Summary
                st.session_state.summary = generate_gemini_content(transcript_text, summary_prompt)

                # Generate Follow-Up Questions
                questions = generate_gemini_content(st.session_state.summary, question_prompt)
                st.session_state.follow_up_questions = re.findall(r"^\d+\.\s*(.+)$", questions, re.MULTILINE)

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Display Summary
if st.session_state.summary:
    st.markdown("## Summary:")
    st.write(st.session_state.summary)

# Display Follow-Up Questions
if st.session_state.follow_up_questions:
    st.markdown("## Follow-Up Questions:")

    # Define custom clickable box styling
    question_style = """
        <style>
            .question-box {
                display: block;
                width: 100%;
                max-width: 700px;
                margin: 10px auto;
                border: 1px solid #444;
                border-radius: 5px;
                background-color: #1f1f1f;
                color: #ffffff; /* Ensure text color is white */
                font-size: 16px;
                line-height: 1.5;
                cursor: pointer;
                padding: 15px;
                text-align: left;
                word-wrap: break-word;
                white-space: normal;
            }
            .question-box:hover {
                background-color: #333;
                border-color: #666;
            }
        </style>
    """
    st.markdown(question_style, unsafe_allow_html=True)

    # Generate clickable question boxes
    for idx, question in enumerate(st.session_state.follow_up_questions, start=1):
        question_text = f"Q{idx}: {question.strip()}"
        if st.button(question_text, key=f"question_{idx}"):
            st.session_state.selected_question = question
            st.session_state.selected_answer = generate_gemini_content(
                st.session_state.transcript, question
            )

# Display the Answer to the Selected Question
if st.session_state.selected_question:
    st.markdown(f"### {st.session_state.selected_question}")
    st.write(st.session_state.selected_answer)

# Ask Your Own Question Section
if st.session_state.transcript:
    st.markdown("## Ask Your Own Question:")
    user_question = st.text_input("Enter your question here:", key="user_question")
    if user_question:
        user_response = generate_gemini_content(st.session_state.transcript, user_question)
        st.markdown(f"### {user_question}")
        st.write(user_response)
