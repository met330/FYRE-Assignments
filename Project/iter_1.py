# MicroPython for Arduino Nano/ESP32

# Members: Cal Stewart, Kindah Qaissi, Meghan Tennant
# Program start date: 9.23.2026
# Last update: 9.23.2026
# AI use: Reference wiring diagram, find numbers/program for moving servo

# GOAL: Create a program that moves a servo 90 degrees (ideally)
# I: Water sensor (sensitivity: V) + the masked module, switch override
# O: Servo activation, LED sensor 

# ================================================================= #
# Import

import machine # PIN, PWM
import time # sleep

# Pin setup - I

# Momentary switch w/ pull up resist - D2 (GPIO 5)
mom_switch = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)

# Pin setup - O

# Servo - D3, (GPIO 6) @ 50 Hertz
servo = machine.PWM(machine.Pin(6))
servo.freq(50)

# ================================================================= #
# Main

# ==============================================================================
# PWM CALIBRATION VALUES (16-bit resolution: 0 - 65535)
# Frequency = 50Hz (20ms period)
# - 0 degrees  => ~0.5ms pulse = (0.5 / 20) * 65535 = 1638 duty
# - 90 degrees => ~1.45ms pulse = Midpoint of 1638 and 7864 = 4751 duty
# ==============================================================================
DUTY_0_DEG = 1638
DUTY_90_DEG = 4751

# Start at 0 degrees
servo.duty_u16(DUTY_0_DEG)

print("Starting Servo Test (0° to 90°)...")
previous_state = mom_switch.value()

while True:
    current_state = mom_switch.value()

    if current_state != previous_state:
        # Small debounce delay to prevent rapid switch flickering
        time.sleep_ms(30)
        
        if mom_switch.value() == current_state:
            # Switch Depressed (Pin pulled LOW to GND)
            if current_state == 0:
                print("Switch Depressed -> Moving to 90°")
                servo.duty_u16(DUTY_90_DEG)
                
            # Switch Released (Pin pulled HIGH)
            else:
                print("Switch Released -> Returning to 0°")
                servo.duty_u16(DUTY_0_DEG)

            previous_state = current_state

    time.sleep_ms(20)