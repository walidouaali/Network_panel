import streamlit as st
import subprocess
import os
import json
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from datetime import datetime
from PIL import Image

# Page Configuration
st.set_page_config(page_title="Network Pro Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* Force increase font size for ALL labels in the config section */
    div[data-testid="stWidgetLabel"] p {
        font-size: 22px !important;
        font-weight: bold !important;
        color: #ffffff !important;
    }
    
    /* Increase font size for the input text itself */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        font-size: 18px !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3.5em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
        font-size: 1.1rem !important;
    }
    
    .terminal-box {
        background-color: #000000;
        color: #00ff00;
        font-family: 'Courier New', Courier, monospace;
        padding: 10px;
        border-radius: 5px;
        height: 450px;
        overflow-y: auto;
        font-size: 12px;
        border: 1px solid #333;
        white-space: pre-wrap;
    }
    
    /* Logo container styling */
    .logo-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding: 20px 0;
        background-color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 🔹 Logos Header
logo_dir = "/home/ubuntu/iperf_dashboard/logos"
logos = ["imt.png", "LogoIMTfor5GFondTransparent.png", "FR2030.png", "Banque.png"]

col_logos = st.columns(len(logos))
for i, logo_name in enumerate(logos):
    logo_path = os.path.join(logo_dir, logo_name)
    if os.path.exists(logo_path):
        with col_logos[i]:
            st.image(logo_path, use_container_width=True)

st.divider()

# 🔹 Navigation Header
st.title("🚀 Network Pro Control Panel")
mode_selection = st.radio("Select Analysis Mode", ["📈 Throughput Analysis", "⏱ Latency Analysis"], horizontal=True)

# 🔹 Log Directories
IPERF_LOG_DIR = "iperf_logs"
PING_LOG_DIR = "ping_logs"
os.makedirs(IPERF_LOG_DIR, exist_ok=True)
os.makedirs(PING_LOG_DIR, exist_ok=True)

# Helper Functions
def parse_iperf_line(line):
    if "bits/sec" in line and "sender" not in line and "receiver" not in line:
        parts = line.split()
        try:
            idx = -1
            for i, p in enumerate(parts):
                if "bits/sec" in p:
                    idx = i - 1
                    unit = p
                    break
            if idx != -1:
                val = float(parts[idx])
                if "Gbits" in unit: val *= 1000
                elif "Kbits" in unit: val /= 1000
                return val
        except:
            pass
    return None

def parse_ping_line(line):
    match = re.search(r"time=([\d\.]+)\s*ms", line)
    if match:
        return float(match.group(1))
    return None

def create_advanced_chart(df, y_col, y_label, title):
    if df.empty:
        return go.Figure()
    
    avg_val = df[y_col].mean()
    std_val = df[y_col].std()
    if pd.isna(std_val): std_val = 0
    
    fig = go.Figure()
    
    # Standard Deviation Shaded Area
    fig.add_trace(go.Scatter(
        x=pd.concat([df['Time'], df['Time'][::-1]]),
        y=pd.concat([pd.Series([avg_val + std_val] * len(df)), pd.Series([avg_val - std_val] * len(df))[::-1]]),
        fill='toself',
        fillcolor='rgba(0, 255, 255, 0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=True,
        name=f'Std Dev (±{std_val:.2f})'
    ))
    
    # Main Line with Points
    fig.add_trace(go.Scatter(
        x=df['Time'], y=df[y_col],
        mode='lines+markers',
        name=y_label,
        line=dict(color='#ff4b4b', width=2),
        marker=dict(size=6, symbol='circle'),
        hovertemplate=f'Time: %{{x:.1f}}s<br>{y_label}: %{{y:.2f}} {y_label.split()[-1]}<extra></extra>'
    ))
    
    # Average Line
    fig.add_trace(go.Scatter(
        x=[df['Time'].min(), df['Time'].max()],
        y=[avg_val, avg_val],
        mode='lines',
        name='Average',
        line=dict(color='cyan', width=2, dash='dash'),
        hovertemplate=f'Average: %{{y:.2f}} {y_label.split()[-1]}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time (seconds)",
        yaxis_title=y_label,
        template="plotly_dark",
        height=450,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# ---------------------------------------------------------
# 📈 THROUGHPUT MODE
# ---------------------------------------------------------
if mode_selection == "📈 Throughput Analysis":
    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 0.8, 0.8, 1, 1.2, 1])
    with col1: ip = st.text_input("📡 Target IP", "192.168.100.2", key="iperf_ip")
    with col2: duration = st.number_input("⏱ Duration (s)", min_value=1, value=10, key="iperf_dur")
    with col3: protocol = st.selectbox("🔌 Protocol", ["TCP", "UDP"], key="iperf_proto")
    with col4: direction = st.selectbox("🔁 Mode", ["Downlink (DL)", "Uplink (UL)"], key="iperf_dir")
    with col5:
        use_bw = st.checkbox("Set Bandwidth", key="iperf_use_bw")
        bw_val = st.number_input("Mbps", min_value=1, value=30, disabled=not use_bw, key="iperf_bw")
    with col6:
        st.write(" ")
        run_btn = st.button("▶ RUN IPERF3")

    st.divider()
    main_col1, main_col2 = st.columns([2, 1])
    with main_col1:
        st.subheader("📈 Throughput Analysis (Mbps)")
        chart_placeholder = st.empty()
        metrics_placeholder = st.empty()
    with main_col2:
        st.subheader("💻 Terminal Output")
        terminal_placeholder = st.empty()

    if 'iperf_history' not in st.session_state:
        st.session_state.iperf_history = pd.DataFrame(columns=['Time', 'Mbps'])

    if run_btn:
        st.session_state.iperf_history = pd.DataFrame(columns=['Time', 'Mbps'])
        cmd = ["iperf3", "-c", ip, "-t", str(duration), "-i", "0.5", "--forceflush"]
        if protocol == "UDP": cmd.append("-u")
        if use_bw: cmd.extend(["-b", f"{bw_val}M"])
        elif protocol == "UDP": cmd.extend(["-b", "1000M"])
        if "Uplink" in direction: cmd.append("-R")

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        terminal_content = ""
        start_time = time.time()
        try:
            for line in process.stdout:
                terminal_content += line
                terminal_placeholder.markdown(f'<div class="terminal-box">{terminal_content}</div>', unsafe_allow_html=True)
                val = parse_iperf_line(line)
                if val is not None:
                    elapsed = time.time() - start_time
                    new_row = pd.DataFrame({'Time': [elapsed], 'Mbps': [val]})
                    st.session_state.iperf_history = pd.concat([st.session_state.iperf_history, new_row], ignore_index=True)
                    fig = create_advanced_chart(st.session_state.iperf_history, 'Mbps', 'Throughput (Mbps)', "Real-Time Throughput")
                    chart_placeholder.plotly_chart(fig, use_container_width=True)
                    with metrics_placeholder.container():
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Current", f"{val:.2f} Mbps")
                        m2.metric("Average", f"{st.session_state.iperf_history['Mbps'].mean():.2f} Mbps")
                        m3.metric("Std Dev", f"{st.session_state.iperf_history['Mbps'].std():.2f} Mbps")
                time.sleep(0.01)
            process.wait()
            st.success("✅ iPerf3 Test Completed")
            log_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"{IPERF_LOG_DIR}/log_{log_id}.txt", "w") as f: f.write(terminal_content)
        except Exception as e:
            st.error(f"Error: {e}")
            if process: process.kill()

    # History
    st.divider()
    with st.expander("📂 iPerf3 History"):
        files = sorted(os.listdir(IPERF_LOG_DIR), reverse=True)
        if files:
            selected_log = st.selectbox("Select log", files, key="iperf_hist_sel")
            with open(os.path.join(IPERF_LOG_DIR, selected_log), "r") as f: content = f.read()
            hist_data = [parse_iperf_line(l) for l in content.split('\n') if parse_iperf_line(l) is not None]
            if hist_data:
                df_h = pd.DataFrame({'Time': [i*0.5 for i in range(len(hist_data))], 'Mbps': hist_data})
                h1, h2 = st.columns([2, 1])
                with h1: st.plotly_chart(create_advanced_chart(df_h, 'Mbps', 'Throughput (Mbps)', f"Analysis: {selected_log}"), use_container_width=True)
                with h2:
                    st.metric("Peak", f"{max(hist_data):.2f} Mbps")
                    st.metric("Average", f"{df_h['Mbps'].mean():.2f} Mbps")
                    st.metric("Std Dev", f"{df_h['Mbps'].std():.2f} Mbps")
            st.text_area("Raw Log", content, height=200)

# ---------------------------------------------------------
# ⏱ LATENCY MODE
# ---------------------------------------------------------
else:
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1: ping_ip = st.text_input("📡 Target IP", "8.8.8.8", key="ping_ip")
    with col2: ping_count = st.number_input("🔢 Count", min_value=1, value=20, key="ping_count")
    with col3: ping_interval = st.number_input("⏱ Interval (s)", min_value=0.2, value=0.5, step=0.1, key="ping_int")
    with col4:
        st.write(" ")
        run_ping_btn = st.button("▶ RUN PING")

    st.divider()
    main_col1, main_col2 = st.columns([2, 1])
    with main_col1:
        st.subheader("📈 Latency Analysis (ms)")
        chart_placeholder = st.empty()
        metrics_placeholder = st.empty()
    with main_col2:
        st.subheader("💻 Terminal Output")
        terminal_placeholder = st.empty()

    if 'ping_history' not in st.session_state:
        st.session_state.ping_history = pd.DataFrame(columns=['Time', 'ms'])

    if run_ping_btn:
        st.session_state.ping_history = pd.DataFrame(columns=['Time', 'ms'])
        cmd = ["ping", "-c", str(ping_count), "-i", str(ping_interval), ping_ip]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        terminal_content = ""
        start_time = time.time()
        try:
            for line in process.stdout:
                terminal_content += line
                terminal_placeholder.markdown(f'<div class="terminal-box">{terminal_content}</div>', unsafe_allow_html=True)
                val = parse_ping_line(line)
                if val is not None:
                    elapsed = time.time() - start_time
                    new_row = pd.DataFrame({'Time': [elapsed], 'ms': [val]})
                    st.session_state.ping_history = pd.concat([st.session_state.ping_history, new_row], ignore_index=True)
                    fig = create_advanced_chart(st.session_state.ping_history, 'ms', 'Latency (ms)', "Real-Time Latency")
                    chart_placeholder.plotly_chart(fig, use_container_width=True)
                    with metrics_placeholder.container():
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Current", f"{val:.2f} ms")
                        m2.metric("Average", f"{st.session_state.ping_history['ms'].mean():.2f} ms")
                        m3.metric("Jitter (Std Dev)", f"{st.session_state.ping_history['ms'].std():.2f} ms")
                time.sleep(0.01)
            process.wait()
            st.success("✅ Ping Test Completed")
            log_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"{PING_LOG_DIR}/log_{log_id}.txt", "w") as f: f.write(terminal_content)
        except Exception as e:
            st.error(f"Error: {e}")
            if process: process.kill()

    # History
    st.divider()
    with st.expander("📂 Ping History"):
        files = sorted(os.listdir(PING_LOG_DIR), reverse=True)
        if files:
            selected_log = st.selectbox("Select log", files, key="ping_hist_sel")
            with open(os.path.join(PING_LOG_DIR, selected_log), "r") as f: content = f.read()
            hist_data = [parse_ping_line(l) for l in content.split('\n') if parse_ping_line(l) is not None]
            if hist_data:
                df_h = pd.DataFrame({'Time': [i*ping_interval for i in range(len(hist_data))], 'ms': hist_data})
                h1, h2 = st.columns([2, 1])
                with h1: st.plotly_chart(create_advanced_chart(df_h, 'ms', 'Latency (ms)', f"Analysis: {selected_log}"), use_container_width=True)
                with h2:
                    st.metric("Min", f"{min(hist_data):.2f} ms")
                    st.metric("Average", f"{df_h['ms'].mean():.2f} ms")
                    st.metric("Max", f"{max(hist_data):.2f} ms")
            st.text_area("Raw Log", content, height=200)
