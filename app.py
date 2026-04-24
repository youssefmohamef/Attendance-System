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
st.markdown("Scan student IDs to log attendance in real-time.")
st.divider()

# --- OCR Engine Path Configuration ---
# Update this path based on your Tesseract installation directory
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    
# --- Helper Functions ---

def pre_process_image(img_array):
    """
    Apply image processing to improve OCR accuracy.
    Converts to grayscale, blurs to reduce noise, and applies Otsu's thresholding.
    """
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, processed_img = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return processed_img

def save_attendance(student_id):
    """
    Handles data logging to a CSV file.
    Includes logic to prevent duplicate entries within the same minute.
    """
    filename = 'attendance_records.csv'
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    current_minute = now.strftime("%Y-%m-%d %H:%M") # Used for duplicate checking
    
    new_entry = pd.DataFrame([[student_id, timestamp]], columns=['Student_ID', 'Timestamp'])
    
    # Check if file exists to either append or create new
    if os.path.isfile(filename):
        df_existing = pd.read_csv(filename)
        # Verify if this ID was already logged in the current minute
        is_duplicate = not df_existing[(df_existing['Student_ID'].astype(str) == str(student_id)) & 
                                     (df_existing['Timestamp'].str.contains(current_minute))].empty
        
        if not is_duplicate:
            new_entry.to_csv(filename, mode='a', header=False, index=False)
            return timestamp, True
        else:
            return timestamp, False # Entry ignored due to duplication
    else:
        new_entry.to_csv(filename, index=False)
        return timestamp, True

# --- Main Application Logic ---

# Step 1: Camera Input Component
st.subheader("📸 Step 1: Scan ID")
picture = st.camera_input("Point the camera at the ID card")

if picture:
    # Convert Streamlit's UploadedFile to OpenCV format
    pil_img = Image.open(picture)
    img_array = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    with st.spinner('Analyzing ID...'):
        # Step 2: Image Pre-processing and Text Extraction
        processed_img = pre_process_image(img_bgr)
        # Using PSM 6 (Assume a single uniform block of text) for better digit detection
        extracted_text = pytesseract.image_to_string(processed_img, config='--psm 6')
        
        # Step 3: Regex Pattern to find any numeric sequence
        id_pattern = re.findall(r'\d+', extracted_text)

    # UI Output Columns
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.image(img_bgr, channels="BGR", caption="Captured Image")

    with col2:
        st.subheader("🔍 Extraction Result")
        if id_pattern:
            # Taking the first detected number as the Primary ID
            student_id = id_pattern[0]
            st.info(f"**Detected ID:** {student_id}")
            
            # Step 4: Attempt to save the record
            log_time, success = save_attendance(student_id)
            
            if success:
                st.success(f"✅ Logged successfully at {log_time}")
                st.balloons()
            else:
                st.warning("⚠️ Already logged in the last minute.")
            
            # Action Button to reset camera for next user
            if st.button("➕ Scan Another Person"):
                st.rerun()
        else:
            st.error("❌ No ID detected. Please try again with better lighting.")

# --- Step 5: Data Visualization & Export ---
if os.path.isfile('attendance_records.csv'):
    st.divider()
    st.subheader("📋 Attendance Log (History)")
    df_log = pd.read_csv('attendance_records.csv')
    
    # Display the dataframe in reverse order (newest logs first)
    st.dataframe(df_log.iloc[::-1], use_container_width=True)
    
    # Download button for the final CSV report
    csv_data = df_log.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Full Attendance Sheet",
        data=csv_data,
        file_name='attendance_report.csv',
        mime='text/csv',
    )