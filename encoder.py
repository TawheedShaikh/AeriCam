import pigpio
import time

ENCODER_A_PIN = 17
ENCODER_B_PIN = 27

encoder_position = 0
last_state = 0


def encoder_callback(gpio, level, tick):
    global encoder_position, last_state
    state_a = pi.read(ENCODER_A_PIN)
    state_b = pi.read(ENCODER_B_PIN)

    if state_a != last_state:
        if state_b != state_a:
            encoder_position += 1  # Clockwise
        else:
            encoder_position -= 1  # Counterclockwise
        last_state = state_a


# Connect to pigpio daemon
pi = pigpio.pi()

# Setup the encoder pins with pigpio
pi.set_mode(ENCODER_A_PIN, pigpio.INPUT)
pi.set_pull_up_down(ENCODER_A_PIN, pigpio.PUD_UP)
pi.set_mode(ENCODER_B_PIN, pigpio.INPUT)
pi.set_pull_up_down(ENCODER_B_PIN, pigpio.PUD_UP)

# Add callback for the A pin
pi.callback(ENCODER_A_PIN, pigpio.EITHER_EDGE, encoder_callback)

try:
    while True:
        print(f"Encoder Position: {encoder_position}")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Program interrupted by user.")
finally:
    pi.stop()
1