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

# --- إعداد مسار محرك Tesseract ---
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# --- الدوال البرمجية ---

def pre_process_image(img_array):
    """
    تحسين احترافي للصورة للتعامل مع الإضاءة القوية (Glare) 
    وتوضيح الأرقام الباهتة.
    """
    # 1. تحويل للرمادي
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    
    # 2. تقنية CLAHE لزيادة التباين وتوضيح الأرقام المختفية بسبب الإضاءة
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 3. إزالة الضوضاء (Noise) مع الحفاظ على حدة الأرقام
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
    
    # 4. تحويل لأسود وأبيض نقي باستخدام Otsu's Thresholding
    _, processed_img = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return processed_img

def extract_id_with_context(text):
    """
    منطق بحث دقيق جداً:
    يبحث عن الكلمة المفتاحية أولاً، ثم يسحب الرقم "الوحيد" المرتبط بها 
    بدلاً من سحب أي رقم طويل عشوائي من الكارنيه.
    """
    # كلمات البحث الأساسية في كارنيهات الجامعات المصرية
    keywords = ['رقم الطالب', 'كود الطالب', 'student code', 'id number', 'رقم الكارنيه']
    
    lines = [line.strip() for line in text.lower().splitlines() if line.strip()]
    
    for i, line in enumerate(lines):
        for key in keywords:
            if key in line:
                # 1. جرب البحث في نفس السطر (بجانب الكلمة)
                numbers = re.findall(r'\d+', line)
                if numbers:
                    for num in numbers:
                        if len(num) >= 4: return num # الأرقام الجامعية غالباً > 4 خانات
                
                # 2. جرب البحث في السطر التالي مباشرة (أسفل الكلمة)
                if i + 1 < len(lines):
                    next_line = lines[i+1]
                    numbers_next = re.findall(r'\d+', next_line)
                    if numbers_next:
                        for num in numbers_next:
                            if len(num) >= 4: return num
                            
    # إذا فشل البحث السياقي، ابحث عن أطول رقم في الصفحة (غالباً هو الـ ID)
    fallback = re.findall(r'\d{7,15}', text) # ابحث عن رقم طوله بين 7 لـ 15 خانة
    return fallback[0] if fallback else None

def save_attendance(student_id):
    """حفظ السجل في ملف CSV ومنع التكرار في نفس الدقيقة"""
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
# إنشاء أزرار اختيار لاختيار المصدر
input_mode = st.radio("Choose how to provide the ID image:", 
                       ("📷 Live Camera Scan", "📁 Upload Image from Device"), 
                       horizontal=True)

final_image_file = None

if input_mode == "📷 Live Camera Scan":
    final_image_file = st.camera_input("Take a photo of your ID")
else:
    # زر رفع الملف من الجهاز
    final_image_file = st.file_uploader("Select ID image from your device...", type=['jpg', 'jpeg', 'png'])

# معالجة الصورة في حال تم توفيرها بأي من الطريقتين
if final_image_file:
    pil_img = Image.open(final_image_file)
    img_array = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    with st.spinner('🔍 Analyzing Image...'):
        processed_img = pre_process_image(img_bgr)
        try:
            # القراءة باللغتين العربية والإنجليزية
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
            
            if st.button("➕ Next Student"):
                st.rerun()
        else:
            st.error("❌ No ID found. Please try a clearer photo or avoid light glare.")
            with st.expander("Show what the AI saw (Debug)"):
                st.text(extracted_text)

# --- عرض سجل الحضور وتصديره ---
if os.path.isfile('attendance_records.csv'):
    st.divider()
    st.subheader("📋 Attendance Records")
    df_log = pd.read_csv('attendance_records.csv')
    st.dataframe(df_log.iloc[::-1], use_container_width=True)
    
    # تحويل البيانات لملف CSV قابل للتحميل
    csv_data = df_log.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Report (Excel/CSV)", csv_data, "attendance.csv", "text/csv")