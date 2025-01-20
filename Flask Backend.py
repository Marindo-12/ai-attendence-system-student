from flask import Flask, request, jsonify, render_template
from deepface import DeepFace
import cv2
import os
import time
import openpyxl
import numpy as np
import base64
from io import BytesIO

app = Flask(__name__)  # Ensure 'app' is defined here

attendance_filename = r"C:\Users\admin\Desktop\FaceRecogAttendance\attendance.xlsx"
reference_images_path = r"C:\Users\admin\Desktop\FaceRecogAttendance\Images"
attendance_dict = {}

# Initialize Excel for attendance tracking
def initialize_excel(filename):
    if not os.path.exists(filename):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Attendance"
        sheet.append(["Name", "Date", "Time", "Status"])
        workbook.save(filename)

initialize_excel(attendance_filename)

# Load reference images
reference_images = {}
for file in os.listdir(reference_images_path):
    if file.endswith(".jpg") or file.endswith(".png"):
        name = os.path.splitext(file)[0].replace("_", " ")
        reference_images[name] = os.path.join(reference_images_path, file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})

    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"})

    try:
        # Save the uploaded image to a temporary file
        img_path = os.path.join("temp_image.png")
        file.save(img_path)

        # Perform face recognition
        results = DeepFace.find(img_path=img_path, db_path=reference_images_path, enforce_detection=False)

        if len(results) > 0:
            match = results[0].iloc[0]
            name = os.path.basename(match["identity"]).split(".")[0].replace("_", " ")

            # Save attendance to Excel
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S").split()
            row = [name, timestamp[0], timestamp[1], "Present"]
            save_to_excel(attendance_filename, row)

            # Convert the image to base64 string to send it back
            with open(img_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

            return jsonify({
                "status": "success",
                "message": f"Attendance marked for {name}",
                "image": img_base64  # Send the base64 image string
            })
        else:
            return jsonify({"status": "error", "message": "Face not recognized"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error: {str(e)}"})

def save_to_excel(filename, row):
    try:
        workbook = openpyxl.load_workbook(filename)
        sheet = workbook["Attendance"]
        sheet.append(row)
        workbook.save(filename)
    except Exception as e:
        print(f"Error saving to Excel: {e}")

if __name__ == '__main__':
    app.run(debug=True)
