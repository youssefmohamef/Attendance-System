import numpy as np
import cv2
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import pytesseract 
import pandas as pd
import datetime
import os
import re

# --- UI Configuration ---
st.set_page_config(page_title="AI Live Attendance", layout="wide")
st.title('🆔 Smart Live Attendance System')

# --- Tesseract Path (Crucial) ---
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# --- Logic: Save to CSV ---
def save_attendance(student_id):
    filename = 'attendance_records.csv'
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    
    new_entry = pd.DataFrame([[student_id, timestamp]], columns=['Student_ID', 'Timestamp'])
    
    if os.path.isfile(filename):
        df_existing = pd.read_csv(filename)
        # Check if ID already scanned in the last 30 seconds to avoid spam
        last_minute = (now - datetime.timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M:%S")
        is_duplicate = not df_existing[(df_existing['Student_ID'].astype(str) == str(student_id)) & 
                                     (df_existing['Timestamp'] > last_minute)].empty
        if not is_duplicate:
            new_entry.to_csv(filename, mode='a', header=False, index=False)
            return True
        return False
    else:
        new_entry.to_csv(filename, index=False)
        return True

# --- Improved Video Processor ---
class AttendanceProcessor(VideoProcessorBase):
    def __init__(self):
        self.status = "Point camera at ID"

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # 1. Enhance Frame for OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Increase contrast
        enhanced = cv2.detailEnhance(gray, sigma_s=10, sigma_r=0.15)
        # Adaptive Thresholding (Better for changing light)
        processed = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # 2. OCR Detection
        # We use lang='eng' first for speed, add 'ara' if needed
        text = pytesseract.image_to_string(processed, config='--psm 6')
        
        # 3. Extract ID (Regex for 5+ digits)
        student_id = None
        # Look for the specific number pattern you have in the card
        found_ids = re.findall(r'\b\d{7,10}\b', text)
        
        if found_ids:
            student_id = found_ids[0]
            if save_attendance(student_id):
                self.status = f"✅ Saved: {student_id}"
            else:
                self.status = f"⚡ Already Logged: {student_id}"

        # 4. On-Screen Overlay
        cv2.rectangle(img, (0, 0), (400, 60), (0, 0, 0), -1)
        cv2.putText(img, self.status, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        return frame.from_ndarray(img, format="bgr24")

# --- Streamlit Layout ---
ctx = webrtc_streamer(
    key="attendance-live",
    video_processor_factory=AttendanceProcessor,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": True, "audio": False},
)

# Display Table
if os.path.isfile('attendance_records.csv'):
    st.subheader("📋 Live Records")
    df = pd.read_csv('attendance_records.csv')
    st.dataframe(df.iloc[::-1], use_container_width=True)
    
    if st.button("🗑️ Clear All"):
        os.remove('attendance_records.csv')
        st.rerun()