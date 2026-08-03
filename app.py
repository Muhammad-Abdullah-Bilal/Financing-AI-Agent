import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict
import math
import io
import datetime
import os
import shutil
import google.generativeai as genai

# Set page config
st.set_page_config(
    page_title="AutoNest - AI Personal Finance Agent",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- COPY LOGO ASSET ----------
local_logo = "autonest_logo.jpg"
brain_logo_path = r"C:\Users\Multi Spot Laptops\.gemini\antigravity\brain\ebe762f7-5659-44dd-92c5-c716e32e1c28\autonest_logo_1785734898078.jpg"
if not os.path.exists(local_logo) and os.path.exists(brain_logo_path):
    try:
        shutil.copy(brain_logo_path, local_logo)
    except Exception:
        pass

# ---------- CUSTOM CSS THEME ----------
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Glassmorphic Metric Cards */
    .metric-container {
        display: flex;
        gap: 15px;
        margin-bottom: 20px;
    }
    .metric-card {
        flex: 1;
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.04);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px 0 rgba(0, 0, 0, 0.08);
        border-color: rgba(0, 0, 0, 0.12);
    }
    .metric-title {
        font-size: 13px;
        color: #71717a;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 32px;
        color: #09090b;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .metric-subtitle {
        font-size: 12px;
        color: #059669;
        font-weight: 600;
        margin-top: 4px;
    }
    .metric-subtitle.negative {
        color: #dc2626;
    }
    .metric-subtitle.neutral {
        color: #71717a;
    }
    
    /* Section Headers */
    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 15px;
        border-left: 4px solid #3b82f6;
        padding-left: 10px;
    }
    
    /* Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 11px;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-priority {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .badge-balanced {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    /* Custom Progress Bar for Goals */
    .goal-card {
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
    }
    .goal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .goal-title {
        font-weight: 600;
        font-size: 16px;
        color: #09090b;
    }
    .goal-target {
        font-size: 14px;
        color: #71717a;
    }
    .goal-progress-container {
        background: rgba(0, 0, 0, 0.06);
        border-radius: 8px;
        height: 10px;
        width: 100%;
        overflow: hidden;
        margin-bottom: 8px;
    }
    .goal-progress-bar {
        background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%);
        height: 100%;
        border-radius: 8px;
    }
    .goal-footer {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #71717a;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------- HELPER FUNCTIONS ----------
def round_down_10(x):
    return int(math.floor(x / 10.0)) * 10

# Cache standard date parsing to make CSV loading fast
@st.cache_data
def standardize_dataframe(df):
    rename_dict = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ["date", "timestamp", "time"]:
            rename_dict[col] = "Date"
        elif col_lower in ["amount", "value", "price"]:
            rename_dict[col] = "Amount"
        elif col_lower in ["category", "type"]:
            rename_dict[col] = "Category"
        elif col_lower in ["subcategory", "sub-category"]:
            rename_dict[col] = "Subcategory"
        elif col_lower in ["income/expense", "type_transaction", "direction"]:
            rename_dict[col] = "Income/Expense"
        elif col_lower in ["note", "description", "details"]:
            rename_dict[col] = "Note"
            
    df = df.rename(columns=rename_dict)
    
    if "Date" not in df.columns:
        df["Date"] = pd.Timestamp.now().strftime("%Y-%m-%d")
    if "Amount" not in df.columns:
        df["Amount"] = 0.0
    if "Category" not in df.columns:
        df["Category"] = "Other"
    if "Income/Expense" not in df.columns:
        df["Income/Expense"] = "expense"
    if "Subcategory" not in df.columns:
        df["Subcategory"] = ""
    if "Note" not in df.columns:
        df["Note"] = ""
        
    df["Income/Expense"] = df["Income/Expense"].fillna("expense").astype(str).str.lower()
    
    # Parse dates with mixed format to suppress warning and make it fast
    parsed_date = pd.to_datetime(df["Date"], errors="coerce", format="mixed")
    df["Date"] = parsed_date.dt.strftime("%Y-%m-%d").fillna(pd.Timestamp.now().strftime("%Y-%m-%d"))
    
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
    df["Category"] = df["Category"].fillna("Other").astype(str).str.strip().str.title()
    df["Subcategory"] = df["Subcategory"].fillna("").astype(str)
    df["Note"] = df["Note"].fillna("").astype(str)
    
    return df

def load_default_data():
    if "transactions" not in st.session_state:
        csv_file = "dummy_transactions.csv"
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                df = standardize_dataframe(df)
                st.session_state.transactions = df.to_dict(orient="records")
            except Exception:
                st.session_state.transactions = []
        else:
            st.session_state.transactions = []
            
    if "custom_buckets" not in st.session_state:
        st.session_state.custom_buckets = ["Emergency", "Travel", "Fun", "Health"]
        
    if "category_mappings" not in st.session_state:
        st.session_state.category_mappings = {
            "Food": {"bucket": "Emergency", "rate": 0.05},
            "Transportation": {"bucket": "Travel", "rate": 0.05},
            "Transport": {"bucket": "Travel", "rate": 0.05},
            "Subscription": {"bucket": "Fun", "rate": 0.05},
            "Festivals": {"bucket": "Fun", "rate": 0.05},
            "Entertainment": {"bucket": "Fun", "rate": 0.05},
            "Healthcare": {"bucket": "Health", "rate": 0.10},
            "Health": {"bucket": "Health", "rate": 0.10},
            "Family": {"bucket": "Emergency", "rate": 0.01},
            "Other": {"bucket": "Emergency", "rate": 0.01}
        }
        
    if "goals" not in st.session_state:
        st.session_state.goals = [
            {"id": 1, "name": "Emergency Cushion", "target": 2000.0, "saved": 150.0, "deadline": "2026-12-31", "bucket": "Emergency"},
            {"id": 2, "name": "Japan Trip", "target": 3000.0, "saved": 350.0, "deadline": "2027-06-30", "bucket": "Travel"}
        ]
        
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I am AutoNest, your AI Financing Agent. Upload your transaction CSV, manage your savings buckets, customize allocation rules, and ask me any financial queries!"}
        ]
        
    if "starting_budget" not in st.session_state:
        st.session_state.starting_budget = 3412.0

# Cache allocations. It takes tuple types to be fully hash-compatible.
@st.cache_data
def calculate_savings_cached(transactions_tuples, priority_threshold, priority_rate, mappings_tuple, buckets_tuple):
    # Convert back to standard structures
    buckets_list = list(buckets_tuple)
    mappings = dict(mappings_tuple)
    
    allocations = {b: 0.0 for b in buckets_list}
    category_spending = defaultdict(float)
    
    # Filter expenses
    expenses = [tx for tx in transactions_tuples if tx.get("Income/Expense", "").lower() == "expense"]
    
    # Group by date
    expenses_by_day = defaultdict(list)
    for tx in expenses:
        dt_str = tx.get("Date")
        try:
            # We already standardized to string YYYY-MM-DD, parse extremely fast
            dt_parsed = datetime.date.fromisoformat(dt_str)
        except Exception:
            dt_parsed = datetime.date.today()
        expenses_by_day[dt_parsed].append(tx)
        
    daily_summaries = []
    
    for day in sorted(expenses_by_day.keys()):
        day_txns = expenses_by_day[day]
        day_allocations = defaultdict(float)
        
        # Calculate daily category totals
        day_cat_totals = defaultdict(float)
        for tx in day_txns:
            cat = tx.get("Category", "Other")
            amt = float(tx.get("Amount", 0.0))
            day_cat_totals[cat] += amt
            category_spending[cat] += amt
            
        # Determine priority category
        user_priority = None
        for cat, total in day_cat_totals.items():
            if total >= priority_threshold:
                user_priority = cat
                break
                
        # Allocate per transaction
        for tx in day_txns:
            amt = float(tx.get("Amount", 0.0))
            cat = tx.get("Category", "Other")
            
            mapping_info = mappings.get(cat, {"bucket": "Emergency", "rate": 0.01})
            target_bucket = mapping_info.get("bucket", "Emergency")
            if target_bucket not in buckets_list:
                target_bucket = "Emergency" if "Emergency" in buckets_list else buckets_list[0]
                
            rate = float(mapping_info.get("rate", 0.01))
            
            if user_priority and cat == user_priority:
                to_save = round_down_10(amt * priority_rate)
                overflow = (amt * priority_rate) - to_save
                day_allocations[target_bucket] += to_save
                if "Emergency" in buckets_list:
                    day_allocations["Emergency"] += overflow
                else:
                    day_allocations[buckets_list[0]] += overflow
            else:
                day_allocations[target_bucket] += amt * rate
                
        # Accumulate to total
        for b in buckets_list:
            allocations[b] += day_allocations.get(b, 0.0)
            
        daily_summaries.append({
            "date": day,
            "transactions": day_txns,
            "priority_category": user_priority,
            "allocations": dict(day_allocations),
            "total_allocated": sum(day_allocations.values())
        })
        
    return allocations, daily_summaries, dict(category_spending)

# Wrapper to convert state into hashable formats for cache
def run_calculations():
    # Convert list of dicts to tuple of frozensets/tuples
    tx_tuples = tuple(tuple(sorted(d.items())) for d in st.session_state.transactions)
    # Reconstruct dict items for the cache resolver to read easily
    tx_dicts = tuple(dict(t) for t in tx_tuples)
    
    # Convert mappings dict to tuple of key-value tuples
    map_tuples = tuple(
        (cat, tuple(sorted(m.items()))) 
        for cat, m in st.session_state.category_mappings.items()
    )
    # Parse back inside cache
    map_dicts_format = tuple((cat, dict(items)) for cat, items in map_tuples)
    
    buckets_tuple = tuple(st.session_state.custom_buckets)
    
    return calculate_savings_cached(
        tx_dicts, 
        priority_threshold, 
        priority_rate, 
        map_dicts_format, 
        buckets_tuple
    )

# ---------- AI CHATBOT CODE ----------
def query_gemini(api_key, prompt, context_data, model_name="gemini-1.5-flash"):
    try:
        genai.configure(api_key=api_key)
        
        # Dynamically list models available for this API key
        available_models = []
        try:
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    model_clean = m.name.replace("models/", "")
                    available_models.append(model_clean)
        except Exception:
            # Fallback to standard model names if listing fails due to permissions/endpoint
            available_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
            
        # Build model sequence starting with the preferred model
        models_to_try = []
        if model_name in available_models:
            models_to_try.append(model_name)
            
        for m in available_models:
            if m not in models_to_try:
                models_to_try.append(m)
                
        if not models_to_try:
            models_to_try = [model_name, "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
            
        errors = []
        for model_to_query in models_to_try:
            try:
                system_prompt = f"""
You are AutoNest, an intelligent personal finance AI assistant.
Here is the user's current financial context based on their transactions:
{context_data}

Provide professional, actionable, and friendly financial advice. Keep answers clear, structured, and concise. You can reference specific categories and spending metrics.
"""
                model = genai.GenerativeModel(
                    model_name=model_to_query,
                    system_instruction=system_prompt
                )
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                errors.append(f"{model_to_query}: {str(e)}")
                continue
                
        # If all models failed, return detailed diagnostics for each model
        err_msg = " | ".join(errors)
        return f"Error contacting Gemini API (tried models {models_to_try}): {err_msg}. Please check your API key in the sidebar."
    except Exception as e:
        return f"Error configuring Gemini SDK: {str(e)}"

def query_local_bot(prompt, context):
    prompt_lower = prompt.lower()
    
    total_income = context.get("total_income", 0.0)
    total_expenses = context.get("total_expenses", 0.0)
    total_saved = context.get("total_saved", 0.0)
    category_spending = context.get("category_spending", {})
    savings_buckets = context.get("savings_buckets", {})
    goals = context.get("goals", [])
    
    response = ""
    
    if any(k in prompt_lower for k in ["spend", "expense", "cost", "bought", "payment"]):
        response += f"### 📊 Spending Breakdown\n"
        response += f"Based on your transaction records, your **Total Expenses** are **${total_expenses:,.2f}**.\n\n"
        if category_spending:
            response += "Here is what you spent in each category:\n"
            for cat, amt in sorted(category_spending.items(), key=lambda x: x[1], reverse=True):
                pct = (amt / total_expenses * 100) if total_expenses > 0 else 0
                response += f"- **{cat}**: ${amt:,.2f} ({pct:.1f}%)\n"
        else:
            response += "No spending records found.\n"
            
    elif any(k in prompt_lower for k in ["save", "savings", "bucket", "emergency", "travel", "fun", "health"]):
        response += f"### 🏦 Savings & Buckets Summary\n"
        response += f"You have accumulated a total of **${total_saved:,.2f}** in savings. Here is the distribution across buckets:\n\n"
        for bucket, amt in savings_buckets.items():
            response += f"- **{bucket}**: ${amt:,.2f}\n"
        if goals:
            response += "\nHere is your progress towards your goals:\n"
            for g in goals:
                pct = (g['saved'] / g['target'] * 100) if g['target'] > 0 else 0
                response += f"- **{g['name']}**: ${g['saved']:,.2f} of ${g['target']:,.2f} ({pct:.1f}%)\n"

    elif any(k in prompt_lower for k in ["recommend", "advice", "suggest", "tip", "improve", "budget"]):
        response += "### 💡 Personalized Financial Recommendations\n"
        
        savings_rate = (total_saved / total_income * 100) if total_income > 0 else 0
        if total_income == 0:
            savings_rate = (total_saved / total_expenses * 100) if total_expenses > 0 else 0
            
        response += f"1. **Savings Rate**: Your savings rate is **{savings_rate:.1f}%**. "
        if savings_rate < 10:
            response += "This is low. We recommend aiming for at least 15-20% by increasing your contextual allocation percentages in the sidebar.\n"
        elif savings_rate < 25:
            response += "This is a healthy start! Consider setting up a specific goal to lock in those savings.\n"
        else:
            response += "Excellent job! You are saving a significant portion of your capital.\n"
            
        if category_spending:
            top_cat, top_amt = max(category_spending.items(), key=lambda x: x[1])
            top_pct = (top_amt / total_expenses * 100) if total_expenses > 0 else 0
            response += f"\n2. **Category Alert**: Your highest spending is in **{top_cat}** (${top_amt:,.2f}, representing **{top_pct:.1f}%** of total expenses). "
            if top_pct > 30:
                response += f"Spending more than 30% on a single category is high. See if you can reduce discretionary costs here.\n"
            else:
                response += f"Your spending in this category is reasonable relative to your total budget.\n"
        
        if goals:
            slow_goals = [g for g in goals if (g['saved']/g['target']) < 0.5]
            if slow_goals:
                response += f"\n3. **Goals Focus**: You have goals like '{slow_goals[0]['name']}' that are less than 50% funded. Consider adjusting your allocation rules in the sidebar to redirect more savings towards this goal's bucket.\n"
        else:
            response += "\n3. **Set a Goal**: You don't have any financial savings goals set up. Setting explicit targets (like an Emergency fund or major purchase) makes saving much more effective. Go to the *Savings Goals Tracker* tab to create one!\n"

    elif any(k in prompt_lower for k in ["find", "search", "filter"]):
        response += "To search, filter, or export specific transactions, click on the **Transaction Manager** tab! It allows full query capabilities, sorting, and manual edits."
        
    else:
        response += f"""
### 👋 Hello! I am AutoNest, your Financing Agent.

I've analyzed your financial data:
- **Total Income**: ${total_income:,.2f}
- **Total Expenses**: ${total_expenses:,.2f}
- **Net Saved**: ${total_saved:,.2f} (Savings Rate: {(total_saved/total_income*100) if total_income > 0 else 0:.1f}%)

You can ask me questions like:
- *"Show my spending breakdown"*
- *"Summarize my savings buckets"*
- *"Give me some saving recommendations"*

*Tip: For conversational, unrestricted AI responses, input your Gemini API Key in the sidebar!*
"""
    return response

# ---------- INITIALIZE APP STATE ----------
load_default_data()
inject_custom_css()

# ---------- SIDEBAR ELEMENTS ----------
with st.sidebar:
    # Logo Image
    if os.path.exists(local_logo):
        st.image(local_logo, use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #3b82f6;'>AutoNest</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-style: italic; color: #8e8e93;'>AI Financing Agent</p>", unsafe_allow_html=True)
    
    st.divider()
    
    # 1. API Configuration - Bound directly to session state via key parameter
    st.markdown("### 🔑 API Configuration")
    st.text_input(
        "Google Gemini API Key", 
        type="password", 
        key="gemini_key", 
        help="Input your Google Gemini API Key. Value is safely kept across tab changes."
    )
    st.selectbox(
        "Gemini Model",
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro", "gemini-2.5-flash", "gemini-2.5-pro"],
        key="gemini_model",
        help="Select the Gemini model to query. If one model returns a 404 error, try another."
    )
    
    # 2. File Uploader
    st.markdown("### 📁 Data Source")
    uploaded_file = st.file_uploader("Upload CSV transaction file", type="csv")
    
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file)
            uploaded_df = standardize_dataframe(uploaded_df)
            st.session_state.transactions = uploaded_df.to_dict(orient="records")
            st.success("Transactions loaded successfully!")
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
            
    # 3. Budget Settings
    st.markdown("### 💰 Budget & Settings")
    st.session_state.starting_budget = st.number_input("Starting/Monthly Budget ($)", value=float(st.session_state.starting_budget), step=100.0)
    
    # 4. Priority Rule Configuration
    with st.expander("⚙️ Savings Allocation Heuristics"):
        priority_threshold = st.slider("Priority Threshold ($)", min_value=50, max_value=1000, value=200, step=50, help="If spending on a category on a single day exceeds this, it triggers priority mode.")
        priority_rate = st.slider("Priority Savings Rate (%)", min_value=1, max_value=30, value=12, step=1, help="Percentage of priority category expense to allocate to savings.") / 100.0
        
    # 5. Bucket Manager
    with st.expander("🏦 Savings Buckets"):
        st.write("Current Buckets:")
        for bucket in st.session_state.custom_buckets:
            col1, col2 = st.columns([4, 1])
            col1.write(f"- {bucket}")
            if bucket != "Emergency":  # Do not allow deleting Emergency
                if col2.button("🗑️", key=f"del_bucket_{bucket}"):
                    st.session_state.custom_buckets.remove(bucket)
                    st.rerun()
                    
        new_bucket = st.text_input("Add custom bucket")
        if st.button("Add Bucket") and new_bucket:
            cleaned_bucket = new_bucket.strip().title()
            if cleaned_bucket not in st.session_state.custom_buckets:
                st.session_state.custom_buckets.append(cleaned_bucket)
                st.success(f"Added bucket '{cleaned_bucket}'")
                st.rerun()
                
    # 6. Category Mapping Editor - Optimized using a single st.data_editor table
    with st.expander("🗺️ Category to Bucket Mappings"):
        unique_categories = sorted(list(set(tx.get("Category", "Other") for tx in st.session_state.transactions)))
        
        # Initialize missing mappings
        for cat in unique_categories:
            if cat not in st.session_state.category_mappings:
                st.session_state.category_mappings[cat] = {"bucket": "Emergency", "rate": 0.01}
        
        # Convert current mapping state into a DataFrame
        mapping_rows = []
        for cat in unique_categories:
            m = st.session_state.category_mappings.get(cat, {"bucket": "Emergency", "rate": 0.01})
            mapping_rows.append({
                "Category": cat,
                "Target Bucket": m.get("bucket", "Emergency"),
                "Rate (%)": float(m.get("rate", 0.01) * 100)
            })
        mapping_df = pd.DataFrame(mapping_rows)
        
        # Render a single interactive table widget
        edited_df = st.data_editor(
            mapping_df,
            column_config={
                "Category": st.column_config.TextColumn(disabled=True),
                "Target Bucket": st.column_config.SelectboxColumn(options=st.session_state.custom_buckets, width="medium"),
                "Rate (%)": st.column_config.NumberColumn(min_value=0.0, max_value=100.0, step=0.5, format="%.1f%%")
            },
            hide_index=True,
            use_container_width=True,
            key="mapping_editor_table"
        )
        
        # Re-populate mapping state from edited DataFrame
        new_mappings = {}
        for _, row in edited_df.iterrows():
            cat = row["Category"]
            new_mappings[cat] = {
                "bucket": row["Target Bucket"],
                "rate": float(row["Rate (%)"]) / 100.0
            }
        st.session_state.category_mappings = new_mappings
            
    # Reset Button
    st.divider()
    if st.button("Reset App to Defaults"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ---------- RUN SAVINGS CALCULATION (CACHED) ----------
savings_allocations, daily_summaries, category_spending = run_calculations()

# ---------- FINANCIAL SUMMARY MATH ----------
income_txns = [tx for tx in st.session_state.transactions if tx.get("Income/Expense", "").lower() == "income"]
expense_txns = [tx for tx in st.session_state.transactions if tx.get("Income/Expense", "").lower() == "expense"]

total_income = sum(float(tx.get("Amount", 0.0)) for tx in income_txns) + st.session_state.starting_budget
total_expenses = sum(float(tx.get("Amount", 0.0)) for tx in expense_txns)
total_savings_allocated = sum(savings_allocations.values())
net_cash_remaining = total_income - total_expenses - total_savings_allocated
savings_rate_percent = (total_savings_allocated / total_income * 100) if total_income > 0 else 0.0

# ---------- MAIN INTERFACE LAYOUT ----------
st.title("AutoNest: AI-Powered Personal Finance Dashboard")
st.markdown("Welcome to **AutoNest**, your personal financing AI agent. View analytics, modify transactions, manage savings goals, and chat with your agent.")

# Create the tabs
tab_dash, tab_tx, tab_goals, tab_chat = st.tabs([
    "📊 Dashboard & Analytics", 
    "🗃️ Transaction Manager", 
    "🎯 Savings Goals Tracker", 
    "💬 AI Financial Chatbot"
])

# ================= TAB 1: DASHBOARD =================
with tab_dash:
    # Metric cards
    st.markdown("""
    <div class='metric-container'>
        <div class='metric-card'>
            <div class='metric-title'>Total Income & Funds</div>
            <div class='metric-value'>${:,.2f}</div>
            <div class='metric-subtitle neutral'>Includes Starting Budget</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Total Expenses</div>
            <div class='metric-value'>${:,.2f}</div>
            <div class='metric-subtitle negative'>Spent to Date</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Savings Allocated</div>
            <div class='metric-value'>${:,.2f}</div>
            <div class='metric-subtitle'>Savings Rate: {:.1f}%</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Net Cash Remaining</div>
            <div class='metric-value'>${:,.2f}</div>
            <div class='metric-subtitle {}'>Liquid Cash Account</div>
        </div>
    </div>
    """.format(
        total_income, 
        total_expenses, 
        total_savings_allocated, 
        savings_rate_percent, 
        net_cash_remaining,
        "negative" if net_cash_remaining < 0 else "neutral"
    ), unsafe_allow_html=True)
    
    # Graphs Row with try-except safety locks to prevent white screen crashes
    col_pie, col_bar = st.columns(2)
    
    with col_pie:
        st.markdown("### 🏦 Savings Allocation Across Buckets")
        try:
            if total_savings_allocated > 0:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=list(savings_allocations.keys()),
                    values=list(savings_allocations.values()),
                    hole=0.4,
                    marker=dict(colors=px.colors.qualitative.Pastel)
                )])
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#ffffff",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    margin=dict(t=10, b=40, l=10, r=10)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No savings allocated yet. Adjust your settings or add transactions!")
        except Exception as e:
            st.error(f"Error rendering savings allocation: {str(e)}")
            
    with col_bar:
        st.markdown("### 🛒 Spending by Category")
        try:
            if category_spending:
                cat_df = pd.DataFrame({
                    "Category": list(category_spending.keys()),
                    "Amount ($)": list(category_spending.values())
                }).sort_values(by="Amount ($)", ascending=True)
                
                fig_bar = px.bar(
                    cat_df,
                    y="Category",
                    x="Amount ($)",
                    orientation="h",
                    color="Amount ($)",
                    color_continuous_scale="Viridis"
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#ffffff",
                    margin=dict(t=10, b=10, l=10, r=10)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No expense transactions recorded.")
        except Exception as e:
            st.error(f"Error rendering category breakdown: {str(e)}")
            
    # Trend Chart
    st.markdown("### 📈 Spending Trend over Time")
    try:
        if expense_txns:
            trend_df = pd.DataFrame(expense_txns)
            trend_df["Date"] = pd.to_datetime(trend_df["Date"])
            trend_grouped = trend_df.groupby("Date")["Amount"].sum().reset_index().sort_values(by="Date")
            
            fig_trend = px.area(
                trend_grouped,
                x="Date",
                y="Amount",
                labels={"Amount": "Spent ($)"}
            )
            fig_trend.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#ffffff",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No spending trends to display.")
    except Exception as e:
        st.error(f"Error rendering spending trend: {str(e)}")
        
    # Capped daily breakdown explorer to resolve heavy element browser crashes
    st.markdown("### 📅 Daily Allocations Breakdown")
    if daily_summaries:
        total_days = len(daily_summaries)
        default_days_show = min(7, total_days)
        
        # UI controls to let user view more logs if they want, default to 7 days
        num_days_to_show = st.slider("Number of recent daily summaries to load", min_value=1, max_value=total_days, value=default_days_show)
        
        recent_summaries = list(reversed(daily_summaries))
        for idx, day_sum in enumerate(recent_summaries[:num_days_to_show]):
            day_date = day_sum["date"]
            day_total_allocated = day_sum["total_allocated"]
            priority_cat = day_sum["priority_category"]
            
            badge_html = ""
            if priority_cat:
                badge_html = f"<span class='badge badge-priority'>⭐ Priority Mode: {priority_cat}</span>"
            else:
                badge_html = "<span class='badge badge-balanced'>🟢 Balanced Mode</span>"
                
            with st.expander(f"{day_date.strftime('%Y-%m-%d')} | Saved: ${day_total_allocated:.2f}"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"**Allocation Mode**: {badge_html}", unsafe_allow_html=True)
                    st.markdown("**Savings Generated**:")
                    alloc_data = {"Bucket": [], "Amount ($)": []}
                    for bucket, amt in day_sum["allocations"].items():
                        if amt > 0:
                            alloc_data["Bucket"].append(bucket)
                            alloc_data["Amount ($)"].append(round(amt, 2))
                    if alloc_data["Bucket"]:
                        st.dataframe(pd.DataFrame(alloc_data), use_container_width=True, hide_index=True)
                    else:
                        st.write("No savings generated today.")
                with col2:
                    st.markdown("**Daily Transactions**:")
                    day_tx_df = pd.DataFrame(day_sum["transactions"])[["Category", "Amount", "Note", "Income/Expense"]]
                    st.dataframe(day_tx_df, use_container_width=True, hide_index=True)
    else:
        st.write("No daily summary available.")

# ================= TAB 2: TRANSACTION MANAGER =================
with tab_tx:
    st.markdown("<div class='section-title'>Transaction Explorer & Database Editor</div>", unsafe_allow_html=True)
    
    col_filters, col_add = st.columns([2, 1])
    
    with col_filters:
        st.markdown("#### 🔍 Filter Database")
        search_q = st.text_input("Search notes or subcategories", "")
        
        c_filter = st.multiselect("Filter by Category", unique_categories, default=[])
        t_filter = st.selectbox("Transaction Type", ["All", "Expense", "Income"])
        
        # Filter transactions
        filtered_txs = st.session_state.transactions.copy()
        if search_q:
            filtered_txs = [t for t in filtered_txs if search_q.lower() in t.get("Note", "").lower() or search_q.lower() in t.get("Subcategory", "").lower()]
        if c_filter:
            filtered_txs = [t for t in filtered_txs if t.get("Category") in c_filter]
        if t_filter != "All":
            filtered_txs = [t for t in filtered_txs if t.get("Income/Expense", "").lower() == t_filter.lower()]
            
        st.markdown(f"**Found {len(filtered_txs)} transactions**")
        if filtered_txs:
            df_display = pd.DataFrame(filtered_txs)
            st.dataframe(df_display[["Date", "Category", "Subcategory", "Note", "Amount", "Income/Expense"]], use_container_width=True)
            
            # Export CSV
            csv_buf = io.StringIO()
            df_display.to_csv(csv_buf, index=False)
            st.download_button("📥 Export Filtered Database as CSV", csv_buf.getvalue(), "exported_transactions.csv", "text/csv")
        else:
            st.info("No transactions match the selected filters.")
            
    with col_add:
        st.markdown("#### ➕ Add New Transaction")
        with st.form("add_tx_form", clear_on_submit=True):
            new_date = st.date_input("Transaction Date", value=datetime.date.today())
            new_type = st.selectbox("Type", ["Expense", "Income"])
            
            new_cat_choice = st.selectbox("Category", unique_categories + ["New Category"])
            if new_cat_choice == "New Category":
                new_cat = st.text_input("Enter New Category Name").strip().title()
            else:
                new_cat = new_cat_choice
                
            new_subcat = st.text_input("Subcategory (optional)")
            new_note = st.text_input("Description / Note")
            new_amount = st.number_input("Amount ($)", min_value=0.0, step=1.0)
            
            submit_tx = st.form_submit_button("Add Transaction to Database")
            if submit_tx:
                if new_cat == "":
                    st.error("Category cannot be empty!")
                elif new_amount <= 0:
                    st.error("Amount must be greater than 0!")
                else:
                    new_record = {
                        "Date": new_date.strftime("%Y-%m-%d"),
                        "Amount": new_amount,
                        "Category": new_cat,
                        "Subcategory": new_subcat,
                        "Note": new_note,
                        "Income/Expense": new_type.lower()
                    }
                    st.session_state.transactions.append(new_record)
                    # Clear cache by changing st.session_state.transactions length
                    st.success(f"Added: {new_note} (${new_amount:.2f})")
                    st.rerun()
                    
        # CRUD: Delete transactions
        st.markdown("#### 🗑️ Delete Transactions")
        if st.session_state.transactions:
            tx_options = [f"{idx}: {t.get('Date')} - {t.get('Category')} - {t.get('Note')} (${t.get('Amount')})" for idx, t in enumerate(st.session_state.transactions)]
            tx_to_del = st.selectbox("Select Transaction to Delete", options=tx_options)
            if st.button("Delete Transaction"):
                idx_to_del = int(tx_to_del.split(":")[0])
                removed = st.session_state.transactions.pop(idx_to_del)
                st.warning(f"Deleted transaction: {removed.get('Note')} (${removed.get('Amount')})")
                st.rerun()

# ================= TAB 3: SAVINGS GOALS =================
with tab_goals:
    st.markdown("<div class='section-title'>Interactive Financial Goals Tracker</div>", unsafe_allow_html=True)
    
    col_list, col_actions = st.columns([2, 1])
    
    with col_list:
        st.markdown("#### 🎯 Active Savings Goals")
        if st.session_state.goals:
            for g in st.session_state.goals:
                pct = (g["saved"] / g["target"] * 100) if g["target"] > 0 else 0
                pct = min(100.0, pct)
                
                st.markdown(f"""
                <div class='goal-card'>
                    <div class='goal-header'>
                        <span class='goal-title'>{g['name']}</span>
                        <span class='goal-target'>Target: ${g['target']:,.2f}</span>
                    </div>
                    <div class='goal-progress-container'>
                        <div class='goal-progress-bar' style='width: {pct}%'></div>
                    </div>
                    <div class='goal-footer'>
                        <span>Saved: ${g['saved']:,.2f} ({pct:.1f}%)</span>
                        <span>Bucket: {g['bucket']} | Deadline: {g['deadline']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No savings goals configured. Add your first goal on the right!")
            
    with col_actions:
        st.markdown("#### ➕ Create Savings Goal")
        with st.form("add_goal_form", clear_on_submit=True):
            g_name = st.text_input("Goal Name (e.g. Vacation, Laptop)")
            g_target = st.number_input("Target Amount ($)", min_value=1.0, value=1000.0, step=100.0)
            g_deadline = st.date_input("Target Date", value=datetime.date.today() + datetime.timedelta(days=180))
            g_bucket = st.selectbox("Link to Savings Bucket", st.session_state.custom_buckets)
            
            submit_goal = st.form_submit_button("Create Financial Goal")
            if submit_goal and g_name:
                new_id = max([g["id"] for g in st.session_state.goals], default=0) + 1
                new_goal = {
                    "id": new_id,
                    "name": g_name,
                    "target": g_target,
                    "saved": 0.0,
                    "deadline": g_deadline.strftime("%Y-%m-%d"),
                    "bucket": g_bucket
                }
                st.session_state.goals.append(new_goal)
                st.success(f"Goal '{g_name}' created successfully!")
                st.rerun()
                
        st.markdown("#### 💸 Allocate Funds to Goal")
        if st.session_state.goals:
            goal_choices = {g["id"]: f"{g['name']} (Target: ${g['target']})" for g in st.session_state.goals}
            selected_g_id = st.selectbox("Select Target Goal", options=list(goal_choices.keys()), format_func=lambda x: goal_choices[x])
            selected_goal = next(g for g in st.session_state.goals if g["id"] == selected_g_id)
            
            source_bucket = selected_goal["bucket"]
            available_funds = savings_allocations.get(source_bucket, 0.0)
            
            allocated_to_other_goals = sum(g["saved"] for g in st.session_state.goals if g["bucket"] == source_bucket)
            remaining_bucket_funds = max(0.0, available_funds - allocated_to_other_goals + selected_goal["saved"])
            
            st.write(f"Remaining funds in **{source_bucket}** bucket: **${remaining_bucket_funds:.2f}**")
            
            transfer_amount = st.number_input("Transfer Amount ($)", min_value=0.0, max_value=float(remaining_bucket_funds), step=10.0)
            if st.button("Transfer Funds"):
                selected_goal["saved"] = transfer_amount
                st.success(f"Transferred! '{selected_goal['name']}' now has ${transfer_amount:.2f} allocated.")
                st.rerun()
                
            st.markdown("#### 🗑️ Delete Goal")
            st.warning("Deleting a goal releases its funds back into its linked bucket.")
            if st.button("Delete Selected Goal"):
                st.session_state.goals = [g for g in st.session_state.goals if g["id"] != selected_g_id]
                st.success("Goal deleted.")
                st.rerun()

# ================= TAB 4: AI FINANCIAL ASSISTANT =================
with tab_chat:
    st.markdown("<div class='section-title'>AutoNest AI Financial Advisor</div>", unsafe_allow_html=True)
    st.write("Ask your AI Agent anything about your spending history, budgets, saving recommendations, or goals progress.")
    
    # Render historical chat
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])
            
    # Compile advisor query context
    context_dict = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_saved": total_savings_allocated,
        "savings_buckets": savings_allocations,
        "category_spending": dict(category_spending),
        "goals": st.session_state.goals
    }
    
    # Chat prompt box
    chat_prompt = st.chat_input("Ask a financial question...")
    
    if chat_prompt:
        st.chat_message("user").write(chat_prompt)
        st.session_state.chat_history.append({"role": "user", "content": chat_prompt})
        
        # Load API Key from session state key binding
        gemini_key = st.session_state.get("gemini_key", "")
        gemini_model = st.session_state.get("gemini_model", "gemini-1.5-flash")
        
        with st.spinner("Analyzing data & thinking..."):
            if gemini_key:
                bot_response = query_gemini(gemini_key, chat_prompt, str(context_dict), model_name=gemini_model)
            else:
                bot_response = query_local_bot(chat_prompt, context_dict)
                
        st.chat_message("assistant").write(bot_response)
        st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
        st.rerun()
        
    if st.button("🧹 Clear Chat History"):
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I am AutoNest, your AI Financing Agent. Ask me anything!"}
        ]
        st.rerun()