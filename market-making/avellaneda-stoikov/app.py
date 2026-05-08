import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="MM Dashboard: Inventory vs. Symmetric", layout="wide")

# --- Initialize Session State for Graphs & Parameters ---
if 'sweep_fig' not in st.session_state:
    st.session_state.sweep_fig = None
if 'heat_fig' not in st.session_state:
    st.session_state.heat_fig = None
if 'sweep_params' not in st.session_state:
    st.session_state.sweep_params = None
if 'heat_params' not in st.session_state:
    st.session_state.heat_params = None

# --- 1. Simulation Engine (Cached for Performance) ---
@st.cache_data
def run_simulation(gamma, sigma, A, k, ask_mult, bid_mult, n_sims, T=1.0, dt=0.01):
    N = int(T / dt)
    time_grid = np.linspace(0, T, N)
    s_0 = 100.0
    inv_pnl_all = []; sym_pnl_all = []
    inv_q_all = []; sym_q_all = []

    for sim in range(n_sims):
        S = np.zeros(N); S[0] = s_0
        q_i = np.zeros(N); q_s = np.zeros(N)
        X_i = np.zeros(N); X_s = np.zeros(N)
        
        for i in range(N - 1):
            t = time_grid[i]
            # Inventory Strategy
            r = S[i] - q_i[i] * gamma * (sigma**2) * (T - t)
            spread = gamma * (sigma**2) * (T - t) + (2/gamma) * np.log(1 + gamma/k)
            p_a_i, p_b_i = r + spread/2, r - spread/2
            
            # Symmetric Strategy
            p_a_s, p_b_s = S[i] + spread/2, S[i] - spread/2
            
            # Poisson arrival intensities
            lamb_a_i = A * np.exp(-k * (p_a_i - S[i])) * ask_mult
            lamb_b_i = A * np.exp(-k * (S[i] - p_b_i)) * bid_mult
            lamb_a_s = A * np.exp(-k * (p_a_s - S[i])) * ask_mult
            lamb_b_s = A * np.exp(-k * (S[i] - p_b_s)) * bid_mult
            
            rnd = np.random.rand(4)
            if rnd[0] < lamb_a_i * dt: q_i[i+1], X_i[i+1] = q_i[i]-1, X_i[i]+p_a_i
            else: q_i[i+1], X_i[i+1] = q_i[i], X_i[i]
            if rnd[1] < lamb_b_i * dt: q_i[i+1], X_i[i+1] = q_i[i+1]+1, X_i[i+1]-p_b_i

            if rnd[2] < lamb_a_s * dt: q_s[i+1], X_s[i+1] = q_s[i]-1, X_s[i]+p_a_s
            else: q_s[i+1], X_s[i+1] = q_s[i], X_s[i]
            if rnd[3] < lamb_b_s * dt: q_s[i+1], X_s[i+1] = q_s[i+1]+1, X_s[i+1]-p_b_s
            
            S[i+1] = S[i] + np.random.choice([1, -1]) * sigma * np.sqrt(dt)

        inv_pnl_all.append(X_i + q_i * S)
        sym_pnl_all.append(X_s + q_s * S)
        inv_q_all.append(q_i[-1]); sym_q_all.append(q_s[-1])
        
    return {
        "inv_pnls": np.array(inv_pnl_all), "sym_pnls": np.array(sym_pnl_all),
        "inv_q": np.array(inv_q_all), "sym_q": np.array(sym_q_all),
        "sample_S": S, "sample_q_inv": q_i, "sample_q_sym": q_s, 
        "sample_pnl_inv": inv_pnl_all[-1], "sample_pnl_sym": sym_pnl_all[-1],
        "sample_t": time_grid
    }

def get_metrics(pnl, final_q):
    return {
        "Profit": pnl[:,-1].mean(), "Risk": pnl[:,-1].std(), 
        "Sharpe": pnl[:,-1].mean()/pnl[:,-1].std() if pnl[:,-1].std() > 0 else 0, 
        "Inv_Vol": final_q.std()
    }

# --- 2. Sidebars ---
st.sidebar.header("Agent & Market Config")
gamma = st.sidebar.slider("Risk Aversion (γ)", 0.01, 0.5, 0.1)
sigma = st.sidebar.slider("Volatility (σ)", 0.5, 4.0, 2.0)
A = st.sidebar.slider("Liquidity Intensity (A)", 50, 300, 140)
k = st.sidebar.slider("Price Decay (k)", 0.5, 3.0, 1.5)
st.sidebar.subheader("Order Imbalance")
ask_m = st.sidebar.slider("Buyer Pressure", 0.5, 2.0, 1.0)
bid_m = st.sidebar.slider("Seller Pressure", 0.5, 2.0, 1.0)
n_sims = st.sidebar.selectbox("Simulations", [50, 100, 200], index=1)

# Check if parameters have changed since last graph generation
curr_params = (gamma, sigma, A, k, ask_m, bid_m, n_sims)
if st.session_state.sweep_params is not None and st.session_state.sweep_params != curr_params:
    st.session_state.sweep_fig = None
if st.session_state.heat_params is not None and st.session_state.heat_params != curr_params:
    st.session_state.heat_fig = None

# Execute Main Data
data = run_simulation(gamma, sigma, A, k, ask_m, bid_m, n_sims=n_sims)
m_i = get_metrics(data["inv_pnls"], data["inv_q"])
m_s = get_metrics(data["sym_pnls"], data["sym_q"])

# --- 3. Dashboard Header & Overview ---
st.title("Market Making Strategy Performance")

# Using a raw string (r"") so LaTeX backslashes aren't parsed as Python escape characters
st.markdown(r"""
This dashboard replicates the core findings of the seminal 2006 paper **"High-frequency trading in a limit order book"** by Marco Avellaneda and Sasha Stoikov. 

In their seminal 2006 paper, Avellaneda and Stoikov tackle the critical problem of Inventory Risk—the danger that a market maker accumulates a massive, unintended position just as the market moves against them. While "naive" strategies quote symmetrically around the market mid-price, they often fall victim to "inventory random walks," leading to high P&L variance and potential ruin during directional price shocks.
            
To solve this, the authors developed a stochastic control framework that replaces the market mid-price with a subjective Indifference Price. This price acts as a "fair value" that automatically adjusts based on the dealer's current holdings and risk aversion. By centering their bid-ask spread around this shifted price rather than the market mid-point, dealers can automatically incentivize trades that reduce their risk—effectively "leaning" into the order book to maintain a neutral position while still capturing the spread.         
            
### The Mathematical Engine
The inventory-aware agent seeks to maximize the expected exponential utility of their terminal wealth. The objective function is defined as:

$$ u(s,x,q,t) = \max_{\delta^a,\delta^b} E_t[-\exp(-\gamma(X_T+q_TS_T))] $$

Solving this via dynamic programming yields a two-step optimal quoting strategy:

1. **The Indifference Price ($r$)**: The dealer computes a subjective "fair value" based on their current inventory ($q$). If they hold too much stock, this price drops to encourage selling.

$$ r(s,q,t) = s - q\gamma\sigma^2(T-t) $$

2. **The Optimal Spread ($\delta^a + \delta^b$)**: The dealer centers a fixed spread around the indifference price. The spread width balances inventory risk against the likelihood of orders arriving.

$$ \delta^a + \delta^b = \gamma\sigma^2(T-t) + \frac{2}{\gamma}\ln\left(1 + \frac{\gamma}{k}\right) $$

**The Symmetric Strategy (The Benchmark):**
Unlike the inventory-aware agent, the naive symmetric dealer ignores their accumulated inventory ($q=0$). They calculate the exact same optimal spread, but anchor it directly to the market **mid-price** ($s$) rather than the shifted indifference price ($r$). While this symmetric approach frequently captures the spread, it exposes the dealer to "inventory random walks"—meaning they can accidentally accumulate massive, risky positions right as the market crashes, leading to high P&L variance.

**Understanding the Parameters:**
| Parameter | Meaning | Impact on Quotes |
| :--- | :--- | :--- |
| **$\gamma$ (Risk Aversion)** | How much you fear inventory. | Higher = Wider spreads and more aggressive price shifts. |
| **$\sigma$ (Volatility)** | Market risk/uncertainty. | Higher = Wider spreads to compensate for inventory risk. |
| **$A$ (Intensity)** | Baseline order arrival rate. | Higher = More frequent trades (higher liquidity). |
| **$k$ (Price Decay)** | Liquidity depth. | Higher = Thinner markets; requires tighter spreads to get filled. |
""")

st.subheader("Inventory-Aware vs. Symmetric Benchmark")

# --- Theme-Aware Metrics Table ---
metrics_list = [
    ("Mean Profit", "Profit", "higher"),
    ("Profit Volatility (Risk)", "Risk", "lower"),
    ("Sharpe Ratio", "Sharpe", "higher"),
    ("Inventory Variance", "Inv_Vol", "lower")
]

# Using RGBA for transparent backgrounds that adapt to Dark/Light mode
border_color = "rgba(128, 128, 128, 0.3)"
header_bg = "rgba(128, 128, 128, 0.1)"

rows = []
for label, key, goal in metrics_list:
    v_i, v_s = m_i[key], m_s[key]
    diff = v_i - v_s
    is_i_better = (diff > 0 if goal == "higher" else diff < 0)
    
    # Vibrant green for better metrics, readable on black or white
    color_i = "#2ecc71" if is_i_better else "inherit"
    weight_i = "bold" if is_i_better else "normal"
    color_s = "#2ecc71" if not is_i_better else "inherit"
    weight_s = "bold" if not is_i_better else "normal"
    symb = "+" if diff > 0 else ""
    
    row_html = f"""<tr>
<td style='padding:10px; border-bottom:1px solid {border_color};'><b>{label}</b></td>
<td style='padding:10px; border-bottom:1px solid {border_color}; color:{color_i}; font-weight:{weight_i};'>{v_i:.2f}</td>
<td style='padding:10px; border-bottom:1px solid {border_color}; color:{color_s}; font-weight:{weight_s};'>{v_s:.2f}</td>
<td style='padding:10px; border-bottom:1px solid {border_color};'>{symb}{diff:.2f}</td>
</tr>"""
    rows.append(row_html)

# Flush the main table HTML to the left as well
table_html = f"""<table style='width:100%; border-collapse: collapse; text-align: left; margin-bottom: 25px;'>
<thead>
<tr style='background-color: {header_bg};'>
<th style='padding:10px; border-bottom:2px solid {border_color};'>Metric</th>
<th style='padding:10px; border-bottom:2px solid {border_color};'>Inventory Strategy</th>
<th style='padding:10px; border-bottom:2px solid {border_color};'>Symmetric Strategy</th>
<th style='padding:10px; border-bottom:2px solid {border_color};'>Difference</th>
</tr>
</thead>
<tbody>{''.join(rows)}</tbody>
</table>"""

st.markdown(table_html, unsafe_allow_html=True)

# --- Updated Charts (Transparent Backgrounds) ---
c1, c2 = st.columns(2)

with c1:
    fig_q = go.Figure()
    fig_q.add_trace(go.Scatter(x=data["sample_t"], y=data["sample_q_inv"], name="Inventory", line=dict(color='#e74c3c')))
    fig_q.add_trace(go.Scatter(x=data["sample_t"], y=data["sample_q_sym"], name="Symmetric", line=dict(color='#3498db', dash='dot')))
    fig_q.update_layout(
        title="Inventory Control (Single Path)", 
        yaxis_title="Quantity (q)",
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_q, use_container_width=True, theme="streamlit")

    fig_dist = go.Figure()
    fig_dist.add_trace(go.Histogram(x=data["inv_pnls"][:,-1], name="Inventory", marker_color='#e74c3c', opacity=0.7))
    fig_dist.add_trace(go.Histogram(x=data["sym_pnls"][:,-1], name="Symmetric", marker_color='#3498db', opacity=0.3))
    fig_dist.update_layout(
        barmode='overlay', 
        title="P&L Distributions", 
        xaxis_title="Profit ($)",
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_dist, use_container_width=True, theme="streamlit")

with c2:
    fig_pnl = go.Figure()
    fig_pnl.add_trace(go.Scatter(x=data["sample_t"], y=data["sample_pnl_inv"], name="Inventory", line=dict(color='#e74c3c')))
    fig_pnl.add_trace(go.Scatter(x=data["sample_t"], y=data["sample_pnl_sym"], name="Symmetric", line=dict(color='#3498db', dash='dot')))
    fig_pnl.update_layout(
        title="Cumulative P&L Path", 
        yaxis_title="P&L ($)",
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_pnl, use_container_width=True, theme="streamlit")

# --- 5. Sensitivity Analysis Section ---
st.divider()
st.title("Parameter Sensitivity Analysis")

tab_sweep, tab_heat = st.tabs(["1D Parameter Sweep", "2D Heatmap (Gamma vs. Volatility)"])

with tab_sweep:
    st.markdown("### Risk Aversion (γ) Sweep")
    run_sweep = st.button("Run Gamma Sweep")
    
    if st.session_state.sweep_params is None or run_sweep:
        with st.spinner("Running sweep..."):
            gamma_range = np.linspace(0.01, 1.0, 20)
            sweep_inv_sharpe = []
            sweep_sym_sharpe = []
            
            for g in gamma_range:
                res = run_simulation(g, sigma, A, k, ask_m, bid_m, n_sims=100)
                inv_pnl = res["inv_pnls"][:,-1]
                sym_pnl = res["sym_pnls"][:,-1]
                sweep_inv_sharpe.append(inv_pnl.mean() / inv_pnl.std() if inv_pnl.std() > 0 else 0)
                sweep_sym_sharpe.append(sym_pnl.mean() / sym_pnl.std() if sym_pnl.std() > 0 else 0)
                
            fig_sweep = go.Figure()
            # Vibrant Red
            fig_sweep.add_trace(go.Scatter(x=gamma_range, y=sweep_inv_sharpe, mode='lines+markers', name='Inventory Strategy', line=dict(color='#e74c3c')))
            # Vibrant Blue (Replaces Navy)
            fig_sweep.add_trace(go.Scatter(x=gamma_range, y=sweep_sym_sharpe, mode='lines+markers', name='Symmetric Strategy', line=dict(color='#3498db', dash='dot')))
            
            fig_sweep.update_layout(
                title="Sharpe Ratio vs. Risk Aversion (γ)", 
                xaxis_title="Risk Aversion (γ)", 
                yaxis_title="Sharpe Ratio", 
                hovermode="x unified",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.session_state.sweep_fig = fig_sweep
            st.session_state.sweep_params = curr_params

    if st.session_state.sweep_fig:
        st.plotly_chart(st.session_state.sweep_fig, use_container_width=True, theme="streamlit")
        st.info("""
        **Interpreting the Gamma Sweep:**
        As the dealer becomes more risk-averse (higher $\gamma$), the Sharpe Ratio of the Inventory Strategy typically climbs before plateauing or slowly decaying. 
        - **Initial Rise:** The dealer stops acting like a naive algorithm and actively manages inventory, drastically dropping variance.
        - **The Plateau/Decay:** If $\gamma$ becomes too high, the dealer becomes "paranoid." They widen their spread so far that they barely execute any trades, which chokes off their profit generation and subsequently lowers the Sharpe Ratio. 
        """)
    else:
        st.warning("Sidebar parameters were updated. Click 'Run Gamma Sweep' to recalculate the chart.")

with tab_heat:
    st.markdown("### The 'Goldilocks' Zone")
    run_heat = st.button("Generate Heatmap")
    
    # Auto-run if first boot, OR if button is clicked
    if st.session_state.heat_params is None or run_heat:
        with st.spinner("Running grid simulations (this takes a few seconds)..."):
            g_grid = np.linspace(0.05, 1.0, 12)
            s_grid = np.linspace(0.5, 4.0, 6)
            heat_z = np.zeros((len(g_grid), len(s_grid)))
            
            for i, g in enumerate(g_grid):
                for j, s in enumerate(s_grid):
                    res = run_simulation(g, s, A, k, ask_m, bid_m, n_sims=50) 
                    inv_pnl = res["inv_pnls"][:,-1]
                    heat_z[i, j] = inv_pnl.mean() / inv_pnl.std() if inv_pnl.std() > 0 else 0
                    
            fig_heat = px.imshow(heat_z, x=s_grid, y=g_grid, labels=dict(x="Volatility (σ)", y="Risk Aversion (γ)", color="Sharpe"), title="Inventory Strategy Sharpe Ratio Heatmap", color_continuous_scale="Viridis", aspect="auto")
            
            st.session_state.heat_fig = fig_heat
            st.session_state.heat_params = curr_params

    # Render figure or show warning
    if st.session_state.heat_fig:
        st.plotly_chart(st.session_state.heat_fig, use_container_width=True)
        st.info("""
        **Interpreting the Heatmap:**
        This map reveals the interaction between market chaos (Volatility) and dealer psychology (Risk Aversion).
        - **Low Volatility (Left Side):** Inventory risk is minimal. Being highly risk-averse here actually hurts performance, because you sacrifice spread capture for a danger that doesn't exist.
        - **High Volatility (Right Side):** Inventory risk is lethal. The dealer *must* have a higher $\gamma$ to aggressively shed stock and survive the price swings. Finding the brightest yellow square allows quants to dynamically tune their algorithms to prevailing market conditions.
        """)
    else:
        st.warning("Sidebar parameters were updated. Click 'Generate Heatmap' to recalculate the chart.")