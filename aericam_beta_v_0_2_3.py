import cv2
import tkinter as tk
from PIL import Image, ImageTk
import os
import datetime
import subprocess
import platform
import threading
import queue

class CameraApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Set fullscreen mode
        self.window.attributes('-fullscreen', True)

        # Initialize recording state, pause state, and timer
        self.recording = False
        self.paused = False
        self.recording_start_time = None
        self.paused_duration = datetime.timedelta()
        self.recording_timer_label = None

        # Thread-safe queue for frames
        self.frame_queue = queue.Queue()

        # Bind the Esc key to the close function
        self.window.bind('<Escape>', lambda e: self.close_app())

        # Case-insensitive key bindings
        self.window.bind('p', lambda e: self.capture_image())
        self.window.bind('P', lambda e: self.capture_image())
        self.window.bind('g', lambda e: self.open_gallery())
        self.window.bind('G', lambda e: self.open_gallery())
        self.window.bind('v', lambda e: self.toggle_recording())
        self.window.bind('V', lambda e: self.toggle_recording())
        self.window.bind('<space>', lambda e: self.pause_or_resume_recording())

        # Get screen width and height
        self.screen_width = self.window.winfo_screenwidth()
        self.screen_height = self.window.winfo_screenheight()

        # Open the default webcam
        self.video_source = 0
        self.vid = cv2.VideoCapture(self.video_source)

        # Get the width and height of the video source
        self.cam_width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create a canvas that fits the screen size
        self.canvas = tk.Canvas(window, width=self.screen_width, height=self.screen_height)
        self.canvas.pack()

        # Button to close the application
        self.btn_close = tk.Button(window, text="Close", command=self.close_app)
        self.btn_close.pack(side=tk.BOTTOM, anchor=tk.S)

        self.delay = 15  # Delay for frame update
        self.update()  # Call the update method to display the video feed

        self.window.mainloop()

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            # Clear the canvas before drawing a new frame
            self.canvas.delete("all")

            # Preserve aspect ratio of the camera feed
            aspect_ratio = self.cam_width / self.cam_height
            new_width, new_height = self.screen_width, self.screen_height

            if self.screen_width / self.screen_height > aspect_ratio:
                new_width = int(self.screen_height * aspect_ratio)
            else:
                new_height = int(self.screen_width / aspect_ratio)

            # Resize the frame while maintaining aspect ratio
            frame = cv2.resize(frame, (new_width, new_height))

            # Add date and time overlay to the frame
            self.add_date_time_overlay(frame, new_width, new_height)

            # Convert the frame to RGB format for displaying
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))

            # Center the image on the canvas
            self.canvas.create_image(
                (self.screen_width - new_width) // 2,
                (self.screen_height - new_height) // 2,
                image=self.photo,
                anchor=tk.NW
            )

            # Store the frame for saving when "P" is pressed
            self.current_frame = frame

        if self.recording:
            self.update_timer()

        # Check for video capture failure
        if not ret:
            print("Failed to grab frame. Exiting...")
            self.close_app()
            return

        self.window.after(self.delay, self.update)

    def add_date_time_overlay(self, frame, new_width, new_height):
        current_time = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        font_scale = new_height / 720
        text_size = cv2.getTextSize(current_time, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
        text_x = new_width - text_size[0] - 10
        text_y = new_height - 10
        cv2.putText(frame, current_time, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2, cv2.LINE_AA)

    def toggle_recording(self):
        if self.recording:
            self.recording = False
            if self.recording_timer_label:
                self.recording_timer_label.place_forget()
            self.stop_video_recording()
        else:
            self.recording = True
            self.paused = False
            self.recording_start_time = datetime.datetime.now()
            self.paused_duration = datetime.timedelta()
            self.recording_timer_label = tk.Label(self.window, text="00:00:00", fg="red", font=("Arial", 20), bg="black")
            self.recording_timer_label.place(x=self.screen_width // 2, y=20, anchor="n")
            self.start_video_recording()

    def pause_or_resume_recording(self):
        if self.recording:
            if self.paused:
                # Resume recording
                self.paused_duration += datetime.datetime.now() - self.pause_start_time
                self.paused = False
            else:
                # Pause recording
                self.paused = True
                self.pause_start_time = datetime.datetime.now()

    def start_video_recording(self):
        os.makedirs("Gallery/Videos", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_filename = f"Gallery/Videos/captured_video_{timestamp}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(self.video_filename, fourcc, 20.0, (self.cam_width, self.cam_height))

        self.recording_thread = threading.Thread(target=self.record_video)
        self.recording_thread.start()

    def stop_video_recording(self):
        self.recording = False
        self.recording_thread.join()  # Ensure the recording thread has finished
        self.out.release()
        print(f"Video saved as {self.video_filename}")

    def record_video(self):
        while self.recording:
            if not self.paused:
                ret, frame = self.vid.read()
                if ret:
                    self.add_date_time_overlay(frame, self.cam_width, self.cam_height)
                    self.out.write(frame)

    def update_timer(self):
        if self.recording_start_time and not self.paused:
            # Only update timer if not paused
            elapsed_time = datetime.datetime.now() - self.recording_start_time - self.paused_duration
            elapsed_str = str(elapsed_time).split('.')[0]
            self.recording_timer_label.config(text=elapsed_str)
        elif self.paused:
            # Keep the timer showing the same paused time
            elapsed_time = self.pause_start_time - self.recording_start_time - self.paused_duration
            elapsed_str = str(elapsed_time).split('.')[0]
            self.recording_timer_label.config(text=elapsed_str)

    def capture_image(self):
        if hasattr(self, 'current_frame'):
            os.makedirs("Gallery/Images", exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Gallery/Images/captured_image_{timestamp}.jpg"
            save_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, save_frame)
            print(f"Image saved as {filename}")

    def open_gallery(self):
        gallery_path = os.path.abspath("Gallery")
        try:
            if platform.system() == "Windows":
                os.startfile(gallery_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", gallery_path])
            else:
                subprocess.Popen(["xdg-open", gallery_path])
        except Exception as e:
            print(f"Error opening gallery: {e}")

    def close_app(self):
        if self.vid.isOpened():
            self.vid.release()
        self.window.quit()

# Create a window and pass it to the CameraApp class
if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root, "Live Camera Feed - Fullscreen Mode")
