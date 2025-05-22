import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import pandas as pd
import time

# Get current Malaysia time
def get_malaysia_time():
    return datetime.now(pytz.timezone("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S")

# Display hospital image
st.image("https://review.ibanding.com/company/1532441453.jpg", caption="Pekan Hospital", use_container_width=True)

# Google Sheets authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open the spreadsheet and worksheet
sheet = client.open("Patient")
worksheet = sheet.worksheet("Patient")

# Read and clean data
def load_patient_data():
    data = worksheet.get_all_values()
    headers = data[0]
    rows = data[1:]
    clean_rows = [row for row in rows if any(cell.strip() for cell in row)]
    df = pd.DataFrame(clean_rows, columns=headers)
    df = df[df["Patient Full Name"].str.strip().astype(bool)]
    return df

df = load_patient_data()

st.title("Pekan Hospital")
st.sidebar.title("Navigation")
menu_option = st.sidebar.radio("Choose an action:", ["Register Patient 🤒", "Edit/Delete Patient 📝"])

# Registration Section
if menu_option == "Register Patient":
    if "page" not in st.session_state:
        st.session_state.page = 1
    if "patient_data" not in st.session_state:
        st.session_state.patient_data = {}

    # Step 1: Basic Info
    if st.session_state.page == 1:
        st.header("Patient Registration System")
        st.subheader("Step 1: Basic Patient Information")
        with st.form("basic_info_form"):
            name = st.text_input("Patient Full Name*", key="name")
            ic_number = st.text_input("IC Number*", key="ic_number")
            age = st.number_input("Age*", min_value=1, max_value=100, key="age")
            gender = st.selectbox("Gender*", ["Select", "Male", "Female"], key="gender")
            next_clicked = st.form_submit_button("Next")

        if next_clicked:
            if not name or not ic_number or gender == "Select":
                st.error("Please fill in all required fields.")
            else:
                df = load_patient_data()
                existing_names = df["Patient Full Name"].str.lower().tolist()
                existing_ics = df["IC Number"].str.strip().tolist()

                if name.lower() in existing_names:
                    st.warning(f"The patient name '{name}' is already registered.")
                elif ic_number.strip() in existing_ics:
                    st.warning(f"The IC number '{ic_number}' is already registered.")
                else:
                    st.session_state.patient_data = {
                        "name": name.upper(),
                        "ic_number": ic_number.strip(),
                        "age": age,
                        "gender": gender
                    }
                    st.session_state.page = 2
                    st.rerun()

    # Step 2: Admission Info
    elif st.session_state.page == 2:
        st.subheader("Step 2: Admission Details")
        wad_options = ["1A", "2A", "3A", "3B", "CCU", "ICU"]
        wad_num = st.selectbox("Wad Number*", wad_options, key="wad_num")
        bed_num = st.number_input("Bed Number*", min_value=1, max_value=120, key="bed_num")
        floor = st.selectbox("Floor*", ["1", "2", "3", "4", "5"], key="floor_selectbox")
        status = st.selectbox("Patient Status*", ["Stable", "Critical", "Under Observation", "Discharged"], key="status")

        if st.button("Submit"):
            patient = st.session_state.patient_data
            time_now = get_malaysia_time()

            new_row = [
                patient["name"],
                patient["ic_number"],
                patient["age"],
                patient["gender"],
                wad_num,
                bed_num,
                floor,
                status,
                time_now
            ]

            data = worksheet.get_all_values()
            rows = data[1:]
            empty_row_index = None
            for i, row in enumerate(rows, start=2):
                if len(row) < 9 or all(cell.strip() == "" for cell in row[:9]):
                    empty_row_index = i
                    break

            if empty_row_index:
                worksheet.update(f"A{empty_row_index}:I{empty_row_index}", [new_row])
            else:
                worksheet.append_row(new_row)

            st.success(f"Patient {patient['name']} registered successfully at {time_now}.")
            time.sleep(2)
            st.session_state.page = 1
            st.session_state.patient_data = {}
            st.rerun()

    # Register another patient
    if st.button("Register Another Patient"):
        st.session_state.page = 1
        st.session_state.patient_data = {}
        st.rerun()

# Edit/Delete Section
elif menu_option == "Edit/Delete Patient":
    st.subheader("Edit or Delete Patient")

    df = load_patient_data()
    if not df.empty:
        df.columns = df.columns.str.strip()
        patient_names = df["Patient Full Name"].dropna().tolist()
        selected_name = st.selectbox("Select a patient", patient_names)

        if selected_name:
            selected_row_index = df[df["Patient Full Name"] == selected_name].index[0]
            selected_data = df.loc[selected_row_index]

            with st.form("edit_form"):
                new_name = st.text_input("Edit Name", value=selected_data["Patient Full Name"])
                new_ic = st.text_input("Edit IC Number", value=selected_data["IC Number"])
                new_age = st.number_input("Edit Age", min_value=1, max_value=100, value=int(selected_data["Age"]))
                new_gender = st.selectbox("Edit Gender", ["Male", "Female"],
                                          index=["Male", "Female"].index(selected_data["Gender"]))
                new_status = st.selectbox("Edit Patient Status", ["Stable", "Critical", "Under Observation", "Discharged"],
                                          index=["Stable", "Critical", "Under Observation", "Discharged"].index(selected_data["Patient Status"]))
                edit_submit = st.form_submit_button("Update Patient")

            if edit_submit:
                confirm_edit = st.radio("Are you sure you want to update this patient record?", ["No", "Yes"])
                if confirm_edit == "Yes":
                    df = load_patient_data()
                    duplicate_ic = df[(df["IC Number"].str.strip() == new_ic.strip()) & (df.index != selected_row_index)]

                    if not duplicate_ic.empty:
                        st.warning(f"The IC number '{new_ic}' is already used by another patient.")
                    else:
                        time_now = get_malaysia_time()
                        update_row = selected_row_index + 2

                        worksheet.update(f"A{update_row}", [[new_name.upper()]])
                        worksheet.update(f"B{update_row}", [[new_ic.strip()]])
                        worksheet.update(f"C{update_row}", [[new_age]])
                        worksheet.update(f"D{update_row}", [[new_gender]])
                        worksheet.update(f"H{update_row}", [[new_status]])
                        worksheet.update(f"I{update_row}", [[time_now]])

                        st.success(f"Updated patient record for {new_name}.")
                        time.sleep(2)
                        st.rerun()
                else:
                    st.info("Update cancelled.")

            if st.button("Delete Patient"):
                confirm_delete = st.radio("Are you sure you want to delete this patient record?", ["No", "Yes"], key="confirm_delete")
                if confirm_delete == "Yes":
                    try:
                        worksheet.delete_rows(int(selected_row_index) + 2)
                        st.success(f"Deleted patient record for {selected_name}.")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting row: {e}")
                else:
                    st.info("Deletion cancelled.")
                    
# Display data
st.markdown("### Existing Patients")
st.dataframe(df)
