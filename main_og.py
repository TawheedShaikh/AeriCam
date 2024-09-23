import tkinter as tk
from tkinter import *
import cv2
from PIL import Image, ImageTk
import os
import datetime
import webbrowser
import sys

def create_directories():
    if not os.path.exists('Gallery'):
        os.makedirs('Gallery')

def initialize_webcam():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        sys.exit()
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap

def capture_photo(frame):
    now = datetime.datetime.now()
    date_time_str = now.strftime("%d/%m/%Y - %H:%M:%S")
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    font_thickness = 2
    text_size, _ = cv2.getTextSize(date_time_str, font, font_scale, font_thickness)
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = frame.shape[0] - 10
    cv2.putText(frame, date_time_str, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    photo_path = os.path.join('Gallery', f'captured_image_{timestamp}.jpg')
    cv2.imwrite(photo_path, frame)
    print(f"Photo saved to {photo_path}")

def start_video_recording():
    global out, recording_start_time
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join('Gallery', f'captured_video_{timestamp}.avi')
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    frame_width = 1280
    frame_height = 720
    out = cv2.VideoWriter(video_path, fourcc, 20.0, (frame_width, frame_height))
    recording_start_time = datetime.datetime.now()
    print(f"Started recording video: {video_path}")

def show_frame():
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (1280, 720))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        now = datetime.datetime.now()
        date_time_str = now.strftime("%d/%m/%Y - %H:%M:%S")
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        font_thickness = 2
        text_size, _ = cv2.getTextSize(date_time_str, font, font_scale, font_thickness)
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = frame.shape[0] - 10
        cv2.putText(frame, date_time_str, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)

        if recording:
            elapsed_time = datetime.datetime.now() - recording_start_time
            minutes, seconds = divmod(int(elapsed_time.total_seconds()), 60)
            hours, minutes = divmod(minutes, 60)
            timer_text = f"{hours:02}:{minutes:02}:{seconds:02}"
            timer_text_size, _ = cv2.getTextSize(timer_text, font, font_scale, font_thickness)
            timer_text_x = frame.shape[1] - timer_text_size[0] - 10
            timer_text_y = frame.shape[0] - 10
            cv2.putText(frame, timer_text, (timer_text_x, timer_text_y), font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)

        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        rt.imgtk = imgtk
        rt.configure(image=imgtk)
        if recording:
            out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    root.after(10, show_frame)

def capture_photo_callback():
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (1280, 720))
        capture_photo(frame)
        photo_button.config(bg='green')
        root.after(500, lambda: photo_button.config(bg='white'))

def start_video_recording_callback():
    global recording
    if not recording:
        start_video_recording()
        recording = True
        video_button.config(image=stop_recording_img, bg='red', fg='white', relief=SUNKEN)
        update_timer()
    else:
        out.release()
        recording = False
        video_button.config(image=start_recording_img, bg='white', fg='black', relief=RAISED)
        timer_label.config(text="00:00:00")
        print("Stopped recording video.")

def load_image(image_path, size):
    try:
        image = Image.open(image_path)
        image = image.resize((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)
    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
        return None

def update_timer():
    if recording:
        elapsed_time = datetime.datetime.now() - recording_start_time
        minutes, seconds = divmod(int(elapsed_time.total_seconds()), 60)
        hours, minutes = divmod(minutes, 60)
        timer_text = f"{hours:02}:{minutes:02}:{seconds:02}"
        timer_label.config(text=timer_text)
        root.after(1000, update_timer)

def open_gallery():
    webbrowser.open('file://' + os.path.realpath('Gallery'))

create_directories()
cap = initialize_webcam()
recording = False
recording_start_time = None

root = tk.Tk()
root.title("AeriCam")
root.state('zoomed')
root.configure(bg='black')
root.resizable(True, True)

# Canvas for video feed and buttons
canvas = Canvas(root, bg='black')
canvas.pack(fill=BOTH, expand=YES)

# Video feed label
rt = Label(canvas, bg='black')
rt.place(relwidth=1, relheight=1)  # Full size of the canvas

# Load images for buttons
photo_button_img = load_image('photo_button.png', 48)
start_recording_img = load_image('video_button.png', 48)
stop_recording_img = load_image('stop_button.png', 48)

if photo_button_img is None or start_recording_img is None or stop_recording_img is None:
    print("Error loading images.")
    root.destroy()
    sys.exit()

# Buttons overlay
button_frame = Frame(canvas, bg='black', bd=0, highlightthickness=0)
button_frame.place(relx=0.95, rely=0.5, anchor=CENTER)  # Center-right vertically

photo_button = Button(button_frame, image=photo_button_img, command=capture_photo_callback, bg='white', bd=0, relief=RAISED)
photo_button.pack(pady=10)  # Top button

video_button = Button(button_frame, image=start_recording_img, command=start_video_recording_callback, bg='white', bd=0, relief=RAISED)
video_button.pack(pady=10)  # Middle button

gallery_button = Button(button_frame, text="Gallery", command=open_gallery, bg='white', fg='black', bd=0, relief=RAISED)
gallery_button.pack(pady=10)  # Bottom button

show_frame()
root.mainloop()

if recording:
    out.release()
cap.release()
