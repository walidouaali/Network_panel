# 🚀 Network Pro Dashboard (iPerf3 & Ping)

A modern, real-time network diagnostic dashboard built with Streamlit. This tool allows you to analyze network throughput (via iPerf3) and latency (via Ping) with professional visualizations.

## ✨ Features

- **Dual Mode Analysis**: Switch between Throughput (iPerf3) and Latency (Ping) analysis.
- **Real-Time Visualization**: Interactive Plotly charts with points, lines, and average markers.
- **Advanced Statistics**: Real-time calculation of Average, Peak, and Jitter (Standard Deviation).
- **Stability Analysis**: Shaded area on charts representing the Standard Deviation for quick stability assessment.
- **Live Terminal**: Integrated terminal output to monitor raw command execution.
- **History Management**: Automatically saves logs and allows for graphical re-analysis of previous tests.
- **Optimized UI**: High-visibility configuration panel and professional branding.

## 🛠 Prerequisites

Ensure you have the following installed on your system:

- **Python 3.8+**
- **iPerf3**: `sudo apt install iperf3` (Linux) or download from [iperf.fr](https://iperf.fr/iperf-download.php)
- **Ping**: Usually pre-installed on most systems.

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd network-pro-dashboard
   ```

2. **Install Python dependencies**:
   ```bash
   pip install streamlit pandas numpy plotly pillow
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## 📂 Project Structure

- `app.py`: The main Streamlit application.
- `logos/`: Directory containing institutional logos.
- `iperf_logs/`: Directory where iPerf3 test results are saved.
- `ping_logs/`: Directory where Ping test results are saved.

## 📝 License

This project is open-source. Feel free to modify and adapt it to your needs.
