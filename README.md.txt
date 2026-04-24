 Smart AI Attendance System (OCR Based)

A professional Image-based Attendance System built with Python, Streamlit, and OpenCV. This application uses Optical Character Recognition (OCR) to extract student IDs from cards and logs their attendance into a CSV file with precise timestamps.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Features

Live Camera Capture: Uses the device's camera to take photos of ID cards instantly.

Robust OCR: Powered by Tesseract to extract any numeric sequence from the card.

Image Processing: Includes grayscale conversion, Gaussian blur, and Otsu's thresholding for high accuracy in low light.

Automated Logging: Saves records in a attendance_records.csv file automatically.

Live Dashboard: Shows the last 5 attendance entries in a table on the web interface.

 Tech Stack

Frontend: Streamlit

Image Processing: OpenCV

OCR Engine: PyTesseract

Data Handling: Pandas

Prerequisites

Before running the project, ensure you have:

Python 3.x installed.

2. Tesseract OCR installed on your machine.

Download it from here.

Note: Make sure to update the path in DocumentScanner.py:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

 Installation & Setup

Clone the repository:
git clone https://github.com/yourusername/attendance-system.git
cd attendance-system

2. Install required libraries:
pip install opencv-python streamlit pytesseract pandas pillow numpy

3. Run the application:
streamlit run app.py


 How it Works

Capture: The user places the ID card in front of the webcam and clicks "Take Photo".

Processing: The system enhances the image (Gray + Threshold) to make the text sharp.

Extraction: Tesseract scans the image, and Regex (\d+) picks up all numbers.

Logging: The first detected number is saved as the Student ID in attendance_records.csv with the current date and time.

Project Structure

DocumentScanner.py: The main application code.

attendance_records.csv: The database file where attendance is stored.

requirements.txt: List of dependencies.

Future Improvements

[ ] Prevent duplicate entries within the same hour.

[ ] Integration with SQLite or Firebase for more secure data storage.

[ ] Adding Student Names by mapping IDs to a master databa