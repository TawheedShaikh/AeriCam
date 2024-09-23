import kivy
from kivy.app import App
from kivy.config import Config
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import cv2
import datetime
import os
import math
import serial

class AeriCamApp(App):
    def create_directories(self):
        """Creates the necessary directories for saving images and videos."""
        if not os.path.exists('Gallery'):
            os.makedirs('Gallery')

    def build(self):
        self.create_directories()  # Call the function to create directories

        btnlayout = BoxLayout(orientation='horizontal')
        videofeed = BoxLayout()

        close_button = Button(
            text='X',
            font_size=24,
            size_hint=(None, None),
            size=(25, 25),
            pos_hint={'center_x': 0.025, 'center_y': 0.975}
        )

        btnlayout.add_widget(close_button)

        # Add the video feed widget (for example, an Image widget)
        self.video_feed_image = Image()  # Placeholder for video feed
        videofeed.add_widget(self.video_feed_image)

        close_button.bind(on_press=self.closeApp)

        # Add videofeed to the main layout
        main_layout = BoxLayout(orientation='vertical')
        main_layout.add_widget(videofeed)
        main_layout.add_widget(btnlayout)

        return main_layout

    def closeApp(self, instance):
        self.stop()


if __name__ == '__main__':
    AeriCamApp().run()
