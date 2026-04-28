import numpy as np
import cv2
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import pytesseract 
import datetime
import pandas as pd
import os
import re

# --- UI Configuration ---
st.set_page_config(page_title="AI Live Attendance", layout="wide")
st.title('🆔 Smart Live Attendance System')
st.markdown("Hold the ID card in front of the camera for **Automatic Detection**.")

# --- Tesseract OCR Path ---
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# --- Helper Functions ---

def save_attendance(student_id):
    """Logs the ID to CSV if not registered in the last minute."""
    filename = 'attendance_records.csv'
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    current_minute = now.strftime("%Y-%m-%d %H:%M")
    
    new_entry = pd.DataFrame([[student_id, timestamp]], columns=['Student_ID', 'Timestamp'])
    
    if os.path.isfile(filename):
        df_existing = pd.read_csv(filename)
        # Prevent duplicates for the same student within the same minute
        is_duplicate = not df_existing[(df_existing['Student_ID'].astype(str) == str(student_id)) & 
                                     (df_existing['Timestamp'].str.contains(current_minute))].empty
        if not is_duplicate:
            new_entry.to_csv(filename, mode='a', header=False, index=False)
            return True, timestamp
        return False, None
    else:
        new_entry.to_csv(filename, index=False)
        return True, timestamp

# --- Live Video Processor ---

class AttendanceProcessor(VideoProcessorBase):
    def __init__(self):
        self.last_id = None
        self.status = "Waiting for ID..."

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # 1. Image Pre-processing for OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # 2. Run OCR (English + Arabic)
        text = pytesseract.image_to_string(processed, lang='eng+ara', config='--psm 6')
        
        # 3. Extract ID Logic
        lines = text.lower().splitlines()
        student_id = None
        target_keywords = ['كود الطالب', 'student code', 'كود', 'code', "id number"]

        for i, line in enumerate(lines):
            if any(key in line for key in target_keywords):
                # Search same line
                nums = re.findall(r'\b\d{5,}\b', line)
                if nums: 
                    student_id = nums[0]
                    break
                # Search next line
                if i + 1 < len(lines):
                    nums_next = re.findall(r'\b\d{5,}\b', lines[i+1])
                    if nums_next: 
                        student_id = nums_next[0]
                        break

        # 4. Save if a new ID is detected
        if student_id and student_id != self.last_id:
            success, time_logged = save_attendance(student_id)
            if success:
                self.last_id = student_id
                self.status = f"✅ Registered: {student_id}"
        
        # 5. Draw Info on Video Feed
        cv2.putText(img, self.status, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return frame.from_ndarray(img, format="bgr24")

# --- Main App Logic ---

# Sidebar for controls
with st.sidebar:
    st.header("🧹 Data Management")
    if st.button("🗑️ Clear All Records", type="primary"):
        if os.path.isfile('attendance_records.csv'):
            os.remove('attendance_records.csv')
            st.rerun()

# Start Video Stream
ctx = webrtc_streamer(
    key="attendance-live",
    video_processor_factory=AttendanceProcessor,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": True, "audio": False},
)

# Display Attendance History
if os.path.isfile('attendance_records.csv'):
    st.divider()
    st.subheader("📋 Live Attendance History")
    df_log = pd.read_csv('attendance_records.csv')
    
    # Data Editor for individual deletion
    edited_df = st.data_editor(
        df_log.iloc[::-1], 
        column_config={"Delete": st.column_config.CheckboxColumn("Remove", default=False)},
        disabled=["Student_ID", "Timestamp"],
        use_container_width=True,
        key="editor"
    )

    if st.button("❌ Remove Selected Rows"):
        if "Delete" in edited_df.columns:
            final_df = edited_df[edited_df["Delete"] == False].drop(columns=["Delete"])
            final_df.iloc[::-1].to_csv('attendance_records.csv', index=False)
            st.rerun()