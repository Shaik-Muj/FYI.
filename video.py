import subprocess
import os
import glob
import requests
import time
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import string
import re # Added import for is_video_url

# Download required NLTK data
nltk.download("punkt")
nltk.download("stopwords")


# ---------------------------
# 🔑 CONFIGURATION
# ---------------------------
ASSEMBLYAI_API_KEY = "2da7b51634e240d6a16d8a92212e2eb0" # Consider moving to environment variables

# ---------------------------
# 🔗 URL Check
# ---------------------------
def is_video_url(url):
    """Check if the URL is a valid YouTube video URL."""
    return bool(re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', url))

# ---------------------------
# 🔽 Download YouTube Audio
# ---------------------------
def download_audio(url):
    try:
        subprocess.run([
            "yt-dlp", "--downloader-args", "ffmpeg_i:-t 60",
            "-x", "--audio-format", "mp3", url
        ], check=True)
        mp3_files = sorted(glob.glob("*.mp3"), key=os.path.getmtime, reverse=True)
        return mp3_files[0] if mp3_files else None
    except Exception as e:
        print("❌ Failed to download audio:", e)
        return None

# ---------------------------
# 🧠 Transcribe using AssemblyAI
# ---------------------------
def transcribe_with_assemblyai(audio_path):
    # Step 1: Upload audio file to AssemblyAI
    upload_url = "https://api.assemblyai.com/v2/upload"
    headers = {"authorization": ASSEMBLYAI_API_KEY}
    with open(audio_path, "rb") as f:
        upload_response = requests.post(upload_url, headers=headers, files={"file": f})
    if upload_response.status_code != 200:
        print("❌ Audio file upload failed:", upload_response.text)
        return ""

    audio_url = upload_response.json()["upload_url"]
    print("📄 Audio uploaded successfully!")

    # Step 2: Request transcription
    transcribe_url = "https://api.assemblyai.com/v2/transcript"
    transcription_payload = {"audio_url": audio_url}
    transcription_response = requests.post(transcribe_url, headers=headers, json=transcription_payload)
    if transcription_response.status_code != 200:
        print("❌ Failed to start transcription:", transcription_response.text)
        return ""

    transcript_id = transcription_response.json()["id"]
    print("📝 Transcription in progress...")

    # Step 3: Poll for transcription result
    while True:
        check_transcript_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        check_response = requests.get(check_transcript_url, headers=headers)
        transcript_data = check_response.json()
        if transcript_data["status"] == "completed":
            return transcript_data["text"]
        elif transcript_data["status"] == "failed":
            print("❌ Transcription failed:", transcript_data["error"])
            return ""
        time.sleep(5)

# ---------------------------
# ✍️ Summarize with NLTK
# ---------------------------
def summarize_with_nltk(text, max_sentences=5):
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(text.lower())
    words = [word for word in words if word not in stop_words and word not in string.punctuation]

    word_frequencies = {}
    for word in words:
        if word not in word_frequencies:
            word_frequencies[word] = 1
        else:
            word_frequencies[word] += 1

    sentence_scores = {}
    sentences = sent_tokenize(text)
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word in word_frequencies:
                if sentence not in sentence_scores:
                    sentence_scores[sentence] = word_frequencies[word]
                else:
                    sentence_scores[sentence] += word_frequencies[word]

    summarized_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
    summary = " ".join(summarized_sentences)
    return summary

# ---------------------------
# 🚀 Main pipeline
# ---------------------------
def extract_video_info(url):
    print("🔽 Downloading audio...")
    audio_file = download_audio(url)
    if not audio_file:
        # Clean up potentially partially downloaded/failed files
        try:
            if audio_file and os.path.exists(audio_file): os.remove(audio_file)
        except: pass
        return {"error": "Download failed."}

    print("🎧 Transcribing via AssemblyAI...")
    transcript = transcribe_with_assemblyai(audio_file)

    # Clean up audio file after upload/transcription attempt
    try:
        if audio_file and os.path.exists(audio_file): os.remove(audio_file)
    except Exception as e:
        print(f"Warning: Could not delete audio file {audio_file}: {e}")

    if not transcript or not transcript.strip():
        return {"error": "Transcription failed or returned empty."}

    print("🧠 Summarizing via NLTK...")
    summary = summarize_with_nltk(transcript, max_sentences=5)

    return {
        "title": "YouTube Video Summary",
        "summary": summary,
        "url": url
    }

