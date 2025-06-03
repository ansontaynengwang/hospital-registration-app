import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import pandas as pd
import time
import io
from fpdf import FPDF

# ------------------------ Configuration ------------------------
st.set_page_config(layout="wide")
st.image("https://review.ibanding.com/company/1532441453.jpg", caption="Pekan Hospital", use_container_width=True)
st.title("Pekan Hospital")
st.sidebar.title("Navigation")

# ------------------------ Google Sheets Setup ------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("Patient")
worksheet = sheet.worksheet("Patient")
previous_worksheet = sheet.worksheet("Previous Patient")

# ------------------------ Utility Functions ------------------------
def get_malaysia_time():
    return datetime.now(pytz.timezone("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S")

def load_patient_data():
    data = worksheet.get_all_values()
    headers = data[0]
    rows = data[1:]
    clean_rows = [row for row in rows if any(cell.strip() for cell in row)]
    df = pd.DataFrame(clean_rows, columns=headers)
    df.columns = df.columns.str.strip()
    df = df[df["Patient Full Name"].str.strip().astype(bool)]
    return df

def log_to_previous_patient(data_row):
    previous_worksheet.append_row(data_row)

def reset_registration():
    st.session_state.page = 1
    st.session_state.patient_data = {}
    st.rerun()

# ------------------------ Sidebar Navigation ------------------------
menu_option = st.sidebar.radio("Menu:", ["Register Patient 🤒", "Edit/Delete Patient 📝"])

# ------------------------ Register Patient ------------------------
def register_patient():
    if "page" not in st.session_state:
        st.session_state.page = 1
    if "patient_data" not in st.session_state:
        st.session_state.patient_data = {}

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
                if name.lower() in df["Patient Full Name"].str.lower().tolist():
                    st.warning(f"The patient name '{name}' is already registered.")
                elif ic_number.strip() in df["IC Number"].str.strip().tolist():
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

    elif st.session_state.page == 2:
        st.subheader("Step 2: Admission Details")
        ward_options = ["1A", "2A", "3A", "3B", "CCU", "ICU"]
        ward_num = st.selectbox("Ward Number*", ward_options)
        bed_num = st.number_input("Bed Number*", min_value=1, max_value=120)
        floor = st.selectbox("Floor*", ["1", "2", "3", "4", "5"])
        status = st.selectbox("Patient Status*", ["Stable", "Critical", "Under Observation", "Discharged"])

        if st.button("Submit"):
            patient = st.session_state.patient_data
            time_now = get_malaysia_time()
            new_row = [
                patient["name"], patient["ic_number"], patient["age"], patient["gender"],
                ward_num, bed_num, floor, status, time_now
            ]

            existing_rows = worksheet.get_all_values()[1:]
            empty_row_index = next((i+2 for i, row in enumerate(existing_rows)
                                    if len(row) < 9 or all(cell.strip() == "" for cell in row[:9])), None)

            if empty_row_index:
                worksheet.update(f"A{empty_row_index}:I{empty_row_index}", [new_row])
            else:
                worksheet.append_row(new_row)

            st.success(f"Patient {patient['name']} registered successfully at {time_now}.")
            time.sleep(2)
            reset_registration()

# ------------------------ Edit or Delete Patient ------------------------
def edit_delete_patient():
    st.subheader("Edit or Delete Patient")
    df = load_patient_data()

    if not df.empty:
        patient_names = df["Patient Full Name"].dropna().tolist()
        selected_name = st.selectbox("Select a patient", patient_names)

        if selected_name:
            selected_row_index = df[df["Patient Full Name"] == selected_name].index[0]
            selected_data = df.loc[selected_row_index]

            with st.form("edit_form"):
                new_name = st.text_input("Edit Name", value=selected_data["Patient Full Name"])
                new_ic = st.text_input("Edit IC Number", value=selected_data["IC Number"])
                new_age = st.number_input("Edit Age", min_value=1, max_value=100, value=int(selected_data["Age"]))
                new_gender = st.selectbox("Edit Gender", ["Male", "Female"], index=["Male", "Female"].index(selected_data["Gender"]))
                new_status = st.selectbox("Edit Patient Status", ["Stable", "Critical", "Under Observation", "Discharged"],
                                          index=["Stable", "Critical", "Under Observation", "Discharged"].index(selected_data["Patient Status"]))
                edit_submit = st.form_submit_button("Update Patient")

            if edit_submit:
                st.session_state.edit_pending = {
                    "name": new_name,
                    "ic": new_ic,
                    "age": new_age,
                    "gender": new_gender,
                    "status": new_status,
                    "index": selected_row_index
                }

            if "edit_pending" in st.session_state:
                st.warning("Are you sure you want to update this patient record?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, update"):
                        pending = st.session_state.edit_pending
                        df = load_patient_data()
                        duplicate_ic = df[(df["IC Number"].str.strip() == pending["ic"].strip()) & (df.index != pending["index"])]
                        if not duplicate_ic.empty:
                            st.warning(f"The IC number '{pending['ic']}' is already used by another patient.")
                        else:
                            update_row = pending["index"] + 2
                            time_now = get_malaysia_time()
                            worksheet.update(f"A{update_row}", [[pending["name"].upper()]])
                            worksheet.update(f"B{update_row}", [[pending["ic"].strip()]])
                            worksheet.update(f"C{update_row}", [[pending["age"]]])
                            worksheet.update(f"D{update_row}", [[pending["gender"]]])
                            worksheet.update(f"H{update_row}", [[pending["status"]]])
                            worksheet.update(f"I{update_row}", [[time_now]])

                            st.success(f"✅ Updated patient record for {pending['name']} at {time_now}.")
                            del st.session_state.edit_pending
                            time.sleep(2)
                            st.rerun()

                with col2:
                    if st.button("❌ No, cancel"):
                        st.info("❎ Update cancelled.")
                        del st.session_state.edit_pending
                        time.sleep(2)
                        st.rerun()

            if st.button("Delete Patient"):
                st.session_state.confirm_delete = True

            if st.session_state.get("confirm_delete", False):
                st.warning("⚠️ Are you sure you want to delete this patient record?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Yes, delete"):
                        row_data = df.loc[selected_row_index].to_dict()
                        row_to_delete = [
                            row_data.get("Patient Full Name", ""),
                            row_data.get("IC Number", ""),
                            row_data.get("Age", ""),
                            row_data.get("Gender", ""),
                            row_data.get("Ward Number", ""),
                            row_data.get("Bed Number", ""),
                            row_data.get("Floor", ""),
                            row_data.get("Patient Status", ""),
                            get_malaysia_time()
                        ]
                        log_to_previous_patient(row_to_delete)
                        worksheet.delete_rows(int(selected_row_index) + 2)
                        st.success(f"🗑️ Deleted patient record for {selected_name}.")
                        st.session_state.confirm_delete = False
                        time.sleep(2)
                        st.rerun()

                with col2:
                    if st.button("❎ No, cancel"):
                        st.info("Deletion cancelled.")
                        st.session_state.confirm_delete = False
                        time.sleep(2)
                        st.rerun()

# ------------------------ Main ------------------------
if menu_option == "Register Patient 🤒":
    register_patient()
elif menu_option == "Edit/Delete Patient 📝":
    edit_delete_patient()

# ------------------------ Display Patient Data ------------------------
st.markdown("### Existing Patients")
st.dataframe(load_patient_data())

# ------------------------ Date Range Filter for Download ------------------------
st.sidebar.markdown("### 📆 Filter by Date Range")
df_all = load_patient_data()

if not df_all.empty:
    # Ensure Timestamp is in datetime format
    df_all["Date & Time"] = pd.to_datetime(df_all["Date & Time"], errors='coerce')
    df_all = df_all.dropna(subset=["Date & Time"])  # Drop rows without proper timestamp

    min_date = df_all["Date & Time"].min().date()
    max_date = df_all["Date & Time"].max().date()

    start_date = st.sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)

    if start_date > end_date:
        st.sidebar.warning("⚠️ Start date must be before end date.")
    else:
        # Filter by date
        mask = (df_all["Date & Time"].dt.date >= start_date) & (df_all["Date & Time"].dt.date <= end_date)
        filtered_df = df_all.loc[mask]

        st.markdown("### 🧾 Filtered Patient Data")
        st.dataframe(filtered_df)

        if not filtered_df.empty:
            # ------------------------ Excel Download ------------------------
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                filtered_df.to_excel(writer, index=False, sheet_name="Patients")
            excel_buffer.seek(0)

            st.sidebar.markdown("### 📥 Download Filtered Data")
            st.sidebar.download_button(
                label="Download Excel 📊",
                data=excel_buffer,
                file_name="filtered_patient_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # ------------------------ PDF Download ------------------------
            def generate_pdf(df):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=8)

                col_width = pdf.w / (len(df.columns) + 1)
                row_height = 8

                # Table header
                for col in df.columns:
                    pdf.cell(col_width, row_height, col[:15], border=1)  # Trim long headers
                pdf.ln(row_height)

                # Table rows
                for _, row in df.iterrows():
                    for item in row:
                        pdf.cell(col_width, row_height, str(item)[:15], border=1)  # Trim long data
                    pdf.ln(row_height)

                pdf_bytes = pdf.output(dest="S").encode("latin1")
                return pdf_buffer

            pdf_data = generate_pdf(filtered_df)

            st.sidebar.download_button(
                label="📄 Download PDF (Filtered)",
                data=pdf_bytes,
                file_name="filtered_patient_data.pdf",
                mime="application/pdf"
            )
        else:
            st.sidebar.info("No patient data in selected date range.")
else:
    st.sidebar.info("No patient records available.")
