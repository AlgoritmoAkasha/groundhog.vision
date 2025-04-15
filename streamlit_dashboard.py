import streamlit as st
import subprocess
import time
import os
import requests
from datetime import datetime
import signal
import sys

# Page configuration
st.set_page_config(page_title="Trading Dashboard", layout="wide")

# Path to your original app.py
APP_PATH = os.path.join(os.path.dirname(__file__), "app.py")

# Web server details
WEB_SERVER_URL = "http://192.168.0.73:5000/"
app_process = None

def start_app_server():
    """Start the original app.py web server"""
    try:
        st.info("Starting web server... please wait")
        # Start the process and return it so we can control it later
        process = subprocess.Popen([sys.executable, APP_PATH], 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        
        # Wait a bit to make sure the server starts
        time.sleep(5)
        
        # Check if the server is running
        try:
            response = requests.get(WEB_SERVER_URL, timeout=5)
            if response.status_code == 200:
                st.success("Web server started successfully!")
                return process
            else:
                st.error(f"Server started but returned status code {response.status_code}")
                return None
        except requests.exceptions.RequestException:
            st.error("Could not connect to web server. It may not have started correctly.")
            process.terminate()
            return None
            
    except Exception as e:
        st.error(f"Error starting app.py: {e}")
        return None

def stop_app_server(process):
    """Stop the web server process"""
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        st.info("Web server stopped")

def check_server_running():
    """Check if the web server is already running"""
    try:
        response = requests.get(WEB_SERVER_URL, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def main():
    st.title("Trading Dashboard")
    
    # Check if server is running
    server_running = check_server_running()
    
    # Server status display
    if server_running:
        st.success("✅ Web server is running")
    else:
        st.warning("⚠️ Web server is not running")
    
    # Add control buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if not server_running:
            if st.button("Start Server"):
                global app_process
                app_process = start_app_server()
                if app_process:
                    st.rerun()  # Reload the page to show the iframe
    
    with col3:
        if server_running:
            if st.button("Restart Server"):
                # We don't have direct access to the existing process if it was started outside
                # this Streamlit session, so we'll try to kill any existing process by port
                if app_process:
                    stop_app_server(app_process)
                
                # Try to kill any other instance on port 5000
                try:
                    if os.name == 'nt':  # Windows
                        subprocess.run(["taskkill", "/f", "/im", "python.exe"], 
                                      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                    else:  # Linux/Mac
                        subprocess.run(["pkill", "-f", APP_PATH],
                                      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                except:
                    pass
                
                # Start a new server
                app_process = start_app_server()
                if app_process:
                    st.rerun()
    
    with col1:
        # Show auto-refresh info
        current_time = datetime.now()
        next_refresh = current_time.replace(minute=0 if current_time.minute >= 30 else 30, second=0, microsecond=0)
        if current_time.minute >= 30:
            next_refresh = next_refresh.replace(hour=current_time.hour + 1)
        
        st.write(f"Next auto-refresh: {next_refresh.strftime('%H:%M')}")
    
    # Display the web app in an iframe if it's running
    if server_running:
        # Use HTML to create an iframe that takes up most of the page
        st.components.v1.html(
            f"""
            <iframe src="{WEB_SERVER_URL}" width="100%" height="800" style="border: none;"></iframe>
            """,
            height=820,
        )
    else:
        st.info("Click 'Start Server' to view the dashboard")

# App entry point
if __name__ == "__main__":
    main()
    
    # Clean up when Streamlit script stops
    if app_process:
        stop_app_server(app_process)
