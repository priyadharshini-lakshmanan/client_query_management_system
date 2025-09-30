import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime
import os
import csv

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Localhost@123",
    "database": "client_query"
}

def create_database_and_tables():
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS client_query")
        cursor.execute("USE client_query")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login (
                username VARCHAR(255),
                password VARCHAR(255),
                role VARCHAR(255)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS synthetic_client_queries (
                query_id VARCHAR(20) PRIMARY KEY,
                client_email VARCHAR(255),
                client_mobile VARCHAR(20),
                query_heading VARCHAR(100),
                query_description TEXT,
                status VARCHAR(20),
                date_raised DATETIME,
                date_closed DATETIME
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        st.error(f"Database setup error: {e}")

def authenticate(username, password, role):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM login WHERE username=%s AND password=%s AND role=%s"
        cursor.execute(query, (username, password, role))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result and result[0] > 0
    except Error as e:
        st.error(f"Authentication error: {e}")
        return False

def register_user(username, password, role):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM login WHERE username=%s AND role=%s", (username, role))
        if cursor.fetchone()[0] > 0:
            cursor.close()
            conn.close()
            return False, "Username already exists for this role"
        
        cursor.execute("INSERT INTO login (username, password, role) VALUES (%s, %s, %s)", 
                      (username, password, role))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM login WHERE username=%s AND role=%s", (username, role))
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        if count > 0:
            save_to_csv(username, password, role)
            return True, f"Registration successful! User {username} added to database and CSV."
        else:
            return False, "Registration failed - user not found after insert"
            
    except Error as e:
        return False, f"Registration error: {e}"

def save_to_csv(username, password, role):
    """Save user data to login.csv file"""
    csv_file = 'login.csv'
    
    file_exists = os.path.isfile(csv_file)
    
    try:
        if file_exists:
            with open(csv_file, 'rb') as f:
                f.seek(-1, os.SEEK_END)
                last_char = f.read(1)
                needs_newline = last_char not in (b'\n', b'\r')
            
            if needs_newline:
                with open(csv_file, 'a', newline='', encoding='utf-8') as file:
                    file.write('\n')
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            if not file_exists:
                writer.writerow(['username', 'password', 'role'])
            
            writer.writerow([username, password, role])
            
    except Exception as e:
        st.error(f"Error saving to CSV: {e}")

def debug_show_all_users():
    """Debug function to show all users in the database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM login")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return users
    except Error as e:
        return f"Error: {e}"

def get_next_query_id():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT query_id FROM synthetic_client_queries ORDER BY query_id DESC LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and row[0].startswith("Q"):
            num = int(row[0][1:])
            return f"Q{num+1:04d}"
        return "Q0001"
    except Exception as e:
        st.error(f"Could not generate next query ID: {e}")
        return "Q0001"

def save_query(query_data):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO synthetic_client_queries
            (query_id, client_email, client_mobile, query_heading, query_description, status, date_raised, date_closed)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            query_data['query_id'],
            query_data['client_email'],
            query_data['client_mobile'],
            query_data['query_heading'],
            query_data['query_description'],
            query_data['status'],
            query_data['date_raised'],
            query_data['date_closed']
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as e:
        st.error(f"Error saving query: {e}")
        return False

def load_queries():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM synthetic_client_queries ORDER BY query_id")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading queries: {e}")
        return pd.DataFrame()

def close_query(query_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE synthetic_client_queries
            SET status='Closed', date_closed=%s
            WHERE query_id=%s
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), query_id))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Error closing query: {e}")

def logout():
    st.session_state.clear()
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except AttributeError:
            st.session_state.needs_rerun = True

def client_query_page():
    st.markdown("<h1 style='text-align: center;'>Submit Your Query</h1>", unsafe_allow_html=True)
 
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("query_form"):
            email = st.text_input("Your Email")
            mobile = st.text_input("Mobile Number")
            query_heading = st.radio(
                "Query Heading",
                ('Bug Report', 'Account Suspension', 'Data Export', 'UI Feedback',
                 'Technical Support', 'Billing Problem', 'Payment Failure',
                 'Feature Request', 'Subscription Cancellation', 'Login Issue'),
                horizontal=True
            )
            query_desc = st.text_area("Query Description", height=150)
            col_btn1, col_btn2 = st.columns([1,1])
            with col_btn1:
                submitted = st.form_submit_button("Submit", use_container_width=True)
            with col_btn2:
                logout_clicked = st.form_submit_button("Logout", use_container_width=True)

            if logout_clicked:
                logout()

            if submitted:
                if not query_desc.strip():
                    st.error("Please enter your query description before submitting.")
                else:
                    query_id = get_next_query_id()
                    query_data = {
                        "query_id": query_id,
                        "client_email": email,
                        "client_mobile": mobile,
                        "query_heading": query_heading,
                        "query_description": query_desc,
                        "status": "Opened",
                        "date_raised": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "date_closed": None
                    }
                    if save_query(query_data):
                        st.success(f"Query submitted successfully with ID: {query_id}")
                        with st.expander("Submission Details", expanded=True):
                            st.write(f"Query ID: {query_id}")
                            st.write(f"Email: {email}")
                            st.write(f"Mobile: {mobile}")
                            st.write(f"Status: Opened")
                            st.write(f"Created: {query_data['date_raised']}")
                            st.write(f"Query Type: {query_heading}")
                            st.write(f"Description: {query_desc}")

def support_portal_page():
    st.title("Support Team Portal")
    df = load_queries()

    if df.empty:
        st.info("No queries found.")
        return

    total_queries = len(df)
    opened_queries_count = (df['status'].str.lower() == 'opened').sum()
    closed_queries_count = (df['status'].str.lower() == 'closed').sum()

    col1, col2, col3 = st.columns(3)
    col1.metric(label="Total Queries", value=total_queries)
    col2.metric(label="Opened Queries", value=opened_queries_count)
    col3.metric(label="Closed Queries", value=closed_queries_count)

    status_filter = st.selectbox("Filter by Status", ["All", "Opened", "Closed"])
    category_filter = st.selectbox("Filter by Category", ['All','Bug Report', 'Account Suspension', 'Data Export', 'UI Feedback',
                                                        'Technical Support', 'Billing Problem', 'Payment Failure',
                                                        'Feature Request', 'Subscription Cancellation', 'Login Issue'])

    filtered_df = df.copy()
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    if category_filter != "All":
        filtered_df = filtered_df[filtered_df['query_heading'] == category_filter]

    if filtered_df.empty:
        st.info("No queries match the selected filters.")
        return
    
    row_height = 35
    header_height = 40
    max_table_height = 600
    calculated_height = min(len(filtered_df) * row_height + header_height, 600)

    st.subheader("Query Summary Table")
    st.dataframe(filtered_df[['query_id', 'date_raised', 'client_email', 'client_mobile', 'query_heading', 'status', 'date_closed']],
                 height=calculated_height)

   
    opened_queries = filtered_df[filtered_df['status'].str.lower() == 'opened']
    
    if opened_queries.empty:
        st.info("No opened queries found.")
    else:
        st.subheader(f"Opened Query Details ({len(opened_queries)})")
        for idx, row in opened_queries.iterrows():
            status_emoji = "🟢" 
            with st.expander(f"{status_emoji} {row['query_heading']} | {row['client_email']} | {row['date_raised']}"):
                st.write(f"**Email:** {row['client_email']}")
                st.write(f"**Mobile:** {row['client_mobile']}")
                st.write(f"**Created:** {row['date_raised']}")
                st.write(f"**Status:** {row['status']}")
                st.info(f"**Description:** {row['query_description']}")
                if st.button("Close Query", key=f"close_{row['query_id']}"):
                    close_query(row['query_id'])
                    st.success("Query closed successfully!")
                    try:
                        st.rerun()
                    except AttributeError:
                        try:
                            st.experimental_rerun()
                        except AttributeError:
                            st.session_state.needs_rerun = True

    if st.button("Logout"):
        logout()

def main():
    st.set_page_config(page_title="Client Query Management System", layout="wide")
    create_database_and_tables()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.show_register = False
    
    if st.session_state.get("needs_rerun", False):
        st.session_state.needs_rerun = False
        st.experimental_rerun() if hasattr(st, 'experimental_rerun') else None

    if not st.session_state.logged_in:
        if not st.session_state.get("show_register", False):
            st.markdown("<h1 style='text-align: center;'>Login Page</h1>", unsafe_allow_html=True)
            
            Roles = ["client", "support"]
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.container():
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    role = st.selectbox("Role", Roles)

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Login", use_container_width=True):
                            if not username or not password or not role:
                                st.error("Please enter username, password, and select role.")
                            elif authenticate(username, password, role):
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.role = role
                                
                                st.markdown("""
                                <style>
                                @keyframes bounce {
                                    0%, 20%, 50%, 80%, 100% {
                                        transform: translateY(0);
                                    }
                                    40% {
                                        transform: translateY(-20px);
                                    }
                                    60% {
                                        transform: translateY(-10px);
                                    }
                                }
                                @keyframes slideIn {
                                    from {
                                        opacity: 0;
                                        transform: translateX(-100px);
                                    }
                                    to {
                                        opacity: 1;
                                        transform: translateX(0);
                                    }
                                }
                                .success-container {
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    padding: 20px;
                                    background: linear-gradient(90deg, #4CAF50, #45a049);
                                    border-radius: 10px;
                                    margin: 20px 0;
                                    animation: slideIn 0.8s ease-out;
                                }
                                .bounce-thumb {
                                    font-size: 3em;
                                    animation: bounce 2s infinite;
                                    margin-right: 15px;
                                }
                                .success-text {
                                    color: white;
                                    font-size: 1.2em;
                                    font-weight: bold;
                                    text-align: center;
                                }
                                </style>
                                <div class="success-container">
                                    <div class="bounce-thumb">👍</div>
                                    <div class="success-text">
                                        Login Successful!<br>
                                        Welcome {username}! 🎉
                                    </div>
                                </div>
                                """.replace("{username}", username), unsafe_allow_html=True)
                                
                                import time
                                time.sleep(2)
                                
                                try:
                                    st.rerun()
                                except AttributeError:
                                    try:
                                        st.experimental_rerun()
                                    except AttributeError:
                                        st.session_state.needs_rerun = True
                            else:
                                st.error("Invalid username, password, or role!")

                    with col_btn2:
                        if st.button("Register", use_container_width=True, type="secondary"):
                            st.session_state.show_register = True
                            try:
                                st.rerun()
                            except AttributeError:
                                try:
                                    st.experimental_rerun()
                                except AttributeError:
                                    st.session_state.needs_rerun = True
        else:    
            st.markdown("<h1 style='text-align: center;'>Create an Account</h1>", unsafe_allow_html=True)
            Roles = ["client", "support"]
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2: 
                with st.form("registration_form"):
                    new_username = st.text_input("Username")
                    new_password = st.text_input("Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    new_role = st.selectbox("Role", Roles)

                    # Buttons side by side
                    button_col1, button_col2 = st.columns([1, 1])
                    with button_col1:
                        create_clicked = st.form_submit_button("Create Account", use_container_width=True)
                    with button_col2:
                        back_clicked = st.form_submit_button("Back to Login", use_container_width=True)
                    
                    if back_clicked:
                        st.session_state.show_register = False
                        try:
                            st.rerun()
                        except AttributeError:
                            try:
                                st.experimental_rerun()
                            except AttributeError:
                                st.session_state.needs_rerun = True
                    
                    if create_clicked:
                        if not new_username or not new_password or not confirm_password:
                            st.error("All fields are required")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match")
                        else:
                            success, message = register_user(new_username, new_password, new_role)
                            if success:
                                st.success("Registration successful! You can now proceed to login")
                                import time
                                time.sleep(3)
                                st.session_state.show_register = False
                                try:
                                    st.rerun()
                                except AttributeError:
                                    try:
                                        st.experimental_rerun()
                                    except AttributeError:
                                        st.session_state.needs_rerun = True
                            else:
                                st.error(message)

    else:
        if st.session_state.role == "client":
            client_query_page()
        elif st.session_state.role == "support":
            support_portal_page()

if __name__ == "__main__":
    main()