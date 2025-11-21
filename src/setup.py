import subprocess
import sys
import os

def install_requirements():
    print("Installing requirements...")
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("Requirements installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)

def run_db_setup():
    print("Setting up database...")
    try:
        # Import database_setup dynamically or run it as a subprocess
        # Running as subprocess to ensure clean state and path handling
        db_setup_path = os.path.join(os.path.dirname(__file__), "database_setup.py")
        subprocess.check_call([sys.executable, db_setup_path])
        print("Database setup completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we are in the src directory context
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("Starting Robot Vacuum Depot Setup...")
    install_requirements()
    run_db_setup()
    print("\nSetup complete! You can now run the application with:")
    print("streamlit run app.py")
