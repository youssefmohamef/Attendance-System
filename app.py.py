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

st.set_page_config(page_title="AI Attendance System", layout="centered")
st.title('Smart Attendance System')
st.markdown("Capture your ID card to log your attendance automatically.")
st.divider()


# load pytesseract model
pytesseract.pytesseract.tesseract_cmd= r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Define a function to extract test from image
def pre_process_image(img_array):
    """Enhance image for better OCR results."""
    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    # Apply thresholding (Otsu's Binarization) to make text pop
    _, processed_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return processed_img

def save_attendance(student_id):
    """Save the ID and timestamp to a CSV file."""
    filename = 'attendance_records.csv'
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_entry = pd.DataFrame([[student_id, timestamp]], columns=['Student_ID', 'Timestamp'])
    
    if not os.path.isfile(filename):
        new_entry.to_csv(filename, index=False)
    else:
        new_entry.to_csv(filename, mode='a', header=False, index=False)
    return timestamp

# --- 3. Main Application Logic ---

# Live Camera Input
st.subheader("Step 1: Capture ID Card")
picture = st.camera_input("Place your ID card in front of the camera")

if picture:
    # Convert captured image to OpenCV format
    pil_img = Image.open(picture)
    img_array = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    with st.spinner('Processing Image...'):
        # Image Processing & OCR
        processed_img = pre_process_image(img_bgr)
        extracted_text = pytesseract.image_to_string(processed_img)

        # Extract numeric ID using Regex (looks for digits longer than 3 characters)
        id_pattern = re.findall(r'\d{4,}', extracted_text)

# --- 4. Display Results ---
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.image(img_bgr, channels="BGR", caption="Captured Image")

    with col2:
        st.subheader("System Results")
        if id_pattern:
            student_id = id_pattern[0]
            st.success(f"**ID Detected:** {student_id}")
            
            # Save to File
            try:
                log_time = save_attendance(student_id)
                st.info(f"**Status:** Logged successfully at {log_time}")
                st.balloons()
            except Exception as e:
                st.error(f"Error saving data: {e}")
        else:
            st.error("No valid ID detected. Please ensure the card is clear and well-lit.")
            st.info("Tip: Try to hold the card closer to the camera.")

# --- 5. Attendance Log Table ---
    if os.path.isfile('attendance_records.csv'):
        st.divider()
        st.subheader("📋 Recent Attendance Logs")
        df = pd.read_csv('attendance_records.csv')
        # Show last 5 entries
        st.table(df.tail(5))