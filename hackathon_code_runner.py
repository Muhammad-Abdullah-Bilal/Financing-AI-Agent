"""hackathon_code_runner.py

Enhanced Financing AI Agent (AutoNest) with colorful CLI, weekly summary, and improved visuals.
"""

import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import math
from rich.console import Console
from rich.table import Table
import sys

# Initialize rich console for colorful output
console = Console()

# ---------- SETTINGS ----------
TOTAL_FUNDS = 3412
CSV_FILE = "dummy_transactions.csv"

# ---------- HELPER FUNCTIONS ----------
def round_down_10(x):
    return int(math.floor(x / 10.0)) * 10

def allocate_daily(transactions, user_priority=None):
    allocations = defaultdict(float)

    for tx in transactions:
        amt = tx["Amount"]
        cat = tx["Category"]
        percent = amt / TOTAL_FUNDS

        # Priority mode
        if user_priority and cat == user_priority:
            to_save = round_down_10(amt * 0.12)
            overflow = (amt * 0.12) - to_save
            allocations[user_priority] += to_save
            allocations["Emergency"] += overflow
            continue

        # Contextual logic
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

# ---------- LOAD TRANSACTIONS ----------
try:
    df = pd.read_csv(CSV_FILE)
    # Rename columns to match expected format
    df = df.rename(columns={"timestamp": "Date", "amount": "Amount", "category": "Category"})
    # Add Income/Expense column if missing
    if "Income/Expense" not in df.columns:
        df["Income/Expense"] = "expense"
    # Filter only expense rows
    df = df[df["Income/Expense"].str.lower() == "expense"]
    # Convert Date with dayfirst=True to handle DD/MM/YYYY
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce").dt.date
    transactions = df.to_dict(orient="records")
except FileNotFoundError:
    console.print(f"[red]Error: {CSV_FILE} not found.[/red]")
    sys.exit(1)
except KeyError as e:
    console.print(f"[red]Error: Missing column {e} in CSV.[/red]")
    sys.exit(1)

# Group by Date
grouped_by_day = defaultdict(list)
for tx in transactions:
    grouped_by_day[tx["Date"]].append(tx)

# Savings buckets
savings_buckets = {
    "Emergency": 0,
    "Travel": 0,
    "Fun": 0,
    "Health": 0
}

# Track spending per category for weekly summary
category_spending = defaultdict(float)

# ---------- MAIN LOGIC LOOP ----------
PRIORITY_THRESHOLD = 200

for day, txns in grouped_by_day.items():
    console.print(f"\n📅 [bold cyan]{day}[/bold cyan]:")
    
    # Calculate total spent per category for the day
    category_totals = defaultdict(float)
    for tx in txns:
        category_totals[tx["Category"]] += tx["Amount"]
        category_spending[tx["Category"]] += tx["Amount"]

    # Determine if any category qualifies as a priority
    user_priority = None
    for cat, total in category_totals.items():
        if total >= PRIORITY_THRESHOLD:
            user_priority = cat
            break

    if user_priority:
        console.print(f"[green]Auto-detected priority category: [bold]{user_priority}[/bold][/green]")
        allocations = allocate_daily(txns, user_priority=user_priority)
    else:
        console.print("[yellow]Balanced mode selected.[/yellow]")
        allocations = allocate_daily(txns)

    for category in savings_buckets:
        savings_buckets[category] += allocations.get(category, 0)

    # Daily Summary
    console.print("\n📊 [bold]Daily Summary[/bold]:")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Amount", justify="right", style="green")
    daily_total = 0
    priority_category = None
    max_allocated = 0

    for category in savings_buckets:
        amount = allocations.get(category, 0)
        daily_total += amount
        table.add_row(category, f"${amount:.2f}")
        if amount > max_allocated:
            max_allocated = amount
            priority_category = category

    console.print(table)
    console.print(f"[bold]→ Total Allocated Today:[/bold] [green]${daily_total:.2f}[/green]")
    if priority_category and max_allocated > 0:
        percent = (max_allocated / daily_total) * 100
        console.print(f"[bold]⭐ Priority of the Day:[/bold] [cyan]{priority_category}[/cyan] ([green]${max_allocated:.2f}[/green] – [yellow]{percent:.1f}%[/yellow])")
    console.print("-" * 50)

# ---------- WEEKLY SUMMARY ----------
console.print("\n📈 [bold underline]Weekly Summary[/bold underline]:")
total_saved = sum(savings_buckets.values())
most_spent_category = max(category_spending.items(), key=lambda x: x[1], default=("None", 0))[0]
top_savings_bucket = max(savings_buckets.items(), key=lambda x: x[1], default=("None", 0))[0]

console.print(f"[bold]Most Frequently Prioritized Category:[/bold] [cyan]{most_spent_category}[/cyan]")
console.print(f"[bold]Category with Most Spending:[/bold] [cyan]{most_spent_category}[/cyan] ([green]${category_spending[most_spent_category]:.2f}[/green])")
console.print(f"[bold]Top Savings Bucket:[/bold] [cyan]{top_savings_bucket}[/cyan] ([green]${savings_buckets[top_savings_bucket]:.2f}[/green])")
console.print("\n[bold]Savings Breakdown:[/bold]")
table = Table(show_header=True, header_style="bold magenta")
table.add_column("Bucket", style="cyan")
table.add_column("Amount", justify="right", style="green")
table.add_column("Percentage", justify="right", style="yellow")
for bucket, amount in savings_buckets.items():
    percent = (amount / total_saved * 100) if total_saved > 0 else 0
    table.add_row(bucket, f"${amount:.2f}", f"{percent:.1f}%")
console.print(table)
console.print(f"[bold]Total Saved:[/bold] [green]${total_saved:.2f}[/green]")

# ---------- PLOT RESULTS ----------
labels = savings_buckets.keys()
sizes = savings_buckets.values()
colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
explode = [0.1 if size == max(sizes) else 0 for size in sizes]

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90, explode=explode, shadow=True)
plt.title("AutoNest – Smart Savings Allocation")
plt.legend(labels, loc="best")
plt.axis("equal")
plt.savefig("savings_allocation.png")
plt.show()  # Added to display pie chart
plt.close()
console.print("\n[bold green]Pie chart saved as 'savings_allocation.png'[/bold green]")