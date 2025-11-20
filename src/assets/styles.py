CUSTOM_CSS = """
<style>
    /* Main container adjustments */
    .reportview-container {
        margin-top: -2em;
    }
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #stDecoration {display:none;}

    /* Make the main content start below the fixed header */
    .block-container {
        padding-top: 6rem !important;
        padding-bottom: 5rem !important;
    }

    /* Fixed header bar */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(h1) {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999 !important;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px) !important;
        padding: 1rem 2rem !important;
        border-bottom: 1px solid rgba(49, 51, 63, 0.1) !important;
    }

    /* Dark mode support for header */
    @media (prefers-color-scheme: dark) {
        div[data-testid="stVerticalBlockBorderWrapper"]:has(h1) {
            background: rgba(14, 17, 23, 0.95) !important;
            border-bottom: 1px solid rgba(250, 250, 250, 0.1) !important;
        }
    }

    /* Streamlit dark theme overrides */
    .stApp[data-theme="dark"] div[data-testid="stVerticalBlockBorderWrapper"]:has(h1) {
        background: rgba(14, 17, 23, 0.95) !important;
    }

    /* Card styling for metrics and results */
    div[data-testid="stMetric"], div[data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
        border: 1px solid rgba(128, 128, 128, 0.1);
    }

    /* Chat input styling */
    .stChatInputContainer {
        padding-bottom: 20px;
    }
    
    /* Custom button styling */
    button[kind="primary"] {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        border: none;
        transition: all 0.3s ease;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
"""
