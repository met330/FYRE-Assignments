# MicroPython for Arduino Nano ESP32
# Lehigh University - ENGR 095: Sensing the World

# Members: Cal Stewart, Kindah Qaissi, Meghan Tennant
# Program start date: 9.23.2026
# Last update: 9.28.2026
# Update desc: Inverted water module logic to Active-LOW (triggers when voltage drops below threshold)

# GOAL: Move 52Pi stepper motor 90 degrees forward on switch press OR water detection (Active LOW)
# I: Momentary switch (GPIO 5 / D2), Water module (GPIO 1 / A0)
# O: Stepper Motor (GPIO 6, 7, 8, 9), Status LED (GPIO 10)

# ================================================================= #
# Imports

import machine
from machine import ADC
import time

# Pin setup - Inputs

# Momentary switch with internal pull-up resistor (Active LOW)
mom_switch = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)

# Water module (ADC on Pin A0 / GPIO 1)
water = machine.Pin(1)
adc = ADC(water)
adc.atten(ADC.ATTN_11DB)  # Extends measurement range up to 3.3V

# Voltage & ADC Constants
MAX_ADC_VALUE = 65535  # MicroPython's 16-bit ADC scale (2^16 - 1)
MAX_VOLTAGE = 3.3      # Full-scale voltage reference in Volts

# Active-LOW Threshold: Trigger when voltage drops BELOW this value.
# (e.g., if dry reads ~3.0V, setting this to 1.5V will trigger when wet)
WATER_THRESHOLD_VOLTS = 1.5  

# Pin setup - Outputs
led = machine.Pin(10, machine.Pin.OUT)

# Stepper Motor Control Pins (ULN2003 Driver)
in1 = machine.Pin(6, machine.Pin.OUT)
in2 = machine.Pin(7, machine.Pin.OUT)
in3 = machine.Pin(8, machine.Pin.OUT)
in4 = machine.Pin(9, machine.Pin.OUT)

stepper_pins = [in1, in2, in3, in4]

# Stepper configuration (52Pi 28BYJ-48 motor)
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
        
    disable_motor()

# ================================================================= #
# WATER SENSOR FUNCTION
# ================================================================= #

def check_water_sensor():
    """
    Reads the water module ADC, calculates exact voltage using formula:
    voltage = (raw_value / MAX_ADC_VALUE) * MAX_VOLTAGE
    
    Returns a tuple: (is_detected, voltage, raw_value)
    Active-LOW Logic: Returns True when voltage drops BELOW threshold.
    """
    # Average 3 rapid readings to filter out electrical noise
    raw_sum = 0
    for _ in range(3):
        raw_sum += adc.read_u16()
        time.sleep_ms(2)
    
    raw_value = raw_sum / 3
    
    # Calculate measured voltage
    voltage = (raw_value / MAX_ADC_VALUE) * MAX_VOLTAGE
    
    # Inverted comparison: True when voltage drops BELOW threshold
    is_detected = voltage <= WATER_THRESHOLD_VOLTS
    
    return is_detected, voltage, raw_value

# ================================================================= #
# Main Execution

print("ENGR 095 System Running: Active-LOW Water Detection & Switch Override")
disable_motor()

is_active = False
debug_timer = time.ticks_ms()

while True:
    # Read inputs
    switch_pressed = (mom_switch.value() == 0)  # Active LOW switch
    water_detected, voltage, raw_value = check_water_sensor()
    
    # Combined OR trigger logic
    target_active_state = switch_pressed or water_detected

    # Print live telemetry every 500ms to assist with calibration
    if time.ticks_diff(time.ticks_ms(), debug_timer) > 500:
        print(f"Raw ADC: {int(raw_value):5d} | Voltage: {voltage:.3f}V | Switch: {mom_switch.value()} | Water Detected: {water_detected}")
        debug_timer = time.ticks_ms()

    # Trigger motor movement on state change
    if target_active_state != is_active:
        time.sleep_ms(30)  # Debounce delay
        
        # Re-verify inputs
        switch_pressed = (mom_switch.value() == 0)
        water_detected, voltage, raw_value = check_water_sensor()
        target_active_state = switch_pressed or water_detected
        
        if target_active_state != is_active:
            if target_active_state:
                source = "Switch" if switch_pressed else f"Water Sensor ({voltage:.2f}V)"
                print(f"-> ACTIVATED by {source}! Rotating +90°")
                led.value(1)
                rotate_stepper(STEPS_90_DEG, direction=1)
            else:
                print("-> CLEARED! Returning -90°")
                rotate_stepper(STEPS_90_DEG, direction=-1)
                led.value(0)

            is_active = target_active_state

    time.sleep_ms(20)