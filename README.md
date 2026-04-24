# Smart ID Attendance System

# An automated image-based attendance system built with Python, Streamlit, and OpenCV. The system captures student ID cards via webcam, extracts the ID number using OCR (Optical Character Recognition), and logs the attendance with a timestamp into a CSV database.

# 🚀Features
* # Live Camera Capture: Uses Streamlit's camera component for real-time scanning.
* # Context-Aware OCR: Smart logic to detect ID numbers whether they are located next to or below keywords like "ID", "Code", or "Student".
* # Image Pre-processing: Advanced OpenCV filters (Grayscale, Gaussian Blur, Adaptive Thresholding) to handle glare and low-light conditions.
* # Attendance Logging: Automatically saves records to attendance\_records.csv.
* # Anti-Duplicate Logic: Prevents the same ID from being logged multiple times within the same minute.
* # Data Export: Built-in button to download the full attendance report.
  
# 🛠️Tech Stack

* # Frontend: Streamlit
* # Image Processing: OpenCV
* # OCR Engine: Tesseract OCR
* # Data Handling: Pandas

# 📋Prerequisites

# Before running the application, ensure you have the following installed:

# 1.Python 3.8+

# 2.Tesseract OCR Engine:

* # Windows: Download and install from UB-Mannheim.
* # Linux: sudo apt install tesseract-ocr

# ⚙️Installation

# 1\. Clone the repository or create a new Python script `Attendance-System.py` and paste the provided code.

# 2\. Install the required dependencies using pip:
```bash
pip install numpy opencv-python streamlit pytesseract pillow pandas
```
# 3\. Configure Tesseract Path:

# Attendance-System.py and update the pytesseract.pytesseract.tesseract\_cmd path to point to your Tesseract executable.

# Usage

# Run the Streamlit app using the following command:
```bash
streamlit run app.py
```
# 📸How It Works

# 1\. Launch the application.
# 2\. Present the ID card to the webcam (Ensure the ID number is clearly visible).

# 3\. Click "Take Photo".

# 4\. The system will highlight the detected ID and save the entry to the log table below.

# 5\. Use the "Download Report" button to export the attendance data.

# 📝Notes

# - Lighting \& Glare:\*\* OCR performance is highly dependent on lighting. Avoid direct reflections (glare) on the ID card, as white spots can erase text details for the camera.

# - Tesseract Path:\*\* Ensure the `tesseract\\\_cmd` path in the script matches your actual installation directory (Default:
bush``` `C:\\\\Program Files\\\\Tesseract-OCR\\\\tesseract.exe`). ```
# - Language Support:\*\* The system is configured for (`eng+ara`). Ensure you have the Arabic language data file (`ara.traineddata`) installed in your Tesseract `tessdata` folder for Arabic keyword recognition.
# - CSV Locking:\*\* Close the `attendance\\\_records.csv` file in Excel before running the scan, as Excel may lock the file and prevent Python from writing new data.
# - Privacy:\*\* This application processes images locally. No images are stored on the disk; only extracted ID numbers and timestamps are saved.

# ⚖️License
# 1. This project is licensed under the \*\*MIT License\*\*.
# 2. Copyright (c) 2026 [Youssef Mohamed Abdalftah]
# 3. Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 4. The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 5. This project is provided “as is”, without any express or implied warranties, including but not limited to merchantability or fitness for a particular purpose. The authors shall not be held liable for any damages, claims, or other liabilities arising from the use of this software.

# Feel free to modify and enhance the project as per your requirements!

# 

