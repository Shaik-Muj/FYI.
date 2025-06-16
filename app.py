import streamlit as st
from news import get_news_chat_summary
from video import extract_video_info
from fake_news_detection import check_news

# Must be the first Streamlit command
st.set_page_config(
    page_title="FYI.",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS for premium look and centered title
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #0f172a 0%, #1a1c48 100%);
    }
    .block-container {
        padding-top: 2.5rem !important;
        max-width: 900px !important;
        margin: 0 auto !important;
    }
    .fyi-title {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: -2px;
        color: #fff;
        margin-bottom: 0.2rem;
        line-height: 1.1;
    }
    .fyi-subtitle {
        text-align: center;
        font-size: 1.3rem;
        color: #94A3B8;
        margin-bottom: 2.5rem;
        font-weight: 400;
        letter-spacing: 1px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: transparent;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #FFF;
        font-size: 1.1rem;
        font-weight: 500;
        padding: 0.7rem 0.5rem;
        position: relative;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #6366F1;
        font-weight: 700;
        /* Remove border-bottom to avoid double line */
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"]::after {
        content: '';
        display: block;
        position: absolute;
        left: 0;
        right: 0;
        bottom: -2px;
        height: 3px;
        background: linear-gradient(90deg, #6366F1 0%, #EC4899 100%);
        border-radius: 2px;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: rgba(30, 41, 59, 0.5) !important;
        border: none !important;
        border-radius: 8px !important;
        color: #FFF !important;
        font-size: 15px !important;
        padding: 14px !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #6366F1 0%, #4F46E5 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 32px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        margin-top: 0.7rem !important;
        margin-bottom: 0.7rem !important;
        transition: box-shadow 0.2s;
        box-shadow: 0 2px 8px 0 rgba(99,102,241,0.10);
    }
    .stButton > button:hover {
        box-shadow: 0 4px 16px 0 rgba(99,102,241,0.18);
    }
    .tool-description {
        color: #94A3B8;
        font-size: 1rem;
        margin-bottom: 1.5rem;
        line-height: 1.5;
    }
    #MainMenu, footer, [data-testid="stToolbar"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Centered FYI title and subtitle
st.markdown('<div style="text-align:center;font-size:3.5rem;font-weight:800;letter-spacing:-2px;color:#fff;line-height:1.1;margin-bottom:0.2rem;">FYI.</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;font-size:1.3rem;color:#94A3B8;margin-bottom:2.5rem;font-weight:400;letter-spacing:1px;">For Your Information</div>', unsafe_allow_html=True)

# Tabs for navigation
tab1, tab2, tab3 = st.tabs([
    "📰 News Summarizer",
    "🔍 News Verifier",
    "🎥 Video Summarizer"
])

# News Summarizer Tab
with tab1:
    st.markdown("<h1>News Summarizer</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="tool-description">Get instant, AI-powered summaries of news topics. '
        'Enter any topic of interest, and we\'ll analyze recent news articles to provide you with a comprehensive overview.</p>',
        unsafe_allow_html=True
    )
    
    topic = st.text_area(
        "Enter a news topic",
        key="summarizer_input",
        height=150,
        placeholder="E.g., 'Latest developments in AI' or 'Current global events'"
    )
    
    if st.button("Generate Summary", key="summarizer_btn"):
        if topic:
            with st.spinner("Analyzing..."):
                summary = get_news_chat_summary(topic)
                st.markdown(summary)
        else:
            st.warning("Please enter a topic to summarize")

# News Verifier Tab
with tab2:
    st.markdown("<h1>News Verifier</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="tool-description">Verify the credibility of news content instantly. '
        'Paste any news text, and our AI will analyze its authenticity.</p>',
        unsafe_allow_html=True
    )
    
    text = st.text_area(
        "Enter news text to verify",
        key="verifier_input",
        height=150,
        placeholder="Paste the news content you want to verify..."
    )
    
    if st.button("Verify News", key="verify_btn"):
        if text:
            with st.spinner("Verifying..."):
                result = check_news(text)
                st.write(result)
        else:
            st.warning("Please enter text to verify")

# Video Summarizer Tab
with tab3:
    st.markdown("<h1>Video Summarizer</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="tool-description">Extract key insights from YouTube videos efficiently. '
        'Simply paste a YouTube URL, and we\'ll provide you with a concise summary.</p>',
        unsafe_allow_html=True
    )
    
    url = st.text_input(
        "Enter YouTube URL",
        key="video_input",
        placeholder="Paste YouTube video URL here..."
    )
    
    if st.button("Summarize Video", key="video_btn"):
        if url:
            with st.spinner("Processing..."):
                result = extract_video_info(url)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.markdown(f"### {result['title']}")
                    st.markdown(result['summary'])
                    st.markdown(f"[Watch Original Video]({result['url']})")
        else:
            st.warning("Please enter a YouTube URL")

