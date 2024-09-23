import cv2
import tkinter as tk
from PIL import Image, ImageTk

class CameraApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Set fullscreen mode
        self.window.attributes('-fullscreen', True)

        # Bind the Esc key to the close function
        self.window.bind('<Escape>', lambda e: self.close_app())

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

        self.window.after(self.delay, self.update)

    def close_app(self):
        # Release the video source when closing the application
        if self.vid.isOpened():
            self.vid.release()
        self.window.quit()

# Create a window and pass it to the CameraApp class
if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root, "Live Camera Feed - Fullscreen Mode")
