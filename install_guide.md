# Marine Seguros Analytics - Installation Guide

## Requirements
- Python 3.8 or higher
- 4GB RAM minimum
- Modern web browser

## Installation Steps

1. **Install Python**
   - Download from https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation

2. **Extract the Application**
   - Unzip the provided marine-seguros.zip file
   - Open Terminal/Command Prompt in that folder

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Key**
   - Get your Gemini API key from https://makersuite.google.com/app/apikey
   - Create a `.env` file and add:
     ```
     GEMINI_API_KEY=your_key_here
     ```

5. **Run the Application**
   ```bash
   streamlit run app_enhanced_v2.py
   ```

6. **Access the Application**
   - Open your browser to http://localhost:8501
   - The app runs locally - your data never leaves your computer

## Security Notes
- All data processing happens on your local machine
- Only the AI questions are sent to Google (not your financial data)
- Close the terminal window to stop the application

## Troubleshooting
- If you see "command not found", try: `python -m streamlit run app_enhanced_v2.py`
- On Mac, you might need to use `python3` instead of `python`
- Contact support if you encounter any issues