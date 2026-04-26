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

# --- إعدادات الواجهة ---
st.set_page_config(page_title="AI Attendance System", layout="wide")
st.title('🆔 Smart Attendance System')
st.markdown("Scan your ID card using the **Camera** or **Upload a Photo**.")

# 1. تهيئة Session State لمسح الصور عند الانتقال للطالب التالي
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# --- إعداد مسار محرك Tesseract ---
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# --- الدوال البرمجية ---

def pre_process_image(img_array):
    """تحسين الصورة لنتائج OCR أفضل."""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    # استخدام عتبة Otsu لتوضيح النص
    _, processed_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return processed_img

def extract_id_with_context(text):
    """منطق مخصص لقراءة 'كود الطالب' وتجاهل أرقام CMP"""
    lines = [line.strip() for line in text.lower().splitlines() if line.strip()]
    target_keywords = ['كود الطالب', 'student code', 'كود', 'code', "id number"]
    
    for i, line in enumerate(lines):
        if any(key in line for key in target_keywords):
            # بحث في نفس السطر
            numbers_same_line = re.findall(r'\b\d{5,}\b', line) 
            if numbers_same_line:
                return numbers_same_line[0]
            
            # بحث في السطر التالي
            if i + 1 < len(lines):
                next_line = lines[i+1]
                numbers_next_line = re.findall(r'\b\d{5,}\b', next_line)
                if numbers_next_line:
                    return numbers_next_line[0]
    
    all_long_numbers = re.findall(r'\b\d{7,}\b', text)
    if all_long_numbers:
        return all_long_numbers[-1]
        
    return None

def save_attendance(student_id):
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

# --- منطق الاختيار بين الكاميرا والرفع ---

st.subheader("📸 Step 1: Input Source")
input_mode = st.radio("Choose how to provide the ID image:", 
                       ("📷 Live Camera Scan", "📁 Upload Image from Device"), 
                       horizontal=True)

final_image_file = None

# استخدام المفتاح الديناميكي (st.session_state.uploader_key) لمسح الصورة
if input_mode == "📷 Live Camera Scan":
    final_image_file = st.camera_input("Take a photo of your ID", key=f"cam_{st.session_state.uploader_key}")
else:
    final_image_file = st.file_uploader("Select ID image...", type=['jpg', 'jpeg', 'png'], key=f"file_{st.session_state.uploader_key}")

if final_image_file:
    pil_img = Image.open(final_image_file)
    img_array = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    with st.spinner('🔍 Analyzing Image...'):
        processed_img = pre_process_image(img_bgr)
        try:
            extracted_text = pytesseract.image_to_string(processed_img, lang='eng+ara', config='--psm 6')
        except:
            extracted_text = pytesseract.image_to_string(processed_img, lang='eng', config='--psm 6')
        
        student_id = extract_id_with_context(extracted_text)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.image(img_bgr, channels="BGR", caption="Original Captured Image")

    with col2:
        st.subheader("🎯 Detection Result")
        if student_id:
            st.success(f"**Identified ID:** {student_id}")
            log_time, success = save_attendance(student_id)
            
            if success:
                st.info(f"✅ Registered at: {log_time}")
                st.balloons()
            else:
                st.warning("⚠️ Already logged in the last minute.")
            
            # عند الضغط على الزر، نقوم بزيادة المفتاح لمسح الواجهة
            if st.button("➕ Next Student"):
                st.session_state.uploader_key += 1
                st.rerun()
        else:
            st.error("❌ No ID found. Please try a clearer photo.")
            if st.button("🔄 Try Again"):
                st.session_state.uploader_key += 1
                st.rerun()

# --- الشريط الجانبي لإدارة السجلات ---
with st.sidebar:
    st.header("🧹 Manage Records")
    if st.button("⏪ Delete Last Entry"):
        if os.path.isfile('attendance_records.csv'):
            df = pd.read_csv('attendance_records.csv')
            if not df.empty:
                df = df[:-1].to_csv('attendance_records.csv', index=False)
                st.success("Last record deleted!")
                st.rerun()
    
    if st.button("🗑️ Clear All Records", type="primary"):
        if os.path.isfile('attendance_records.csv'):
            os.remove('attendance_records.csv')
            st.success("All records cleared!")
            st.rerun()

# --- عرض سجل الحضور ---
if os.path.isfile('attendance_records.csv'):
    st.divider()
    st.subheader("📋 Attendance Records (Select to Delete)")
    df_log = pd.read_csv('attendance_records.csv')
    
    edited_df = st.data_editor(
        df_log.iloc[::-1], 
        column_config={"Delete": st.column_config.CheckboxColumn("Select to Delete", default=False)},
        disabled=["Student_ID", "Timestamp"],
        use_container_width=True,
        key="attendance_editor"
    )

    if st.button("🗑️ Delete Selected Rows"):
        if "Delete" in edited_df.columns:
            remaining_df = edited_df[edited_df["Delete"] == False].drop(columns=["Delete"])
            remaining_df.iloc[::-1].to_csv('attendance_records.csv', index=False)
            st.success("Selected records deleted!")
            st.rerun()
    
    csv_data = df_log.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Report (CSV)", csv_data, "attendance.csv", "text/csv")