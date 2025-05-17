import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

try:
    sheet = client.open("Patient")
    st.success("✅ Successfully connected to Google Sheet!")
except Exception as e:
    st.error(f"❌ Failed to connect: {e}")
