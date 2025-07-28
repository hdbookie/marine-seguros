# Marine Seguros - Financial Analytics Platform

A comprehensive financial analytics dashboard with AI-powered insights for Marine Seguros and financial services.
🚀 Features

📊 Interactive Dashboard: Dynamic visualizations of revenue, profit, and margins
🤖 AI Insights: Automated analysis using advanced language models
📈 Financial Forecasting: Projections and scenario analysis
📁 Excel Integration: Smart data extraction from various Excel formats
📥 Report Export: Generate PDF and Excel reports
🔐 Authentication: Secure user management system

🛠️ Technology Stack

Frontend: Streamlit
Backend: Python
AI Integration: Google Gemini API
Data Processing: Pandas, NumPy
Visualizations: Plotly
Authentication: JWT, bcrypt

📋 Setup Instructions
1. Clone the repository
bashgit clone <repository-url>
cd financial-analytics
2. Install dependencies
bashpip install -r requirements.txt
3. Configure environment variables
bashcp .env.example .env
# Add your API keys and configuration
4. Run the application
bashstreamlit run app_refactored.py
📊 Supported Data Formats
The platform supports various Excel formats commonly used in financial reporting:

Revenue and income statements
Cost analysis spreadsheets
Monthly/quarterly financial reports
Custom financial data structures

🔧 Configuration
Create a .env file with the following variables:
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET_KEY=your_jwt_secret_here
🚀 Deployment
Streamlit Cloud



Docker
bashdocker build -t financial-analytics .
docker run -p 8501:8501 financial-analytics
📈 Key Metrics Analyzed

Revenue and income trends
Cost analysis and margins
Operational expenses
Profit and loss statements
Growth rates and projections
Financial anomaly detection

🔒 Security Features

Secure authentication system
Environment-based configuration
Data privacy protection
Session management

🤖 AI Capabilities

Automated financial analysis
Trend detection and insights
Natural language reporting
Predictive analytics
Anomaly identification


📄 License
This project is licensed under the MIT License - see the LICENSE file for details

Desenvolvido com ❤️ para Marine Seguros
