import cv2
import tkinter as tk
from PIL import Image, ImageTk
import os
import datetime
import subprocess
import platform
import threading

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
        self.paused_time = None
        self.total_paused_duration = datetime.timedelta()
        self.recording_timer_label = None

        # Bind the Esc key to the close function
        self.window.bind('<Escape>', lambda e: self.close_app())

        # Bind the "P" key to capture an image
        self.window.bind('p', lambda e: self.capture_image())

        # Bind the "G" key to open the gallery
        self.window.bind('g', lambda e: self.open_gallery())

        # Bind the "V" key to toggle video recording
        self.window.bind('v', lambda e: self.toggle_recording())

        # Bind the "Space" key to pause/resume recording
        self.window.bind('<space>', lambda e: self.pause_or_resume_recording())

        # Get the screen width and height
        self.screen_width = self.window.winfo_screenwidth()
        self.screen_height = self.window.winfo_screenheight()

        # Open the default webcam
        self.video_source = 0
        self.vid = cv2.VideoCapture(self.video_source)

        # Get the width and height of the video source
        self.cam_width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create a canvas that can fit the screen size
        self.canvas = tk.Canvas(window, width=self.screen_width, height=self.screen_height)
        self.canvas.pack()

        # Button to close the application
        self.btn_close = tk.Button(window, text="Close", command=self.close_app)
        self.btn_close.pack(anchor=tk.CENTER, expand=True)

        self.delay = 15  # Delay for frame update
        self.update()  # Call the update method to display the video feed

        self.window.mainloop()

    def update(self):
        # Get a frame from the video source
        ret, frame = self.vid.read()
        if ret:
            # Preserve aspect ratio of the camera feed
            aspect_ratio = self.cam_width / self.cam_height
            new_width, new_height = self.screen_width, self.screen_height

            # Calculate the new dimensions to fit the screen while maintaining aspect ratio
            if self.screen_width / self.screen_height > aspect_ratio:
                new_width = int(self.screen_height * aspect_ratio)
            else:
                new_height = int(self.screen_width / aspect_ratio)

            # Resize the frame while maintaining aspect ratio
            frame = cv2.resize(frame, (new_width, new_height))
            # Convert the frame to RGB format
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

        if self.recording and not self.paused:
            self.update_timer()

        self.window.after(self.delay, self.update)

    def toggle_recording(self):
        if self.recording:
            # Stop recording
            self.recording = False
            self.recording_timer_label.place_forget()
            self.stop_video_recording()
        else:
            # Start recording
            self.recording = True
            self.paused = False
            self.recording_start_time = datetime.datetime.now()
            self.total_paused_duration = datetime.timedelta()
            self.recording_timer_label = tk.Label(self.window, text="00:00:00", fg="red", font=("Arial", 20), bg="black")
            self.recording_timer_label.place(x=self.screen_width // 2, y=20, anchor="n")
            self.start_video_recording()

    def pause_or_resume_recording(self):
        if self.recording:
            if not self.paused:
                # Pause recording
                self.paused = True
                self.paused_time = datetime.datetime.now()
            else:
                # Resume recording
                self.paused = False
                self.total_paused_duration += datetime.datetime.now() - self.paused_time
                self.paused_time = None

    def start_video_recording(self):
        # Create directory for saving videos
        os.makedirs("Gallery/Videos", exist_ok=True)

        # Generate a timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_filename = f"Gallery/Videos/captured_video_{timestamp}.mp4"

        # Define the codec and create a VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 'mp4v' is the codec for .mp4 files
        self.out = cv2.VideoWriter(self.video_filename, fourcc, 20.0, (self.cam_width, self.cam_height))

        # Start a separate thread to save video frames
        self.recording_thread = threading.Thread(target=self.record_video)
        self.recording_thread.start()

    def stop_video_recording(self):
        # Stop the recording thread
        self.out.release()
        print(f"Video saved as {self.video_filename}")

    def record_video(self):
        while self.recording:
            if not self.paused:
                ret, frame = self.vid.read()
                if ret:
                    self.out.write(frame)

    def update_timer(self):
        # Calculate the elapsed time excluding paused durations
        elapsed_time = datetime.datetime.now() - self.recording_start_time - self.total_paused_duration
        elapsed_str = str(elapsed_time).split('.')[0]  # Format to HH:MM:SS
        self.recording_timer_label.config(text=elapsed_str)

    def capture_image(self):
        # Capture the current frame and save it as an image
        if hasattr(self, 'current_frame'):
            # Create the directory if it doesn't exist
            os.makedirs("Gallery/Images", exist_ok=True)

            # Generate a timestamped filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Gallery/Images/captured_image_{timestamp}.jpg"

            # Convert the current frame to BGR format for saving
            save_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, save_frame)
            print(f"Image saved as {filename}")

    def open_gallery(self):
        # Open the gallery directory using the default file explorer
        gallery_path = os.path.abspath("Gallery")

        # Check the platform and open the folder
        if platform.system() == "Windows":
            os.startfile(gallery_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", gallery_path])
        else:  # Linux
            subprocess.Popen(["xdg-open", gallery_path])

    def close_app(self):
        # Release the video source when closing the application
        if self.vid.isOpened():
            self.vid.release()
        self.window.quit()

# Create a window and pass it to the CameraApp class
if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root, "Live Camera Feed - Fullscreen Mode")
