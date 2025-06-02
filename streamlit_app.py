import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import pytz
import time

# Set up the Streamlit page
st.set_page_config(layout="wide")
st.image("https://review.ibanding.com/company/1532441453.jpg", caption="Pekan Hospital", use_container_width=True)
st.title("Pekan Hospital")

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Menu", ["Register Patient 🤒", "Edit/Delete Patient 📝", "Visitor Log 🧑‍⚕️"])

# Authenticate with Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open the spreadsheet and get worksheets
main_sheet = client.open("Patient")
patient_ws = main_sheet.worksheet("Patient")
previous_patient_ws = main_sheet.worksheet("Previous Patient")
visitor_ws = main_sheet.worksheet("Visitors")
availability_ws = main_sheet.worksheet("Availability")

def get_time():
    return datetime.now(pytz.timezone("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S")

def register_patient():
    with st.form("register_form"):
        st.subheader("Patient Registration")
        col1, col2, col3 = st.columns(3)
        with col1:
            bed = st.text_input("Bed")
            code = st.text_input("Code")
        with col2:
            name = st.text_input("Name")
            age = st.text_input("Age")
        with col3:
            gender = st.selectbox("Gender", ["", "Male", "Female"])
            ward = st.text_input("Ward")
        diagnosis = st.text_area("Diagnosis")
        complaint = st.text_area("Complaint")
        submit_button = st.form_submit_button(label="Register Patient")

        if submit_button:
            if not all([bed, code, name, age, gender, ward, diagnosis, complaint]):
                st.error("All fields are required.")
            else:
                time_now = get_time()
                data = [time_now, bed, code, name, age, gender, ward, diagnosis, complaint]
                patient_ws.append_row(data)
                st.success(f"Patient {name} registered successfully!")

def edit_delete_patient():
    st.subheader("Edit or Delete Patient Record")
    patients = patient_ws.get_all_values()[1:]  # Skip header
    if not patients:
        st.write("No patients found.")
        return

    df = pd.DataFrame(patients, columns=["Timestamp", "Bed", "Code", "Name", "Age", "Gender", "Ward", "Diagnosis", "Complaint"])
    selected = st.selectbox("Select Patient to Edit/Delete", df["Name"] + " - " + df["Code"])
    if selected:
        index = df[df["Name"] + " - " + df["Code"] == selected].index[0] + 2  # account for header + 1-based index
        with st.form("edit_form"):
            updated = {}
            for field in ["Bed", "Code", "Name", "Age", "Gender", "Ward", "Diagnosis", "Complaint"]:
                updated[field] = st.text_input(field, value=df.at[index-2, field])
            submit_edit = st.form_submit_button("Update Record")
            delete_record = st.form_submit_button("Delete Record")

        if submit_edit:
            time_now = get_time()
            data = [time_now] + [updated[f] for f in ["Bed", "Code", "Name", "Age", "Gender", "Ward", "Diagnosis", "Complaint"]]
            patient_ws.delete_rows(index)
            patient_ws.insert_row(data, index)
            st.success("Patient record updated.")

        if delete_record:
            patient_ws.delete_rows(index)
            previous_patient_ws.append_row([df.at[index-2, col] for col in df.columns])
            st.success("Patient record moved to Previous Patient and deleted.")

def visitor_log():
    st.header("Availability Sheet")
    availability_df = pd.DataFrame(availability_ws.get_all_records())
    st.dataframe(availability_df if not availability_df.empty else "No data.")

    st.header("Visitors Record")
    visitor_df = pd.DataFrame(visitor_ws.get_all_records())
    if visitor_df.empty:
        visitor_df = pd.DataFrame(columns=["Time", "Date", "UID", "Ward", "Bed", "IN / OUT"])
    st.dataframe(visitor_df)

    st.subheader("Search Visitor")
    uid = st.text_input("Enter UID")
    ward = st.text_input("Enter Ward")
    bed = st.text_input("Enter Bed")
    in_out = st.radio("IN / OUT", ["IN", "OUT"])
    current_time = datetime.now(pytz.timezone("Asia/Kuala_Lumpur"))
    current_date = current_time.strftime("%Y-%m-%d")
    current_time_str = current_time.strftime("%H:%M:%S")

    if st.button("Submit Visitor Record"):
        data = [current_time_str, current_date, uid, ward, bed, in_out]
        visitor_ws.append_row(data)
        st.success("Visitor record added.")

if menu == "Register Patient 🤒":
    register_patient()
elif menu == "Edit/Delete Patient 📝":
    edit_delete_patient()
elif menu == "Visitor Log 🧑‍⚕️":
    visitor_log()
