# 📊 AI Data Analysis Chatbot (Google Sheet Live)

An interactive AI-powered analytics chatbot built using **Streamlit**, **Pandas**, and **Groq Llama 3.3**, which analyzes live data from a public Google Sheet.

This bot can answer questions like:
- "Yesterday revenue"
- "Top 5 cities by revenue"
- "Daily trend for last 7 days"
- "Total revenue last month"
- "Revenue by city"
- And any custom query in natural language

---

## 🚀 Features

### ✅ Live Google Sheet Data
Automatically fetches and refreshes dataset every 5 minutes.

### ✅ AI-Powered Insights
Uses **Groq Llama 3.3** for:
- Natural language query detection  
- Business insights  
- Trend explanations  

### ✅ Smart Date Handling
Bot understands:
- Yesterday  
- Last 7 days  
- Last month  
- Future date restrictions  
- Custom date ranges  

### ✅ Clean, Simple Streamlit UI
Includes quick insight buttons and dataset preview.

---

## 📂 Project Structure


---

## 🔧 Installation (Local)

Install dependencies:

```bash
pip install -r requirements.txt
streamlit run data-analysis-chatbot.py
