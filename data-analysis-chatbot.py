# data-analysis-bot.py
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_experimental.agents import create_pandas_dataframe_agent

from analysis_engine import interpret_and_run
from analytics_functions import ensure_date_column

# ------------------------------
# Load ENV
# ------------------------------
st.set_page_config(page_title="AI Data Insights Bot", page_icon="📊", layout="wide")

st.markdown("""
<style>
.big-title {
    font-size: 38px;
    font-weight: 700;
    background: -webkit-linear-gradient(90deg, #4fa3ff, #9b6bff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.sub-text {
    color: #b3b3b3;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. LOAD ENV + GROQ MODEL (Correct Params)
# ----------------------------------------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    api_key=groq_api_key,
    model="llama-3.3-70b-versatile",
    temperature=0
)

# ----------------------------------------------------
# 3. LOAD GOOGLE SHEET DATA
# ----------------------------------------------------
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQtCYlNqNBIxDnHHbbNRG7WUH6SqbHOscVf--YtwkKEHj3qleqwds30jWfO3kvheQf4pQGpMQ25mqqx/"
    "pub?gid=1995147516&single=true&output=csv"
)

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(SHEET_URL)
    return df

df = load_data()

# ----------------------------------------------------
# 4. DATE FIX — CRITICAL FOR YESTERDAY / LAST 7 DAYS
# ----------------------------------------------------
df["collection_date"] = pd.to_datetime(df["collection_date"], errors="coerce")
max_date = df["collection_date"].max()

if pd.isna(max_date):
    st.error("⚠️ No valid dates found in dataset. Check 'collection_date' column.")
    st.stop()

st.session_state["LATEST_DATE"] = max_date
st.info(f"📅 Latest data available: **{max_date.date()}**")

# ----------------------------------------------------
# 5. CREATE AGENT WITH SMART CUSTOM SYSTEM PROMPT
# ----------------------------------------------------
SYSTEM_INSTRUCTIONS = f"""
You are a Data Analysis AI working over a Pandas DataFrame.

IMPORTANT RULES:
1. The latest date in the dataset is {max_date.date()} — treat this as “today”.
2. If user asks:
   - "yesterday" → use (today - 1 day)
   - "last 7 days" → between (today - 7) to today
   - "last month" → month(today - 30 days)
3. If user asks a date that is newer than the latest dataset → respond:
   "Data is not updated till that date."
4. ALWAYS return a clean human-readable answer (no Python, no code).
"""

agent = create_pandas_dataframe_agent(
    llm,
    df,
    verbose=False,
    handle_parsing_errors=True,
    allow_dangerous_code=True,
    system_message=SYSTEM_INSTRUCTIONS
)

# ----------------------------------------------------
# 6. HEADER
# ----------------------------------------------------
st.markdown("<div class='big-title'>📊 AI Data Analysis Bot</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-text'>Live Google Sheet → Instant Insights. Powered by Groq Llama 3.3</div>", unsafe_allow_html=True)
st.write("---")

# ----------------------------------------------------
# 7. QUICK QUERY BUTTONS
# ----------------------------------------------------
st.write("#### 🔍 Quick Insights")

suggestions = [
    "Top 5 cities by revenue",
    "Yesterday revenue",
    "Daily trend for last 7 days",
    "Average price by city",
    "Total revenue last month",
    "Top 5 sources last week"
]

cols = st.columns(3)
for i, text in enumerate(suggestions):
    if cols[i % 3].button(text):
        st.session_state["prefill"] = text

# ----------------------------------------------------
# 8. DATA PREVIEW
# ----------------------------------------------------
with st.expander("📁 Preview your live data", expanded=False):
    st.dataframe(df.head(100), width="stretch")

st.write("---")

# ----------------------------------------------------
# 9. INPUT BOX
# ----------------------------------------------------
query = st.text_input(
    "Ask anything about your dataset 👇",
    value=st.session_state.get("prefill", ""),
    placeholder="Example: yesterday revenue, top 3 cities last week, revenue on 2025-12-08..."
)

# ----------------------------------------------------
# 10. RUN QUERY
# ----------------------------------------------------
if query:
    with st.spinner("🤖 Analyzing your dataset..."):
        try:
            answer = agent.run(query)
            st.success(answer)
        except Exception as e:
            st.error(f"⚠️ Error: {e}")

