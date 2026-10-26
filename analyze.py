import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the ledger
df = pd.read_csv("simulation_ledger.csv")

# -----------------------------------------
# 1. Calculate Metrics
# -----------------------------------------
final_pnl = df["TotalPnL"].iloc[-1]

# Max Drawdown Calculation
df["Peak"] = df["TotalPnL"].cummax()
df["Drawdown"] = df["TotalPnL"] - df["Peak"]
max_drawdown = df["Drawdown"].min()

# Spread Capture
df["Spread"] = df["AgentAsk"] - df["AgentBid"]
avg_spread = df["Spread"].mean()

print("=== Simulation Performance Metrics ===")
print(f"Final Total PnL:      ${final_pnl:.2f}")
print(f"Maximum Drawdown:     ${max_drawdown:.2f}")
print(f"Average Spread Width: ${avg_spread:.4f}")
print("======================================")

# -----------------------------------------
# 2. Build the 3-Panel Dashboard
# -----------------------------------------
fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
fig.suptitle("Avellaneda-Stoikov Market Maker Performance", fontsize=16)

# Panel 1: Price Action and Quotes
axs[0].plot(df["TimeStep"], df["MidPrice"], label="Mid Price", color="black", linewidth=1.5)
axs[0].plot(df["TimeStep"], df["AgentBid"], label="Agent Bid", color="green", alpha=0.6, linestyle="--")
axs[0].plot(df["TimeStep"], df["AgentAsk"], label="Agent Ask", color="blue", alpha=0.6, linestyle="--")

# Highlight Market Shocks
shocks = df[df["IsShock"] == 1]
axs[0].scatter(shocks["TimeStep"], shocks["MidPrice"], color="red", label="Market Shock", zorder=5)

axs[0].set_ylabel("Price")
axs[0].set_title("Market Mid-Price vs Agent Quotes")
axs[0].legend(loc="upper left")
axs[0].grid(True, alpha=0.3)

# Panel 2: Inventory Management
axs[1].plot(df["TimeStep"], df["Inventory"], color="purple", linewidth=1.5)
axs[1].axhline(0, color="black", linestyle="--", alpha=0.5) # Zero line
axs[1].set_ylabel("Held Inventory")
axs[1].set_title("Agent Inventory Position (Mean Reversion)")
axs[1].grid(True, alpha=0.3)

# Panel 3: PnL and Drawdowns
axs[2].plot(df["TimeStep"], df["TotalPnL"], label="Total PnL", color="green", linewidth=1.5)
axs[2].plot(df["TimeStep"], df["Peak"], label="High Water Mark", color="grey", linestyle=":", alpha=0.7)

# Shade the drawdown periods
axs[2].fill_between(df["TimeStep"], df["TotalPnL"], df["Peak"], color="red", alpha=0.3, label="Drawdown")

axs[2].set_xlabel("Time Step")
axs[2].set_ylabel("PnL ($)")
axs[2].set_title("Cumulative Profit and Loss with Drawdowns")
axs[2].legend(loc="upper left")
axs[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()