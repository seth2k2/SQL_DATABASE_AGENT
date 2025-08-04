# SQL Database Assistant

A Streamlit-based application for interacting with SQL databases, developed by Seniru Epasinghe.
![Database Structure](database.png)
## Features

- Natural language to SQL query conversion
- Support for both Azure SQL Database and local SQLite
- Real-time database interaction
- GPT-powered query understanding

## Setup Instructions

### Prerequisites
- Python 3.7+
- Git (optional)

### Installation
1. Clone the repository:(bash)<br>
git clone [repository-url]
cd [repository-name]

2. Create and activate virtual environment:<br>
python -m venv venv<br><br>
On Windows: <br>
.\venv\Scripts\activate<br><br>
On macOS/Linux:<br>
source venv/bin/activate<br>

3. Install dependencies:<br>
pip install -r requirements.txt

### Running the Application
streamlit run streamlit_app.py

### Database Configuration
- Azure SQL Database
- Access via MSSQL Server
- Structure shown in database.png
#### Also can use local database using a file with .db extension
- Local SQLite Database
- Sample db File: classicmodels.db

### Database changes in Azure will reflect in real-time

### Local database provided for offline development

### Demo video is also provided for reference
