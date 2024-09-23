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
            # Resize the frame to fit the screen
            frame = cv2.resize(frame, (self.screen_width, self.screen_height))
            # Convert the frame to RGB format
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

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
