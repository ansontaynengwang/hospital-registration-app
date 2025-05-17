import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Display hospital image
st.image("https://review.ibanding.com/company/1532441453.jpg", caption="Pekan Hospital", use_container_width=True)

# Set up credentials
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open the spreadsheet and worksheet
sheet = client.open("Patient")  # <- Use your actual Google Sheet name
worksheet = sheet.worksheet("Patient")

# Read existing data
data = worksheet.get_all_records()
df = pd.DataFrame(data)

st.title("Pekan Hospital Patient Registration")
st.markdown("### Existing Patients")
st.dataframe(df)

# Form to add a new patient
st.markdown("### Add New Patient")
with st.form("patient_form"):
    name = st.text_input("Patient Name*")
    age = st.number_input("Age*", min_value=1, max_value=100)
    wad_num = st.number_input("Wad Number*", min_value=1, max_value=120)
    bed_num = st.number_input("Bed Number*", min_value=1, max_value=120)
    gender = st.selectbox("Gender*", ["Select", "Male", "Female"])
    submitted = st.form_submit_button("Submit")

# Validation and submission
if submitted:
    existing_names = df["Patient Name"].str.lower().tolist() if not df.empty else []

    if not name or gender == "Select":
        st.error("Please fill in all fields before submitting.")
    elif name.lower() in existing_names:
        st.warning(f"The patient name '{name}' is already registered.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([name, age, wad_num, bed_num, gender, timestamp])
        st.success(f"Added {name} to the patient list.")
        st.info("Please refresh the page to see the updated list.")
