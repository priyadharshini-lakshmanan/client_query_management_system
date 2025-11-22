# Client Query Management System

A simple web app for managing client support queries. Built this to help small teams handle customer queries without needing complex querying systems.

## What it does

**For Clients:**
- Submit support queries through a simple form
- Get a unique query ID for tracking
- Choose from common issue categories

**For Support Team:**
- See all queries in one place
- Filter by status or category
- Close query when resolved

## Setup

You'll need Python and MySQL installed.

```bash
# Install dependencies
pip install streamlit mysql-connector-python pandas

# Create database
mysql -u root -p
CREATE DATABASE client_query;

# Update credentials in the code (line 8-13)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "client_query"
}

# Run the app
streamlit run app.py
```

The app will create tables automatically on first run.

## How to use

1. Open http://localhost:8501 in your browser
2. Register as either 'client' or 'support' role
3. Login and start using

**Client side:** Fill the form, pick a category, describe your issue, and submit.

**Support side:** View the dashboard, filter tickets, and close them when done.

## Query categories

Bug Report, Account Suspension, Data Export, UI Feedback, Technical Support, Billing Problem, Payment Failure, Feature Request, Subscription Cancellation, Login Issue

## Notes

- User data gets saved to both MySQL and a CSV file (login.csv)
- Query IDs auto-increment (Q0001, Q0002, etc.)
