import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import pandas as pd

# Display hospital image
st.image("https://review.ibanding.com/company/1532441453.jpg", caption="Pekan Hospital", use_container_width=True)

# Set up credentials using st.secrets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open the spreadsheet and worksheet
sheet = client.open("Patient")
worksheet = sheet.worksheet("Patient")

# Read existing data
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = 1
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {}

st.title("Pekan Hospital Patient Registration")

# Step 1: Basic Info
if st.session_state.page == 1:
    st.header("Step 1: Basic Patient Information")
    name = st.text_input("Patient Full Name*")
    ic_number = st.text_input("IC Number*")
    age = st.number_input("Age*", min_value=1, max_value=100)
    gender = st.selectbox("Gender*", ["Select", "Male", "Female"])

    if st.button("Next"):
        if not name or not ic_number or gender == "Select":
            st.error("Please fill in all required fields.")
        else:
            st.session_state.patient_data = {
                "name": name,
                "ic_number": ic_number,
                "age": age,
                "gender": gender
            }
            st.session_state.page = 2


# Step 2: Admission Info
elif st.session_state.page == 2:
    st.header("Step 2: Admission Details")
    wad_num = st.number_input("Wad Number*", min_value=1, max_value=120)
    bed_num = st.number_input("Bed Number*", min_value=1, max_value=120)
    floor = st.selectbox("Floor*", ["1", "2", "3", "4", "5"])
    status = st.selectbox("Patient Status*", ["Stable", "Critical", "Under Observation", "Discharged"])

    if st.button("Submit"):
        patient = st.session_state.patient_data
        malaysia_time = datetime.now(pytz.timezone("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S")

        # Check for duplicates
        existing_names = df["Patient Name"].str.lower().tolist() if not df.empty else []
        if patient["name"].lower() in existing_names:
            st.warning(f"The patient name '{patient['name']}' is already registered.")
        else:
            worksheet.append_row([
                patient["name"],
                patient["ic_number"],
                patient["age"],
                patient["gender"],
                wad_num,
                bed_num,
                floor,
                status,
                malaysia_time
            ])
            st.success(f"Patient {patient['name']} registered successfully at {malaysia_time}.")

        # Reset session state
        st.session_state.page = 1
        st.session_state.patient_data = {}
        st.experimental_rerun()

# Display existing patients
st.markdown("### Existing Patients")
st.dataframe(df)
