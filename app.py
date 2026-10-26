import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import os

st.set_page_config(layout="wide", page_title="Market Maker Simulator")
st.title("Avellaneda-Stoikov Market Maker Dashboard")

# 1. Interactive Sliders (Sidebar)
st.sidebar.header("Tuning Parameters")
gamma = st.sidebar.slider("Risk Aversion (Gamma)", min_value=0.01, max_value=0.50, value=0.10, step=0.01)
k = st.sidebar.slider("Liquidity Depth (k)", min_value=0.5, max_value=5.0, value=1.5, step=0.1)
jump_intensity = st.sidebar.slider("Market Shock Probability", min_value=0.0, max_value=0.20, value=0.05, step=0.01)

# 2. Run the C++ Backend 
if os.path.exists("./sim"):
    subprocess.run(["./sim", str(gamma), str(k), str(jump_intensity)])
else:
    st.error("C++ executable './sim' not found. Please compile main.cpp first.")
    st.stop()

# 3. Load the newly generated data
df = pd.read_csv("simulation_ledger.csv")

# 4. Calculate Metrics
final_pnl = df["TotalPnL"].iloc[-1]
df["Peak"] = df["TotalPnL"].cummax()
df["Drawdown"] = df["TotalPnL"] - df["Peak"]
max_drawdown = df["Drawdown"].min()
avg_spread = (df["AgentAsk"] - df["AgentBid"]).mean()

# Display Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Final PnL", f"${final_pnl:.2f}")
col2.metric("Max Drawdown", f"${max_drawdown:.2f}")
col3.metric("Avg Spread", f"${avg_spread:.4f}")

# 5. Plot the Dashboard
fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# Panel 1: Price Action
axs[0].plot(df["TimeStep"], df["MidPrice"], label="Mid Price", color="black", linewidth=1.5)
axs[0].plot(df["TimeStep"], df["AgentBid"], label="Agent Bid", color="green", alpha=0.6, linestyle="--")
axs[0].plot(df["TimeStep"], df["AgentAsk"], label="Agent Ask", color="blue", alpha=0.6, linestyle="--")
shocks = df[df["IsShock"] == 1]
axs[0].scatter(shocks["TimeStep"], shocks["MidPrice"], color="red", label="Market Shock", zorder=5)
axs[0].set_ylabel("Price")
axs[0].legend(loc="upper left")
axs[0].grid(True, alpha=0.3)

# Panel 2: Inventory
axs[1].plot(df["TimeStep"], df["Inventory"], color="purple", linewidth=1.5)
axs[1].axhline(0, color="black", linestyle="--", alpha=0.5)
axs[1].set_ylabel("Inventory Position")
axs[1].grid(True, alpha=0.3)

# Panel 3: PnL
axs[2].plot(df["TimeStep"], df["TotalPnL"], label="Total PnL", color="green", linewidth=1.5)
axs[2].plot(df["TimeStep"], df["Peak"], color="grey", linestyle=":", alpha=0.7)
axs[2].fill_between(df["TimeStep"], df["TotalPnL"], df["Peak"], color="red", alpha=0.3)
axs[2].set_xlabel("Time Step")
axs[2].set_ylabel("PnL ($)")
axs[2].grid(True, alpha=0.3)

plt.tight_layout()

# Render the plot in Streamlit
st.pyplot(fig)