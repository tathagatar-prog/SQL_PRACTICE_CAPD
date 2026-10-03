import streamlit as st
import sqlite3
import pandas as pd
import os
import re
import hashlib

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="SQL Practice Lab",
    page_icon="🗄️",
    layout="wide"
)

DATABASE_FOLDER = "databases"

os.makedirs(DATABASE_FOLDER, exist_ok=True)


# =========================================================
# BASIC FUNCTIONS
# =========================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def clean_username(name):
    """
    Creates username from first 4 letters of student's name.
    Example:
    Rahul Kumar -> RAHU
    Amit Das    -> AMIT
    """

    letters = re.sub(r"[^a-zA-Z]", "", name)

    if len(letters) < 4:
        return letters.upper()

    return letters[:4].upper()


def database_path(username):
    return os.path.join(
        DATABASE_FOLDER,
        username.lower() + ".db"
    )


def connect_database(username):
    return sqlite3.connect(database_path(username))


# =========================================================
# USER DATABASE
# =========================================================

USER_DATABASE = "users.db"


def create_user_database():

    conn = sqlite3.connect(USER_DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_user_database()


# =========================================================
# REGISTER USER
# =========================================================

def register_student(name):

    username = clean_username(name)

    if len(username) < 4:
        return False, "Name must contain at least 4 letters."

    conn = sqlite3.connect(USER_DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT username FROM users WHERE username = ?",
        (username,)
    )

    existing = cursor.fetchone()

    if existing:

        conn.close()

        return False, (
            f"Username {username} already exists. "
            "Please use a different name."
        )

    password = "1234"

    cursor.execute(
        """
        INSERT INTO users
        (name, username, password)
        VALUES (?, ?, ?)
        """,
        (
            name,
            username,
            hash_password(password)
        )
    )

    conn.commit()
    conn.close()

    # Create student's personal database
    conn = sqlite3.connect(database_path(username))

    conn.close()

    return True, username


# =========================================================
# LOGIN
# =========================================================

def login_student(username, password):

    conn = sqlite3.connect(USER_DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name, username
        FROM users
        WHERE username = ?
        AND password = ?
        """,
        (
            username.upper(),
            hash_password(password)
        )
    )

    user = cursor.fetchone()

    conn.close()

    return user


# =========================================================
# CHANGE PASSWORD
# =========================================================

def change_password(username, new_password):

    conn = sqlite3.connect(USER_DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET password = ?
        WHERE username = ?
        """,
        (
            hash_password(new_password),
            username
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# GET TABLES
# =========================================================

def get_tables(username):

    conn = connect_database(username)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)

    tables = [row[0] for row in cursor.fetchall()]

    conn.close()

    return tables


# =========================================================
# GET TABLE COLUMNS
# =========================================================

def get_columns(username, table_name):

    conn = connect_database(username)

    cursor = conn.cursor()

    cursor.execute(
        f'PRAGMA table_info("{table_name}")'
    )

    columns = cursor.fetchall()

    conn.close()

    return columns


# =========================================================
# VIEW TABLE
# =========================================================

def view_table(username, table_name):

    conn = connect_database(username)

    try:

        query = f'SELECT * FROM "{table_name}"'

        dataframe = pd.read_sql_query(
            query,
            conn
        )

        return dataframe

    finally:

        conn.close()


# =========================================================
# EXECUTE SQL
# =========================================================

def execute_sql(username, query):

    conn = connect_database(username)

    try:

        cursor = conn.cursor()

        cursor.execute(query)

        # SELECT query
        if query.strip().upper().startswith(
            ("SELECT", "PRAGMA", "WITH")
        ):

            rows = cursor.fetchall()

            columns = [
                description[0]
                for description in cursor.description
            ]

            dataframe = pd.DataFrame(
                rows,
                columns=columns
            )

            return True, dataframe

        # Other SQL commands
        else:

            conn.commit()

            return True, (
                f"Query executed successfully.\n\n"
                f"Rows affected: {cursor.rowcount}"
            )

    except Exception as e:

        return False, str(e)

    finally:

        conn.close()


# =========================================================
# LOGIN PAGE
# =========================================================

def login_page():

    st.title("🗄️ SQL Practice Lab")

    st.write(
        "Practice SQL using your personal database."
    )

    st.divider()

    tab1, tab2 = st.tabs(
        ["🔐 Login", "📝 First Time Registration"]
    )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    with tab1:

        st.subheader("Student Login")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "🔑 Login",
            use_container_width=True
        ):

            if not username or not password:

                st.warning(
                    "Please enter username and password."
                )

            else:

                user = login_student(
                    username,
                    password
                )

                if user:

                    st.session_state.logged_in = True
                    st.session_state.username = user[1]
                    st.session_state.name = user[0]

                    st.rerun()

                else:

                    st.error(
                        "❌ Invalid username or password."
                    )

    # -----------------------------------------------------
    # REGISTRATION
    # -----------------------------------------------------

    with tab2:

        st.subheader("Create Student Account")

        st.info(
            "Your initial password will be 1234."
        )

        name = st.text_input(
            "Enter your full name",
            key="register_name",
            placeholder="Example: Rahul Kumar"
        )

        if st.button(
            "📝 Register",
            use_container_width=True
        ):

            if not name.strip():

                st.warning(
                    "Please enter your name."
                )

            else:

                success, result = register_student(
                    name.strip()
                )

                if success:

                    st.success(
                        "Registration successful!"
                    )

                    st.write(
                        f"**Your username:** `{result}`"
                    )

                    st.write(
                        "**Your initial password:** `1234`"
                    )

                    st.info(
                        "Please remember your username."
                    )

                else:

                    st.error(result)


# =========================================================
# STUDENT DASHBOARD
# =========================================================

def student_dashboard():

    username = st.session_state.username
    name = st.session_state.name

    # -----------------------------------------------------
    # SIDEBAR
    # -----------------------------------------------------

    with st.sidebar:

        st.title("🗄️ SQL Lab")

        st.write(f"👨‍🎓 **{name}**")

        st.write(
            f"Username: `{username}`"
        )

        st.divider()

        page = st.radio(
            "Menu",
            [
                "💻 SQL Editor",
                "📋 My Tables",
                "🔐 Change Password"
            ]
        )

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.name = None

            st.rerun()

    # =====================================================
    # SQL EDITOR
    # =====================================================

    if page == "💻 SQL Editor":

        st.title("💻 SQL Editor")

        st.write(
            f"Welcome **{name}** 👋"
        )

        st.info(
            f"Your personal database: **{username}**"
        )

        st.divider()

        # -------------------------------------------------
        # SAMPLE QUERY BUTTONS
        # -------------------------------------------------

        st.subheader("Quick Examples")

        col1, col2, col3, col4 = st.columns(4)

        if col1.button("CREATE TABLE"):

            st.session_state.example_query = """
CREATE TABLE Student (
    RollNo INTEGER PRIMARY KEY,
    Name TEXT,
    Marks INTEGER
);
"""

        if col2.button("INSERT DATA"):

            st.session_state.example_query = """
INSERT INTO Student
VALUES
(101, 'Rahul', 85),
(102, 'Priya', 92),
(103, 'Amit', 76);
"""

        if col3.button("SELECT DATA"):

            st.session_state.example_query = """
SELECT * FROM Student;
"""

        if col4.button("UPDATE DATA"):

            st.session_state.example_query = """
UPDATE Student
SET Marks = 90
WHERE RollNo = 101;
"""

        # -------------------------------------------------
        # SQL EDITOR
        # -------------------------------------------------

        default_query = st.session_state.get(
            "example_query",
            ""
        )

        query = st.text_area(
            "Enter SQL Query",
            value=default_query,
            height=300,
            placeholder="""
Example:

CREATE TABLE Student (
    RollNo INTEGER PRIMARY KEY,
    Name TEXT,
    Marks INTEGER
);

INSERT INTO Student
VALUES (101, 'Rahul', 85);

SELECT * FROM Student;
"""
        )

        if st.button(
            "▶ Execute SQL",
            type="primary",
            use_container_width=True
        ):

            if not query.strip():

                st.warning(
                    "Please enter an SQL query."
                )

            else:

                success, result = execute_sql(
                    username,
                    query
                )

                if success:

                    st.success(
                        "✅ Query executed successfully."
                    )

                    if isinstance(
                        result,
                        pd.DataFrame
                    ):

                        st.dataframe(
                            result,
                            use_container_width=True
                        )

                    else:

                        st.code(result)

                else:

                    st.error(
                        "❌ SQL Error"
                    )

                    st.code(result)

        # -------------------------------------------------
        # DATABASE INFORMATION
        # -------------------------------------------------

        st.divider()

        st.subheader("📊 Your Database")

        tables = get_tables(username)

        if tables:

            st.write(
                "Tables currently available:"
            )

            cols = st.columns(
                min(len(tables), 4)
            )

            for i, table in enumerate(tables):

                cols[
                    i % len(cols)
                ].success(
                    f"📋 {table}"
                )

        else:

            st.info(
                "No tables yet. Create your first table "
                "using CREATE TABLE."
            )

    # =====================================================
    # MY TABLES
    # =====================================================

    elif page == "📋 My Tables":

        st.title("📋 My Tables")

        tables = get_tables(username)

        if not tables:

            st.info(
                "You don't have any tables yet."
            )

        else:

            selected_table = st.selectbox(
                "Select a table",
                tables
            )

            if selected_table:

                st.subheader(
                    f"Table: {selected_table}"
                )

                dataframe = view_table(
                    username,
                    selected_table
                )

                st.dataframe(
                    dataframe,
                    use_container_width=True
                )

                st.divider()

                st.subheader(
                    "Table Structure"
                )

                columns = get_columns(
                    username,
                    selected_table
                )

                structure = pd.DataFrame(
                    columns,
                    columns=[
                        "CID",
                        "Column",
                        "Type",
                        "Not Null",
                        "Default",
                        "Primary Key"
                    ]
                )

                st.dataframe(
                    structure,
                    use_container_width=True
                )

    # =====================================================
    # CHANGE PASSWORD
    # =====================================================

    elif page == "🔐 Change Password":

        st.title("🔐 Change Password")

        st.write(
            f"Username: **{username}**"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button(
            "Change Password",
            type="primary"
        ):

            if not new_password:

                st.warning(
                    "Enter a new password."
                )

            elif new_password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                change_password(
                    username,
                    new_password
                )

                st.success(
                    "Password changed successfully."
                )


# =========================================================
# MAIN APPLICATION
# =========================================================

def main():

    if "logged_in" not in st.session_state:

        st.session_state.logged_in = False

    if st.session_state.logged_in:

        student_dashboard()

    else:

        login_page()


if __name__ == "__main__":

    main()