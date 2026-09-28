# MicroPython for Arduino Nano ESP32
# Lehigh University - ENGR 095: Sensing the World
# Utility Script: Manual Stepper Positioning / Calibration

# GOAL: Slowly jog the 52Pi stepper motor forward while the momentary switch is held down.
# I: Momentary switch (GPIO 5 / D2)
# O: Stepper Motor (GPIO 6, 7, 8, 9), Status LED (GPIO 10)

# ================================================================= #
# Imports

import machine
import time

# ================================================================= #
# Hardware Configurations

# Momentary switch with internal pull-up resistor (Active LOW)
mom_switch = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)

# Status LED (turns ON while motor is actively jogging)
led = machine.Pin(10, machine.Pin.OUT)

# Stepper Motor Control Pins (ULN2003 Driver)
in1 = machine.Pin(6, machine.Pin.OUT)
in2 = machine.Pin(7, machine.Pin.OUT)
in3 = machine.Pin(8, machine.Pin.OUT)
in4 = machine.Pin(9, machine.Pin.OUT)

stepper_pins = [in1, in2, in3, in4]

# Half-step sequence pattern (28BYJ-48 stepper motor)
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

# Adjust this value to change speed:
# Higher value (e.g., 15-20 ms) = Slower, more precise movement
# Lower value  (e.g., 3-5 ms)   = Faster movement
STEP_DELAY_MS = 10 

# ================================================================= #
# Helper Functions

def disable_motor():
    """De-energize all coils to save power and prevent motor overheating."""
    for pin in stepper_pins:
        pin.value(0)

def step_motor_once(step_index):
    """Applies a single step pattern to the motor driver pins."""
    pattern = HALFSTEP_SEQ[step_index]
    for pin_idx in range(4):
        stepper_pins[pin_idx].value(pattern[pin_idx])

# ================================================================= #
# Main Execution

print("--- ENGR 095 Stepper Calibration Mode ---")
print("Hold the switch (Pin D2) to slowly step the motor.")
print("Release the switch to stop and hold position.")

disable_motor()
led.value(0)

step_idx = 0  # Sequence position tracker

while True:
    # Switch pressed check (Active LOW: 0 = Pressed)
    if mom_switch.value() == 0:
        led.value(1)  # Turn LED on while moving
        
        # Advance sequence by 1 step
        step_idx = (step_idx + 1) % len(HALFSTEP_SEQ)
        step_motor_once(step_idx)
        
        # Controlled slow delay
        time.sleep_ms(STEP_DELAY_MS)
    else:
        # Switch released
        led.value(0)
        disable_motor()
        time.sleep_ms(20)  # Gentle polling delay when idle