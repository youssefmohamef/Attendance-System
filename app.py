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
st.markdown("Scan student IDs via **Live Camera** or **Upload a Photo** to log attendance.")

# --- OCR Engine Path Configuration ---
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# --- Helper Functions ---

def pre_process_image(img_array):
    """Enhance image for better OCR accuracy and glare reduction."""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    # Applying median blur to handle camera noise
    blurred = cv2.medianBlur(gray, 3)
    # Adaptive thresholding handles uneven lighting better than static thresholding
    processed_img = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
    return processed_img

def extract_id_with_context(text):
    """
    Search logic:
    1. Looks for keywords (ID, Code, etc.)
    2. Checks the same line or the immediate next line for numbers.
    """
    keywords = ['id', 'number', 'code', 'student', 'كود', 'الرقم', 'الطالب', 'جامعي']
    lines = [line.strip() for line in text.lower().splitlines() if line.strip()]
    
    for i, line in enumerate(lines):
        if any(key in line for key in keywords):
            # Same line check
            numbers_same = re.findall(r'\d+', line)
            if numbers_same:
                for num in numbers_same:
                    if len(num) >= 3: return num
            
            # Next line check (Crucial for cards where ID is below the label)
            if i + 1 < len(lines):
                numbers_next = re.findall(r'\d+', lines[i+1])
                if numbers_next:
                    for num in numbers_next:
                        if len(num) >= 3: return num
    
    # Fallback: Find longest numeric string
    all_numbers = re.findall(r'\d{5,}', text)
    return all_numbers[0] if all_numbers else None

def save_attendance(student_id):
    """Log to CSV and prevent duplicates within the same minute."""
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
        else:
            return timestamp, False
    else:
        new_entry.to_csv(filename, index=False)
        return timestamp, True

# --- Sidebar: Notes & License ---
with st.sidebar:
    st.header("📝 Project Info")
    st.info("""
    **Notes:**
    - Avoid direct light glare on the ID.
    - Ensure the ID number is clear and horizontal.
    - Path: `attendance_records.csv`
    """)
    st.divider()
    st.markdown("### ⚖️ License")
    st.caption("Licensed under the **MIT License**. You are free to use and modify this code.")

# --- Main Application Logic ---

# Step 1: Input Source Selection
st.subheader("📸 Step 1: Provide ID Image")
source = st.radio("Choose source:", ("Live Camera", "Upload Image File"), horizontal=True)

input_image = None
if source == "Live Camera":
    input_image = st.camera_input("Scan ID Card")
else:
    input_image = st.file_uploader("Choose an image file...", type=['jpg', 'jpeg', 'png'])

if input_image:
    pil_img = Image.open(input_image)
    img_array = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    with st.spinner('🔍 Analyzing context and searching for ID...'):
        processed_img = pre_process_image(img_bgr)
        try:
            extracted_text = pytesseract.image_to_string(processed_img, lang='eng+ara', config='--psm 6')
        except:
            extracted_text = pytesseract.image_to_string(processed_img, lang='eng', config='--psm 6')
        
        student_id = extract_id_with_context(extracted_text)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.image(img_bgr, channels="BGR", caption="Input ID Card")

    with col2:
        st.subheader("🎯 System Detection")
        if student_id:
            st.success(f"**Identified ID:** {student_id}")
            log_time, success = save_attendance(student_id)
            
            if success:
                st.info(f"✅ Registered at: {log_time}")
                st.balloons()
            else:
                st.warning("⚠️ Already logged in the last minute.")
            
            if st.button("➕ Clear & Add Next"):
                st.rerun()
        else:
            st.error("❌ No ID found. Ensure keywords (ID, Code) or numbers are visible.")
            with st.expander("Debug: Raw Text Output"):
                st.text(extracted_text)

# --- Step 4: Attendance Log ---
if os.path.isfile('attendance_records.csv'):
    st.divider()
    st.subheader("📋 Recent Attendance Records")
    df_log = pd.read_csv('attendance_records.csv')
    st.dataframe(df_log.iloc[::-1], use_container_width=True)
    
    # Export options
    csv_data = df_log.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Attendance Report (CSV)",
        data=csv_data,
        file_name='attendance_report.csv',
        mime='text/csv',
    )