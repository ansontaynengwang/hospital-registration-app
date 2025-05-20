import streamlit as st
from datetime import datetime
import pytz

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = 1
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {}

st.title("Pekan Hospital Patient Registration")

# Page 1: Basic Info
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
            st.experimental_rerun()

# Page 2: Admission Info
elif st.session_state.page == 2:
    st.header("Step 2: Admission Details")
    wad_num = st.number_input("Wad Number*", min_value=1, max_value=120)
    bed_num = st.number_input("Bed Number*", min_value=1, max_value=120)
    floor = st.selectbox("Floor*", ["1", "2", "3", "4", "5"])
    status = st.selectbox("Patient Status*", ["Stable", "Critical", "Under Observation", "Discharged"])

    if st.button("Submit"):
        # Combine data
        patient = st.session_state.patient_data
        malaysia_time = datetime.now(pytz.timezone("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S")

        # Example: Save to Google Sheet (you can insert your worksheet.append_row here)
        st.success(f"Patient {patient['name']} registered successfully at {malaysia_time}.")

        # Clear session state
        st.session_state.page = 1
        st.session_state.patient_data = {}
