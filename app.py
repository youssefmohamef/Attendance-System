# %%writefile DocumentScanner.py
import numpy as np
import cv2
import streamlit as st
import pytesseract 
from PIL import Image
import datetime
import pandas as pd
import os
import re

# --- UI Configuration ---
st.set_page_config(page_title="AI Attendance System", layout="wide")
st.title('🆔 Smart Attendance System')
st.markdown("Scan your ID card using the **Camera**")

# --- Session State Initialization ---
# This key is used to reset the camera/uploader when switching to a new student
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# --- Tesseract OCR Path ---
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# --- Image Processing Functions ---

def pre_process_image(img_array):
    """Convert to grayscale and apply Otsu thresholding for better OCR"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    _, processed_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return processed_img

def extract_id_with_context(text):
    """Search for student code based on specific keywords"""
    lines = [line.strip() for line in text.lower().splitlines() if line.strip()]
    target_keywords = ['كود الطالب', 'student code', 'كود', 'code', "id number"]
    
    for i, line in enumerate(lines):
        if any(key in line for key in target_keywords):
            # Check for numbers in the same line (excluding letters like CMP)
            numbers_same_line = re.findall(r'\b\d{5,}\b', line) 
            if numbers_same_line:
                return numbers_same_line[0]
            
            # Check for numbers in the next line
            if i + 1 < len(lines):
                next_line = lines[i+1]
                numbers_next_line = re.findall(r'\b\d{5,}\b', next_line)
                if numbers_next_line:
                    return numbers_next_line[0]
    
    # Fallback: Find the last long numeric string in the text
    all_long_numbers = re.findall(r'\b\d{7,}\b', text)
    return all_long_numbers[-1] if all_long_numbers else None

def save_attendance(student_id):
    """Log the student ID to a CSV file and prevent duplicates in the same minute"""
    filename = 'attendance_records.csv'
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    current_minute = now.strftime("%Y-%m-%d %H:%M")
    
    new_entry = pd.DataFrame([[student_id, timestamp]], columns=['Student_ID', 'Timestamp'])
    
    if os.path.isfile(filename):
        df_existing = pd.read_csv(filename)
        is_duplicate = not df_existing[(df_existing['Student_ID'].astype(str) == str(student_id)) & 
                                     (df_existing['Timestamp'].str.contains(current_minute))].empty
        if not is_duplicate:
            new_entry.to_csv(filename, mode='a', header=False, index=False)
            return timestamp, True
        return timestamp, False
    else:
        new_entry.to_csv(filename, index=False)
        return timestamp, True

# --- Main App Logic ---

st.subheader("📸 Step 1: Input Source")
input_mode = st.radio("Choose source:", ("📷 Live Camera Scan"), horizontal=True)

# Generate a dynamic key to reset inputs
final_image_file = None
current_key = f"{input_mode}_{st.session_state.uploader_key}"

if input_mode == "📷 Live Camera Scan":
    final_image_file = st.camera_input("Capture ID", key=current_key)

if final_image_file:
    pil_img = Image.open(final_image_file)
    img_array = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    with st.spinner('🔍 Extracting ID...'):
        processed_img = pre_process_image(img_bgr)
        try:
            extracted_text = pytesseract.image_to_string(processed_img, lang='eng+ara', config='--psm 6')
        except:
            extracted_text = pytesseract.image_to_string(processed_img, lang='eng', config='--psm 6')
        
        student_id = extract_id_with_context(extracted_text)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.image(img_bgr, channels="BGR", caption="Input Image")

    with col2:
        st.subheader("🎯 Result")
        if student_id:
            st.success(f"**Identified ID:** {student_id}")
            log_time, success = save_attendance(student_id)
            
            if success:
                st.info(f"✅ Logged at: {log_time}")
                st.balloons()
            else:
                st.warning("⚠️ Already logged recently.")
            
            # Increment key to clear the current photo for the next student
            if st.button("➕ Next Student"):
                st.session_state.uploader_key += 1
                st.rerun()
        else:
            st.error("❌ No ID detected.")
            if st.button("🔄 Retry"):
                st.session_state.uploader_key += 1
                st.rerun()

# --- Record Management (Sidebar) ---
with st.sidebar:
    st.header("🧹 Data Management")
    if st.button("🗑️ Clear Everything", type="primary"):
        if os.path.isfile('attendance_records.csv'):
            os.remove('attendance_records.csv')
            st.rerun()

# --- Attendance History Table ---
if os.path.isfile('attendance_records.csv'):
    st.divider()
    st.subheader("📋 Attendance History")
    df_log = pd.read_csv('attendance_records.csv')
    
    # Interactive data editor to allow individual row deletion
    edited_df = st.data_editor(
        df_log.iloc[::-1], 
        column_config={"Delete": st.column_config.CheckboxColumn("Remove", default=False)},
        disabled=["Student_ID", "Timestamp"],
        use_container_width=True,
        key="editor"
    )

    if st.button("❌ Remove Selected"):
        if "Delete" in edited_df.columns:
            final_df = edited_df[edited_df["Delete"] == False].drop(columns=["Delete"])
            final_df.iloc[::-1].to_csv('attendance_records.csv', index=False)
            st.rerun()