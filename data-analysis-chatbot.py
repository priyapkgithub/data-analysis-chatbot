# data-analysis-bot.py
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_groq import ChatGroq

# ----------------------------------------------------
# 1. PAGE UI CONFIG
# ----------------------------------------------------
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
    model="llama-3.3-70b-versatile",   # FIXED FOR YOUR VERSION
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
# 4. DATE FIX — REQUIRED FOR TIME QUERIES
# ----------------------------------------------------
df["collection_date"] = pd.to_datetime(df.get("collection_date"), errors="coerce")
max_date = df["collection_date"].max()

if pd.isna(max_date):
    st.error("⚠️ No valid 'collection_date' found. Check dataset.")
    st.stop()

st.session_state["LATEST_DATE"] = max_date
st.info(f"📅 Latest available date in data: **{max_date.date()}**")

# ----------------------------------------------------
# 5. SYSTEM PROMPT FOR THE AGENT
# ----------------------------------------------------
SYSTEM_INSTRUCTIONS = f"""
You are a Data Analyst AI working on a Pandas DataFrame.

Rules:
1. Treat latest dataset date {max_date.date()} as TODAY.
2. "Yesterday" = today - 1 day.
3. "Last 7 days" = today - 7 → today.
4. If the user asks for a date newer than {max_date.date()}, respond:
   "Data is not updated till that date."
5. Always provide a clean business explanation, NOT Python code.
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
# 7. QUICK INSIGHTS BUTTONS
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
