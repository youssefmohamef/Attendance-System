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
st.set_page_config(page_title="Smart AI Attendance", layout="wide")
st.title('Smart Context-Aware Attendance')
# st.markdown("Recognizes IDs based on keywords like **'ID Number'**, **'Student Code'**, or **'كود الطالب'**.")
st.divider()

# --- OCR Engine Path Configuration ---
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# --- Helper Functions ---

def pre_process_image(img_array):
    """Enhance image for better OCR accuracy."""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    # Median blur to remove noise while keeping edges sharp
    blurred = cv2.medianBlur(gray, 3)
    # Apply Otsu's thresholding
    _, processed_img = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return processed_img

def extract_id_with_context(text):
    """
    Search logic:
    1. Look for keywords (ID, Code, etc.)
    2. Check the same line for numbers.
    3. If not found, check the immediate next line.
    """
    keywords = ['id', 'number', 'code', 'student', 'كود', 'الرقم', 'الطالب', 'جامعي']
    lines = [line.strip() for line in text.lower().splitlines() if line.strip()]
    
    
    for i, line in enumerate(lines):
        # If a keyword is found in the current line
        if any(key in line for key in keywords):
            # A. Search for numbers in the SAME line (بجانب الكلمة)
            numbers_same_line = re.findall(r'\d+', line)
            if numbers_same_line:
                # Return the first number that looks like an ID (at least 3 digits)
                for num in numbers_same_line:
                    if len(num) >= 3: return num
            
            # B. Search in the NEXT line (أسفل الكلمة) - fixed for your ID card style
            if i + 1 < len(lines):
                next_line = lines[i+1]
                numbers_next_line = re.findall(r'\d+', next_line)
                if numbers_next_line:
                    for num in numbers_next_line:
                        if len(num) >= 3: return num
    
    # Fallback: Just find the longest numeric string in the whole text
    all_numbers = re.findall(r'\d{5,}', text)
    return all_numbers[0] if all_numbers else None

def save_attendance(student_id):
    """Log to CSV and prevent duplicates in the same minute."""
    filename = 'attendance_records.csv'
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    current_minute = now.strftime("%Y-%m-%d %H:%M")
    
    new_entry = pd.DataFrame([[student_id, timestamp]], columns=['Student_ID', 'Timestamp'])
    
    if os.path.isfile(filename):
        df_existing = pd.read_csv(filename)
        # Check if ID already exists in the current minute
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

# --- Main Application Logic ---

# Step 1: Camera Input
st.subheader("📸 Step 1: Scan ID Card")
picture = st.camera_input("Position the card clearly in the frame")

if picture:
    pil_img = Image.open(picture)
    img_array = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    with st.spinner('🔍 Analyzing context and searching for ID...'):
        processed_img = pre_process_image(img_bgr)
        # Try to read both English and Arabic if data files are present
        try:
            extracted_text = pytesseract.image_to_string(processed_img, lang='eng+ara', config='--psm 6')
        except:
            extracted_text = pytesseract.image_to_string(processed_img, lang='eng', config='--psm 6')
        
        # Step 2: Use Context Logic to find the right number
        student_id = extract_id_with_context(extracted_text)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.image(img_bgr, channels="BGR", caption="Original Captured Image")

    with col2:
        st.subheader("🎯 System Detection")
        if student_id:
            st.success(f"**Identified ID:** {student_id}")
            
            # Step 3: Save Record
            log_time, success = save_attendance(student_id)
            
            if success:
                st.info(f"✅ Registered at: {log_time}")
                st.balloons()
            else:
                st.warning("⚠️ Already logged in the last minute.")
            
            if st.button("➕ Add Another Person"):
                st.rerun()
        else:
            st.error("❌ Could not find an ID (e.g., Code, ID, Number).")
            with st.expander("Show Raw OCR Result"):
                st.text(extracted_text)

# --- Step 4: History & Export ---
if os.path.isfile('attendance_records.csv'):
    st.divider()
    st.subheader("📋 Today's Attendance Log")
    df_log = pd.read_csv('attendance_records.csv')
    
    st.dataframe(df_log.iloc[::-1], use_container_width=True)
    
    csv_data = df_log.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Attendance Report",
        data=csv_data,
        file_name='attendance_report.csv',
        mime='text/csv',
    )