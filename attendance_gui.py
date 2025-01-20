import cv2
import os
from deepface import DeepFace
import openpyxl
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from threading import Thread
import traceback
import pygame  # For sound feedback

# Initialize sound
pygame.mixer.init()

def play_sound(file):
    try:
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing sound: {e}")

# Initialize Excel for attendance tracking
def initialize_excel(filename):
    try:
        if not os.path.exists(filename):
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Attendance"
            sheet.append(["Name", "Date", "Time", "Status"])
            workbook.save(filename)
            print(f"Excel file created at {filename}")
        else:
            print(f"Excel file already exists at {filename}")
    except Exception as e:
        print(f"Error initializing Excel file: {e}")
        traceback.print_exc()

def save_to_excel(filename, row):
    try:
        workbook = openpyxl.load_workbook(filename)
        sheet = workbook["Attendance"]
        sheet.append(row)
        workbook.save(filename)
        print(f"Row saved successfully: {row}")
    except Exception as e:
        print(f"Error saving to Excel: {e}")
        traceback.print_exc()

# Paths for Excel and reference images
attendance_filename = r"C:\Users\admin\Desktop\FaceRecogAttendance\attendance.xlsx"
initialize_excel(attendance_filename)

reference_images_path = r"C:\Users\admin\Desktop\FaceRecogAttendance\Images"
if not os.path.exists(reference_images_path):
    print(f"Error: The path {reference_images_path} does not exist.")
    exit()

# Load reference images
reference_images = {}
try:
    for file in os.listdir(reference_images_path):
        if file.endswith(".jpg") or file.endswith(".png"):
            name = os.path.splitext(file)[0].replace("_", " ")
            reference_images[name] = os.path.join(reference_images_path, file)
    print(f"Reference images loaded: {list(reference_images.keys())}")
except Exception as e:
    print(f"Error loading reference images: {e}")
    traceback.print_exc()

# Attendance tracking dictionary
attendance_dict = {}

# Start attendance function
def start_attendance(status_label, attendee_list):
    attendance_dict.clear()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        status_label.config(text="Error: Could not access the camera.", fg="red")
        return

    status_label.config(text="Camera opened. Starting attendance...", fg="blue")
    while True:
        ret, frame = cap.read()
        if not ret:
            status_label.config(text="Error: Could not read frame.", fg="red")
            break

        resized_frame = cv2.resize(frame, (640, 480))

        try:
            results = DeepFace.find(
                img_path=resized_frame,
                db_path=reference_images_path,
                enforce_detection=False,
                detector_backend="opencv",
            )

            if len(results) > 0:
                match = results[0].iloc[0]
                full_path = match["identity"]
                name = os.path.basename(full_path).split(".")[0].replace("_", " ")

                if name not in attendance_dict:
                    attendance_dict[name] = True
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S").split()
                    save_to_excel(attendance_filename, [name, timestamp[0], timestamp[1], "Present"])
                    play_sound(r"C:\Users\admin\Desktop\FaceRecogAttendance\FeedbackSoundsq")
                    attendee_list.insert(tk.END, f"{name} marked present at {timestamp[1]}\n")
                    status_label.config(text=f"Marked attendance for: {name}", fg="green")

                cv2.putText(frame, name, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Unknown", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        except Exception as e:
            print(f"Error during face recognition: {e}")
            traceback.print_exc()
            cv2.putText(frame, "Error", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("Face Recognition Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' to exit
            break

    cap.release()
    cv2.destroyAllWindows()
    status_label.config(text="Attendance process completed.", fg="blue")

def start_attendance_thread(status_label, attendee_list):
    attendance_thread = Thread(target=start_attendance, args=(status_label, attendee_list))
    attendance_thread.daemon = True
    attendance_thread.start()

# GUI Creation
root = tk.Tk()
root.title("Face Recognition Attendance System")
root.geometry("800x600")
root.config(bg="#f5f5f5")

# Header
header_frame = tk.Frame(root, bg="#3b3b3b", padx=20, pady=20)
header_frame.pack(fill=tk.X)

header_label = tk.Label(
    header_frame,
    text=" Face Recognition Attendance System",
    font=("Helvetica", 20, "bold"),
    fg="white",
    bg="#3b3b3b",
)
header_label.pack()

# Status Label
status_label = tk.Label(root, text="System ready. Press 'Start' to begin.", font=("Helvetica", 14), bg="#f5f5f5", fg="black")
status_label.pack(pady=20)

# Real-time Attendance Display
attendee_frame = tk.Frame(root, bg="#f5f5f5")
attendee_frame.pack(pady=10, fill=tk.BOTH, expand=True)

attendee_label = tk.Label(attendee_frame, text="Attendance List:", font=("Helvetica", 14), bg="#f5f5f5", anchor="w")
attendee_label.pack(fill=tk.X, padx=10, pady=5)

attendee_list = scrolledtext.ScrolledText(attendee_frame, font=("Helvetica", 12), height=15, wrap=tk.WORD)
attendee_list.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

# Buttons
button_frame = tk.Frame(root, bg="#f5f5f5")
button_frame.pack(pady=20)

start_button = ttk.Button(button_frame, text="Start Attendance", command=lambda: start_attendance_thread(status_label, attendee_list))
start_button.grid(row=0, column=0, padx=10, pady=10)

exit_button = ttk.Button(button_frame, text="Exit", command=root.quit)
exit_button.grid(row=0, column=1, padx=10, pady=10)

# Footer
footer_label = tk.Label(
    root, text="© 2025  Face Recognition Attendance System", font=("Helvetica", 10), bg="#f5f5f5", fg="#333"
)
footer_label.pack(side=tk.BOTTOM, pady=10)

root.mainloop()
