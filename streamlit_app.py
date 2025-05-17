import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

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

st.title("Pekan Hospital Patient Registration")

# Show existing patients
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

# Edit or delete patient
st.markdown("### Edit or Delete Patient")

if not df.empty:
    selected_name = st.selectbox("Select a patient to edit or delete", df["Patient Name"].tolist())

    selected_row = df[df["Patient Name"] == selected_name].index[0]
    selected_data = df.loc[selected_row]

    with st.form("edit_form"):
        new_name = st.text_input("Edit Name", value=selected_data["Patient Name"])
        new_age = st.number_input("Edit Age", min_value=1, max_value=100, value=int(selected_data["Age"]))
        new_wad = st.number_input("Edit Wad Number", min_value=1, max_value=120, value=int(selected_data["Wad Number"]))
        new_bed = st.number_input("Edit Bed Number", min_value=1, max_value=120, value=int(selected_data["Bed Number"]))
        new_gender = st.selectbox("Edit Gender", ["Male", "Female"], index=["Male", "Female"].index(selected_data["Gender"]))
        edit_submitted = st.form_submit_button("Update Patient")

    if edit_submitted:
        worksheet.update(f"A{selected_row + 2}", new_name)
        worksheet.update(f"B{selected_row + 2}", new_age)
        worksheet.update(f"C{selected_row + 2}", new_wad)
        worksheet.update(f"D{selected_row + 2}", new_bed)
        worksheet.update(f"E{selected_row + 2}", new_gender)
        st.success(f"Updated patient record for {new_name}. Please refresh to see changes.")

    if st.button("Delete Patient"):
        worksheet.delete_rows(selected_row + 2)
        st.success(f"Deleted patient record for {selected_name}. Please refresh to see changes.")
else:
    st.info("No patients to edit or delete.")
