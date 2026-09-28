# MicroPython for Arduino Nano ESP32

# Members: Cal Stewart, Kindah Qaissi, Meghan Tennant
# Program start date: 9.23.2026
# Last update: 9.23.2026
# Update desc: Replaced PWM Servo with 52Pi (28BYJ-48) Stepper Motor and ULN2003 driver
# AI use: Generated stepper step sequence math, motor control functions, and wiring guide

# GOAL: Move a 52Pi stepper motor 90 degrees forward on switch press, and 90 degrees back on release
# I: Momentary switch override (GPIO 5 / D2)
# O: 52Pi Stepper Motor via ULN2003 Driver (GPIO 6, 7, 8, 9), LED status indicator (GPIO 10)

# ================================================================= #
# Imports

import machine
import time

# Pin setup - Inputs

# Momentary switch with internal pull-up resistor (Active LOW)
mom_switch = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)

# Pin setup - Outputs

# LED Indicator
led = machine.Pin(10, machine.Pin.OUT)

# Stepper Motor Control Pins (ULN2003 Driver Pins IN1 - IN4)
in1 = machine.Pin(6, machine.Pin.OUT)
in2 = machine.Pin(7, machine.Pin.OUT)
in3 = machine.Pin(8, machine.Pin.OUT)
in4 = machine.Pin(9, machine.Pin.OUT)

stepper_pins = [in1, in2, in3, in4]

# ================================================================= #
# STEPPER MOTOR CONFIGURATION
# ================================================================= #
# The 52Pi 28BYJ-48 motor uses a 64:1 gear reduction ratio.
# Half-stepping (8-step sequence) provides smoother rotation and higher torque:
# - Full Revolution (360°) = ~4096 half-steps
# - 90 Degree Rotation     = 4096 * (90 / 360) = 1024 half-steps
# ================================================================= #

STEPS_90_DEG = 1024

HALFSTEP_SEQ = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]

def disable_motor():
    """De-energize all coils to save power and prevent motor overheating."""
    for pin in stepper_pins:
        pin.value(0)

def rotate_stepper(steps, direction=1, delay_ms=2):
    """
    Rotates the stepper motor by driving the 4 control pins through sequence steps.
    
    :param steps: Number of steps to move
    :param direction: 1 for clockwise (+90°), -1 for counter-clockwise (-90°)
    :param delay_ms: Time between step movements in ms (controls speed)
    """
    seq_len = len(HALFSTEP_SEQ)
    
    for step_num in range(steps):
        if direction > 0:
            step_idx = step_num % seq_len
        else:
            step_idx = (seq_len - 1) - (step_num % seq_len)
            
        pattern = HALFSTEP_SEQ[step_idx]
        for pin_idx in range(4):
            stepper_pins[pin_idx].value(pattern[pin_idx])
            
        time.sleep_ms(delay_ms)
        
    # Cut power to coils after movement completes
    disable_motor()

# ================================================================= #
# Main Execution

print("Starting 52Pi Stepper Motor Control (0° to 90°)...")
disable_motor()
previous_state = mom_switch.value()

while True:
    current_state = mom_switch.value()

    if current_state != previous_state:
        # Debounce delay
        time.sleep_ms(30)
        
        if mom_switch.value() == current_state:
            # Switch Depressed (Pin pulled LOW to GND)
            if current_state == 0:
                print("Switch Depressed -> Rotating +90°")
                led.value(1)
                rotate_stepper(STEPS_90_DEG, direction=1)
                
            # Switch Released (Pin pulled HIGH)
            else:
                print("Switch Released -> Returning -90°")
                rotate_stepper(STEPS_90_DEG, direction=-1)
                led.value(0)

            previous_state = current_state

    time.sleep_ms(20)