import streamlit as st
import numpy as np
import pandas as pd
import time
import altair as alt

# --- 1. Page Configuration ---
st.set_page_config(page_title="Dynamic Pricing Simulation", layout="wide")
st.title("Agent-Based Market Simulation")

# --- 2. Session State Initialization ---
# We use session state to remember the data between Streamlit re-runs
if 'initialized' not in st.session_state:
    st.session_state.N = 1000
    # Assign private WTP to 1000 consumers uniformly between 0 and 1
    st.session_state.wtp = np.random.uniform(0, 1, st.session_state.N)
    
    # Create grid coordinates for the 1000 agents (40 cols x 25 rows)
    x, y = np.meshgrid(np.arange(40), np.arange(25))
    st.session_state.agent_x = x.flatten()
    st.session_state.agent_y = y.flatten()

    # Initial Market State
    st.session_state.prices = [0.5]
    st.session_state.demands = [np.sum(st.session_state.wtp >= 0.5) / 1000]
    st.session_state.day = 0
    st.session_state.initialized = True

# --- 3. Sidebar Controls ---
st.sidebar.header("Bot Parameters")
r = st.sidebar.slider("Bot Aggression (r)", min_value=1.0, max_value=4.0, value=3.0, step=0.01)

st.sidebar.header("Simulation Controls")
days_to_run = st.sidebar.number_input("Days to advance", min_value=1, max_value=1000, value=50)
anim_speed = st.sidebar.slider("Animation Speed (seconds)", 0.0, 0.5, 0.05)

col1, col2 = st.sidebar.columns(2)
run_btn = col1.button("Run Simulation", type="primary")
reset_btn = col2.button("Reset System")

if reset_btn:
    # Clear the state to start over
    del st.session_state.initialized
    st.rerun()

# --- 4. Dashboard Layout ---
# We create empty placeholders that we will overwrite during the animation loop
col_agents, col_charts = st.columns([1, 1.5])

with col_agents:
    st.subheader(f"Consumer Market (1000 Agents)")
    agent_status_text = st.empty()
    agent_plot_placeholder = st.empty()

with col_charts:
    st.subheader("Price & Demand Over Time")
    chart_placeholder = st.empty()

# --- 5. Helper Function to Draw UI ---
def draw_ui():
    current_price = st.session_state.prices[-1]
    current_demand = st.session_state.demands[-1]
    
    # A. Draw Agent Grid (Using Altair for fast rendering)
    agent_status = ['Bought' if w >= current_price else 'Priced Out' for w in st.session_state.wtp]
    df_agents = pd.DataFrame({
        'x': st.session_state.agent_x,
        'y': st.session_state.agent_y,
        'Status': agent_status
    })
    
    agent_chart = alt.Chart(df_agents).mark_circle(size=50).encode(
        x=alt.X('x', axis=None),
        y=alt.Y('y', axis=None),
        color=alt.Color('Status', 
                        scale=alt.Scale(domain=['Bought', 'Priced Out'], 
                                        range=['#00ff00', '#444444']),
                        legend=None)
    ).properties(height=400).configure_view(strokeWidth=0)
    
    agent_status_text.caption(f"Day: **{st.session_state.day}** | Price: **{current_price:.3f}** | Demand: **{current_demand:.3f}**")
    agent_plot_placeholder.altair_chart(agent_chart, use_container_width=True)

    # B. Draw Time Series Chart
    df_chart = pd.DataFrame({
        'Price': st.session_state.prices,
        'Demand': st.session_state.demands
    })
    chart_placeholder.line_chart(df_chart, height=400, color=["#00d2ff", "#ff6b6b"])

# Draw the initial state before any loops
if not run_btn:
    draw_ui()

# --- 6. The Simulation Loop ---
if run_btn:
    for _ in range(days_to_run):
        current_price = st.session_state.prices[-1]
        current_demand = st.session_state.demands[-1]
        
        # Bot updates price: P(t+1) = r * P(t) * D(t)
        next_price = r * current_price * current_demand
        
        # Calculate new demand for the new price
        next_demand = np.sum(st.session_state.wtp >= next_price) / st.session_state.N
        
        # Save to state
        st.session_state.prices.append(next_price)
        st.session_state.demands.append(next_demand)
        st.session_state.day += 1
        
        # Render the updated state
        draw_ui()
        
        # Pause for animation effect
        if anim_speed > 0:
            time.sleep(anim_speed)