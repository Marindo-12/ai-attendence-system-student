# face-recognition-attendance-system
A Python-based Face Recognition Attendance System using DeepFace for facial recognition, OpenCV for webcam capture, and Openpyxl for Excel logging. The GUI is built with Tkinter. It enables real-time face detection and automated attendance tracking.
A Python-based Face Recognition Attendance System that uses DeepFace for facial recognition, OpenCV for webcam capture, and Openpyxl for logging attendance to an Excel sheet. The GUI is built with Tkinter, and Pygame provides sound feedback.

Features:
Real-time Face Recognition: Automatically detects and matches faces with pre-stored reference images.
Attendance Logging: Marks attendance and saves it to an Excel sheet.
Sound Feedback: Plays a sound when attendance is successfully marked.
User-Friendly GUI: Built using Tkinter for a simple and intuitive interface.
Technologies Used:
DeepFace for face recognition
OpenCV for webcam capture and image processing
Openpyxl for handling Excel files
Tkinter for GUI
Pygame for sound feedback
Installation:
Clone the repository:

bash
Copy
Edit
git clone https://github.com/your-username/FaceRecognitionAttendance.git
Install the required libraries:

bash
Copy
Edit
pip install deepface opencv-python openpyxl pygame
Place your reference images in the Images folder. Make sure each image filename is the person's name (e.g., John_Doe.jpg).

Run the main.py file:

bash
Copy
Edit
python main.py
How It Works:
The system captures video through your webcam.
It processes the video frames, recognizes faces, and matches them with the reference images.
When a match is found, attendance is logged with the current date and time in the attendance.xlsx file.
A sound is played for feedback.
Future Improvements:
Performance optimization for faster face recognition with larger datasets.
Real-time webcam integration for smoother attendance marking.
Error handling and additional user features.
