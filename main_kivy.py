import cv2
import os
import datetime
import math
import serial
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window


class AeriCamApp(App):
    def build(self):
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print("Error: Could not open webcam.")
            exit()

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Set up serial connection to Arduino
        self.serial_conn = serial.Serial('COM3', 9600)

        # Global variables
        self.recording = False
        self.paused = False
        self.last_roll_value = "0"
        self.last_angle = 0
        self.recording_start_time = None
        self.pause_start_time = None
        self.total_pause_duration = datetime.timedelta()

        # Set up layout
        self.root = BoxLayout(orientation='vertical')
        self.image = Image()
        self.root.add_widget(self.image)

        # Buttons
        button_layout = BoxLayout(size_hint=(1, 0.1))
        self.photo_button = Button(text="Capture Photo")
        self.photo_button.bind(on_press=self.capture_photo_callback)
        button_layout.add_widget(self.photo_button)

        self.video_button = Button(text="Start Video")
        self.video_button.bind(on_press=self.start_video_recording_callback)
        button_layout.add_widget(self.video_button)

        self.pause_button = Button(text="Pause Video")
        self.pause_button.bind(on_press=self.pause_video_recording_callback)
        button_layout.add_widget(self.pause_button)

        self.gallery_button = Button(text="Open Gallery")
        self.gallery_button.bind(on_press=self.open_gallery)
        button_layout.add_widget(self.gallery_button)

        self.root.add_widget(button_layout)

        # Start updating the video feed
        Clock.schedule_interval(self.update, 1.0 / 30.0)

        return self.root

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.resize(frame, (1280, 720))

            # Read Roll value from serial
            roll_value = self.last_roll_value
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8').strip()
                if line.startswith("roll ="):
                    parts = line.split(',')
                    roll_value = parts[0].split('=')[1].strip()
                    self.last_roll_value = roll_value

            # Draw radar
            self.draw_radar(frame, roll_value)

            # Display the current date and time
            now = datetime.datetime.now()
            date_time_str = now.strftime("%d/%m/%Y - %H:%M:%S")
            cv2.putText(frame, date_time_str, (frame.shape[1] - 360, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

            # Timer logic
            if self.recording:
                if self.paused:
                    elapsed_time = self.pause_start_time - self.recording_start_time - self.total_pause_duration
                else:
                    elapsed_time = now - self.recording_start_time - self.total_pause_duration
                minutes, seconds = divmod(int(elapsed_time.total_seconds()), 60)
                hours, minutes = divmod(minutes, 60)
                timer_text = f"{hours:02}:{minutes:02}:{seconds:02}"
                cv2.putText(frame, timer_text, (frame.shape[1] // 2 - 50, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)  # Timer in red

                if not self.paused:
                    # Write frame to video output without color conversion
                    self.out.write(frame)

            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.image.texture = texture

    def draw_radar(self, frame, roll_value):
        min_radius = min(frame.shape[1], frame.shape[0]) // 8

        # Calculate the radar angle
        target_angle = (90 - float(roll_value)) % 360
        target_angle_rad = math.radians(target_angle)

        # Calculate the shortest path for angle interpolation
        angle_difference = (target_angle - self.last_angle + 180) % 360 - 180

        # Smooth transition
        self.last_angle += angle_difference * 0.1
        self.last_angle %= 360

        angle_rad = math.radians(self.last_angle)
        center = (frame.shape[1] - min_radius - 20, min_radius + 20)
        radar_x = int(center[0] + min_radius * math.cos(angle_rad))
        radar_y = int(center[1] - min_radius * math.sin(angle_rad))
        cv2.line(frame, center, (radar_x, radar_y), (0, 0, 255), 2)  # Radar hand in red
        cv2.circle(frame, center, min_radius, (255, 255, 255), 2)
        cv2.line(frame, (center[0], center[1] - min_radius), (center[0], center[1] + min_radius), (255, 255, 255), 1)
        cv2.line(frame, (center[0] - min_radius, center[1]), (center[0] + min_radius, center[1]), (255, 255, 255), 1)

        cv2.putText(frame, f"Rotation Roll: {roll_value}", (center[0] - min_radius - 100, min_radius * 2 + 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    def capture_photo(self, frame, roll_value):
        # Draw the radar on the frame
        self.draw_radar(frame, roll_value)

        now = datetime.datetime.now()
        date_time_str = now.strftime("%d/%m/%Y - %H:%M:%S")
        cv2.putText(frame, date_time_str, (frame.shape[1] - 360, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        photo_path = os.path.join('Gallery', f'captured_image_{timestamp}.jpg')
        cv2.imwrite(photo_path, frame)
        print(f"Photo saved to {photo_path}")

    def capture_photo_callback(self, instance):
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.resize(frame, (1280, 720))
            self.capture_photo(frame, self.last_roll_value)
            self.photo_button.background_color = (0, 1, 0, 1)
            Clock.schedule_once(self.reset_photo_button_color, 0.1)

    def reset_photo_button_color(self, dt):
        self.photo_button.background_color = (1, 1, 1, 1)

    def start_video_recording(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = os.path.join('Gallery', f'captured_video_{timestamp}.avi')
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(video_path, fourcc, 20.0, (1280, 720))
        self.recording_start_time = datetime.datetime.now()
        self.total_pause_duration = datetime.timedelta()
        print(f"Started recording video: {video_path}")

    def start_video_recording_callback(self, instance):
        if not self.recording:
            self.recording = True
            self.start_video_recording()
            instance.text = "Stop Video"
        else:
            self.recording = False
            self.out.release()
            instance.text = "Start Video"
            print("Video recording stopped.")

    def pause_video_recording_callback(self, instance):
        if self.recording:
            if not self.paused:
                self.pause_start_time = datetime.datetime.now()
                self.paused = True
                instance.text = "Resume Video"
                print("Video recording paused.")
            else:
                pause_duration = datetime.datetime.now() - self.pause_start_time
                self.total_pause_duration += pause_duration
                self.paused = False
                instance.text = "Pause Video"
                print("Video recording resumed.")

    def open_gallery(self, instance):
        print("Opening gallery (this should be implemented with file browser in Android).")


if __name__ == '__main__':
    AeriCamApp().run()
