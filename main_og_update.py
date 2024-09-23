import tkinter as tk
from tkinter import *
import cv2
from PIL import Image, ImageTk
import os
import datetime
import webbrowser
import sys
import serial
import math
import numpy as np

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

def capture_photo(frame, roll_value):
    # Draw the radar on the frame
    draw_radar(frame, roll_value)

    # Display Roll value below the radar circle
    font = cv2.FONT_HERSHEY_SIMPLEX
    radar_center_x = frame.shape[1] - min_radius - 20  # Adjust for top right placement
    text_y = min_radius * 2 + 40  # Adjust for radius and some padding
    cv2.putText(frame, f"Rotation Roll: {roll_value}", (radar_center_x - min_radius - 100, text_y), font, 0.8, (255, 0, 0), 2, cv2.LINE_AA)

    now = datetime.datetime.now()
    date_time_str = now.strftime("%d/%m/%Y - %H:%M:%S")
    font_scale = 0.8
    font_thickness = 2
    text_size, _ = cv2.getTextSize(date_time_str, font, font_scale, font_thickness)
    text_x = frame.shape[1] - text_size[0] - 10
    text_y = frame.shape[0] - 10
    cv2.putText(frame, date_time_str, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)

    # Save the photo
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    photo_path = os.path.join('Gallery', f'captured_image_{timestamp}.jpg')
    cv2.imwrite(photo_path, frame)
    print(f"Photo saved to {photo_path}")

def start_video_recording():
    global out, recording_start_time, pause_start_time, paused, total_pause_duration
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join('Gallery', f'captured_video_{timestamp}.avi')
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    frame_width = 1280
    frame_height = 720
    out = cv2.VideoWriter(video_path, fourcc, 20.0, (frame_width, frame_height))
    recording_start_time = datetime.datetime.now()
    total_pause_duration = datetime.timedelta()
    paused = False
    print(f"Started recording video: {video_path}")

# Global variables to store previous radar values
previous_angle_rad = None

def draw_radar(frame, roll_value):
    global min_radius, previous_angle_rad

    min_radius = min(frame.shape[1], frame.shape[0]) // 8  # Reduce radar size by half

    # Calculate the radar angle
    angle = (90 - float(roll_value)) % 360
    angle_rad = math.radians(angle)

    if previous_angle_rad is None:
        previous_angle_rad = angle_rad

    # Smooth transition between previous and current angles
    transition_speed = 0.1  # Adjust this value for smoother or more responsive transitions
    diff_angle_rad = angle_rad - previous_angle_rad
    diff_angle_rad = (diff_angle_rad + np.pi) % (2 * np.pi) - np.pi  # Normalize to [-π, π]
    smoothed_angle_rad = previous_angle_rad + transition_speed * diff_angle_rad

    # Update previous_angle_rad for the next frame
    previous_angle_rad = smoothed_angle_rad

    # Top right placement
    center = (frame.shape[1] - min_radius - 20, min_radius + 20)
    radar_x = int(center[0] + min_radius * math.cos(smoothed_angle_rad))
    radar_y = int(center[1] - min_radius * math.sin(smoothed_angle_rad))
    cv2.line(frame, center, (radar_x, radar_y), (255, 0, 0), 2)

    # Draw circle around the radar widget
    cv2.circle(frame, center, min_radius, (255, 255, 255), 2)

    # Draw perpendicular lines
    cv2.line(frame, (center[0], center[1] - min_radius), (center[0], center[1] + min_radius), (255, 255, 255), 1)  # Vertical line
    cv2.line(frame, (center[0] - min_radius, center[1]), (center[0] + min_radius, center[1]), (255, 255, 255), 1)  # Horizontal line

def show_frame():
    global last_roll_value, paused, total_pause_duration, pause_start_time
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (1280, 720))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Read Roll value from serial
        roll_value = last_roll_value
        if serial_conn.in_waiting > 0:
            line = serial_conn.readline().decode('utf-8').strip()
            print(f"Serial line read: {line}")  # Debug print
            if line.startswith("roll ="):
                parts = line.split(',')
                roll_value = parts[0].split('=')[1].strip()
                last_roll_value = roll_value  # Update last_roll_value to avoid flickering

        # Draw radar on the video frame
        draw_radar(frame, roll_value)

        # Display Roll value below the radar circle
        font = cv2.FONT_HERSHEY_SIMPLEX
        radar_center_x = frame.shape[1] - min_radius  # Adjust for top right placement
        text_y = min_radius * 2 + 50  # Adjust for radius and some padding
        cv2.putText(frame, f"Rotation Roll: {roll_value}", (radar_center_x - min_radius - 100, text_y), font, 0.8, (255, 0, 0), 2, cv2.LINE_AA)

        # Display the current date and time at the bottom right
        now = datetime.datetime.now()
        date_time_str = now.strftime("%d/%m/%Y - %H:%M:%S")
        font_scale = 0.8
        font_thickness = 2
        text_size, _ = cv2.getTextSize(date_time_str, font, font_scale, font_thickness)
        text_x = frame.shape[1] - text_size[0] - 10
        text_y = frame.shape[0] - 10
        cv2.putText(frame, date_time_str, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)

        if recording:
            if paused:
                elapsed_time = pause_start_time - recording_start_time - total_pause_duration
            else:
                elapsed_time = now - recording_start_time - total_pause_duration
            minutes, seconds = divmod(int(elapsed_time.total_seconds()), 60)
            hours, minutes = divmod(minutes, 60)
            timer_text = f"{hours:02}:{minutes:02}:{seconds:02}"
            cv2.putText(frame, timer_text, (frame.shape[1] // 2 - 50, 30), font, 0.8, (255, 0, 0), 2, cv2.LINE_AA)

            if not paused:
                # Write frame to video output
                out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        rt.imgtk = imgtk
        rt.configure(image=imgtk)

    root.after(10, show_frame)

def capture_photo_callback():
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (1280, 720))
        capture_photo(frame, last_roll_value)  # Pass last_roll_value to capture_photo
        photo_button.config(bg='green')
        root.after(500, lambda: photo_button.config(bg='white'))

def start_video_recording_callback():
    global recording
    if not recording:
        start_video_recording()
        recording = True
        video_button.config(image=stop_recording_img, bg='red', fg='white', relief=SUNKEN)
        pause_button.pack(pady=10)  # Show the pause button
    else:
        out.release()
        recording = False
        video_button.config(image=start_recording_img, bg='white', fg='black', relief=RAISED)
        pause_button.pack_forget()  # Hide the pause button
        print("Stopped recording video.")

def pause_video_recording_callback():
    global paused, pause_start_time, total_pause_duration
    if not paused:
        pause_start_time = datetime.datetime.now()
        paused = True
        pause_button.config(image=resume_button_img, bg='yellow', fg='black', relief=SUNKEN)
    else:
        pause_duration = datetime.datetime.now() - pause_start_time
        total_pause_duration += pause_duration
        paused = False
        pause_button.config(image=pause_button_img, bg='white', fg='black', relief=RAISED)

def load_image(image_path, size):
    try:
        image = Image.open(image_path)
        image = image.resize((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)
    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
        return None

def open_gallery():
    webbrowser.open('file://' + os.path.realpath('Gallery'))

# Initialize
create_directories()
cap = initialize_webcam()
recording = False
paused = False
recording_start_time = None
total_pause_duration = datetime.timedelta()

# Initialize serial connection to Arduino
serial_port = 'COM3'  # Replace with your Arduino port
baud_rate = 9600
serial_conn = serial.Serial(serial_port, baud_rate)

# Global variable to store last roll value
last_roll_value = "0"

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
photo_button_img = load_image(r'images\photo_button.png', 48)
start_recording_img = load_image(r'images\video_button.png', 48)
stop_recording_img = load_image(r'images\stop_button.png', 48)
pause_button_img = load_image(r'images\pause_button.png', 48)
resume_button_img = load_image(r'images\resume_button.png', 48)
gallery_button_img = load_image(r'images\gallery_button.png', 48)  # Load gallery button image

if photo_button_img is None or start_recording_img is None or stop_recording_img is None or pause_button_img is None or resume_button_img is None or gallery_button_img is None:
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

pause_button = Button(button_frame, image=pause_button_img, command=pause_video_recording_callback, bg='white', bd=0, relief=RAISED)

gallery_button = Button(button_frame, image=gallery_button_img, command=open_gallery, bg='white', bd=0, relief=RAISED)
gallery_button.pack(pady=10)  # Bottom button

show_frame()
root.mainloop()

if recording:
    out.release()
cap.release()
serial_conn.close()
