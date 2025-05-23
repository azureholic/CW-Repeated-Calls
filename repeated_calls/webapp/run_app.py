"""
Script to run the Repeated Calls Streamlit Web Application
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run the Streamlit application."""
    app_path = Path(__file__).parent / "app.py"
    
    try:
        print("🚀 Starting Repeated Calls Web Application...")
        print(f"📍 App location: {app_path}")
        print("🌐 The app will open in your default web browser")
        print("🛑 Press Ctrl+C to stop the application\n")
        
        # Run streamlit with the app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--theme.base", "light"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {str(e)}")

if __name__ == "__main__":
    main()
