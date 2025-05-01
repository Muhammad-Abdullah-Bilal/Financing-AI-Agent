import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import math
import streamlit as st
import io

# Streamlit page config
st.set_page_config(page_title="AutoNest - Financing AI Agent", layout="wide")

# ---------- SETTINGS ----------
TOTAL_FUNDS = 3412
PRIORITY_THRESHOLD = 200

# ---------- HELPER FUNCTIONS ----------
def round_down_10(x):
    return int(math.floor(x / 10.0)) * 10

def allocate_daily(transactions, user_priority=None):
    allocations = defaultdict(float)
    for tx in transactions:
        amt = tx["Amount"]
        cat = tx["Category"]
        percent = amt / TOTAL_FUNDS
        if user_priority and cat == user_priority:
            to_save = round_down_10(amt * 0.12)
            overflow = (amt * 0.12) - to_save
            allocations[user_priority] += to_save
            allocations["Emergency"] += overflow
            continue
        if cat == "Food":
            allocations["Emergency"] += amt * 0.05
        elif cat == "Entertainment":
            allocations["Fun"] += amt * 0.05
        elif cat == "Transport":
            allocations["Travel"] += amt * 0.05
        elif cat == "Healthcare":
            if percent >= 0.10:
                to_save = amt * 0.10
                rounded = round_down_10(to_save)
                allocations["Health"] += rounded
                allocations["Emergency"] += (to_save - rounded)
            else:
                allocations["Health"] += amt * 0.10
        else:
            allocations["Emergency"] += amt * 0.01
    return allocations

# ---------- STREAMLIT APP ----------
st.title("AutoNest - Smart Financing AI Agent")
st.write("Upload your transaction CSV to analyze and allocate savings into Emergency, Travel, Fun, and Health buckets.")

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file (e.g., dummy_transactions.csv)", type="csv")

if uploaded_file is not None:
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        df = df.rename(columns={"timestamp": "Date", "amount": "Amount", "category": "Category"})
        if "Income/Expense" not in df.columns:
            df["Income/Expense"] = "expense"
        df = df[df["Income/Expense"].str.lower() == "expense"]
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce").dt.date
        transactions = df.to_dict(orient="records")
        
        # Group by Date
        grouped_by_day = defaultdict(list)
        for tx in transactions:
            grouped_by_day[tx["Date"]].append(tx)
        
        # Savings buckets
        savings_buckets = {"Emergency": 0, "Travel": 0, "Fun": 0, "Health": 0}
        category_spending = defaultdict(float)
        
        # Process transactions
        if st.button("Analyze Transactions"):
            st.header("Daily Summaries")
            for day, txns in sorted(grouped_by_day.items()):
                st.subheader(f"📅 {day}")
                
                # Calculate total spent per category
                category_totals = defaultdict(float)
                for tx in txns:
                    category_totals[tx["Category"]] += tx["Amount"]
                    category_spending[tx["Category"]] += tx["Amount"]
                
                # Determine priority
                user_priority = None
                for cat, total in category_totals.items():
                    if total >= PRIORITY_THRESHOLD:
                        user_priority = cat
                        break
                
                if user_priority:
                    st.write(f"**Auto-detected priority category**: {user_priority}")
                    allocations = allocate_daily(txns, user_priority=user_priority)
                else:
                    st.write("**Balanced mode selected**")
                    allocations = allocate_daily(txns)
                
                for category in savings_buckets:
                    savings_buckets[category] += allocations.get(category, 0)
                
                # Daily Summary Table
                st.write("**Daily Summary**")
                daily_data = {"Category": [], "Amount ($)": []}
                daily_total = 0
                priority_category = None
                max_allocated = 0
                for category in savings_buckets:
                    amount = allocations.get(category, 0)
                    daily_data["Category"].append(category)
                    daily_data["Amount ($)"].append(round(amount, 2))
                    daily_total += amount
                    if amount > max_allocated:
                        max_allocated = amount
                        priority_category = category
                st.dataframe(daily_data, use_container_width=True)
                st.write(f"**Total Allocated Today**: ${daily_total:.2f}")
                if priority_category and max_allocated > 0:
                    percent = (max_allocated / daily_total) * 100
                    st.write(f"**Priority of the Day**: {priority_category} (${max_allocated:.2f} – {percent:.1f}%)")
                st.write("---")
            
            # Weekly Summary
            st.header("Weekly Summary")
            total_saved = sum(savings_buckets.values())
            most_spent_category = max(category_spending.items(), key=lambda x: x[1], default=("None", 0))[0]
            top_savings_bucket = max(savings_buckets.items(), key=lambda x: x[1], default=("None", 0))[0]
            
            st.write(f"**Most Frequently Prioritized Category**: {most_spent_category}")
            st.write(f"**Category with Most Spending**: {most_spent_category} (${category_spending[most_spent_category]:.2f})")
            st.write(f"**Top Savings Bucket**: {top_savings_bucket} (${savings_buckets[top_savings_bucket]:.2f})")
            
            st.write("**Savings Breakdown**")
            weekly_data = {"Bucket": [], "Amount ($)": [], "Percentage (%)": []}
            for bucket, amount in savings_buckets.items():
                percent = (amount / total_saved * 100) if total_saved > 0 else 0
                weekly_data["Bucket"].append(bucket)
                weekly_data["Amount ($)"].append(round(amount, 2))
                weekly_data["Percentage (%)"].append(round(percent, 1))
            st.dataframe(weekly_data, use_container_width=True)
            st.write(f"**Total Saved**: ${total_saved:.2f}")
            
            # Pie Chart
            labels = savings_buckets.keys()
            sizes = savings_buckets.values()
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            explode = [0.1 if size == max(sizes) else 0 for size in sizes]
            
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90, explode=explode, shadow=True)
            ax.set_title("AutoNest – Smart Savings Allocation")
            ax.legend(labels, loc="best")
            ax.axis("equal")
            st.pyplot(fig)
            plt.close()
            
            # Download pie chart
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            st.download_button("Download Pie Chart", buf.getvalue(), "savings_allocation.png", "image/png")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("Please upload a CSV file to begin.")