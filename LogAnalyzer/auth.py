import streamlit as st
import json
import os

USER_FILE = "users.json"

# load users
def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

# save users
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# signup
def signup():
    st.subheader("📝 Create Account")

    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")

    if st.button("Sign Up"):
        users = load_users()

        if new_user in users:
            st.error("User already exists")
        else:
            users[new_user] = new_pass
            save_users(users)
            st.success("Account created! Please login.")

# login
def login():
    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()

        if username in users and users[username] == password:
            st.session_state["logged_in"] = True
        else:
            st.error("Invalid credentials")

# main auth
def check_auth():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        choice = st.radio("Choose", ["Login", "Sign Up"])

        if choice == "Login":
            login()
        else:
            signup()

        st.stop()

# logout
def logout():
    if st.sidebar.button("🚪 Logout"):
        st.session_state["logged_in"] = False
        st.rerun()