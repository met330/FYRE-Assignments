# MicroPython for Arduino Nano ESP32
# Lehigh University - ENGR 095: Sensing the World

# Members: Cal Stewart, Kindah Qaissi, Meghan Tennant
# Program start date: 9.23.2026
# Last update: 9.28.2026
# Update desc: Added Ohmmeter sensor on Pin A1 (GPIO 2) to trigger stepper when Rx < 1.4 kΩ
# AI use: Integrated resistance measure to full program

# GOAL: Move 52Pi stepper motor 90 degrees forward on switch press, water detection (Active LOW), 
#       OR low resistance measurement (< 1.4 kΩ).
# I: Momentary switch (GPIO 5 / D2), Water module (GPIO 1 / A0), Ohmmeter Probe (GPIO 2 / A1)
# O: Stepper Motor (GPIO 6, 7, 8, 9), Status LED (GPIO 10)

# ================================================================= #
# Imports

import machine
from machine import ADC
import time

# ================================================================= #
# Pin Setup & ADC Configurations

# Momentary switch with internal pull-up resistor (Active LOW)
mom_switch = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)

# Water module (ADC on Pin A0 / GPIO 1)
water_pin = machine.Pin(1)
water_adc = ADC(water_pin)
water_adc.atten(ADC.ATTN_11DB)  # Extends measurement range up to 3.3V

# Resistance module / Ohmmeter Probe 1 (ADC on Pin A1 / GPIO 2)
ohm_pin = machine.Pin(2)
ohm_adc = ADC(ohm_pin)
ohm_adc.atten(ADC.ATTN_11DB)    # Extends measurement range up to 3.3V

# Voltage & Sensor Constants
MAX_ADC_VALUE = 65535  # MicroPython's 16-bit ADC scale (2^16 - 1)
MAX_VOLTAGE = 3.3      # Full-scale voltage reference in Volts

# Threshold Settings
WATER_THRESHOLD_VOLTS = 1.5      # Trigger when water voltage drops BELOW 1.5V
R1_REF_OHMS = 220.0            # Known reference resistor (10 kΩ)
RESISTANCE_THRESHOLD_OHMS = 1400.0  # Trigger when Rx falls BELOW 1.4 kΩ (1400 Ω)

# Output Pins Setup
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

# ================================================================= #
# Helper Functions

def disable_motor():
    """De-energize all coils to save power and prevent motor overheating."""
    for pin in stepper_pins:
        pin.value(0)

def rotate_stepper(steps, direction=1, delay_ms=2):
    """Rotates the stepper motor by driving the 4 control pins through sequence steps."""
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
# SENSOR READING FUNCTIONS
# ================================================================= #

def check_water_sensor():
    """
    Reads the water module ADC and calculates voltage.
    Returns: (is_detected, voltage, raw_value)
    """
    raw_sum = 0
    for _ in range(3):
        raw_sum += water_adc.read_u16()
        time.sleep_ms(2)
    
    raw_value = raw_sum / 3
    voltage = (raw_value / MAX_ADC_VALUE) * MAX_VOLTAGE
    is_detected = voltage <= WATER_THRESHOLD_VOLTS
    
    return is_detected, voltage, raw_value

def check_ohmmeter_sensor():
    """
    Reads the voltage on Pin A1 and uses the voltage divider formula 
    to calculate unknown resistance Rx: Rx = R1 * (Vout / (Vin - Vout))
    
    Returns: (is_detected, resistance_ohms, measured_volts)
    """
    raw_sum = 0
    for _ in range(3):
        raw_sum += ohm_adc.read_u16()
        time.sleep_ms(2)
        
    raw_value = raw_sum / 3
    v_out = (raw_value / MAX_ADC_VALUE) * MAX_VOLTAGE
    
    # Check for open circuit (Probes disconnected / no current flow)
    if v_out >= (MAX_VOLTAGE - 0.05):
        return False, float('inf'), v_out
    
    # Calculate resistance Rx
    r_x = R1_REF_OHMS * (v_out / (MAX_VOLTAGE - v_out))
    
    # Trigger active state if resistance falls below 1.4 kΩ (1400 Ω)
    is_detected = r_x < RESISTANCE_THRESHOLD_OHMS
    
    return is_detected, r_x, v_out

# ================================================================= #
# Main Execution

print("ENGR 095 System Running: Switch, Water & Resistance Detection")
disable_motor()

is_active = False
debug_timer = time.ticks_ms()

while True:
    # 1. Read all three input triggers
    switch_pressed = (mom_switch.value() == 0)
    water_detected, w_volts, w_raw = check_water_sensor()
    ohm_detected, resistance, o_volts = check_ohmmeter_sensor()
    
    # 2. Combined OR trigger logic
    target_active_state = switch_pressed or water_detected or ohm_detected

    # 3. Print live telemetry every 500ms
    if time.ticks_diff(time.ticks_ms(), debug_timer) > 500:
        res_str = "OPEN" if resistance == float('inf') else f"{resistance:.1f} Ω"
        print(f"Water: {w_volts:.2f}V | Resistance: {res_str} | Switch: {mom_switch.value()} | Active: {target_active_state}")
        debug_timer = time.ticks_ms()

    # 4. Trigger motor movement on state change
    if target_active_state != is_active:
        time.sleep_ms(30)  # Debounce delay
        
        # Re-verify inputs to confirm valid state change
        switch_pressed = (mom_switch.value() == 0)
        water_detected, w_volts, w_raw = check_water_sensor()
        ohm_detected, resistance, o_volts = check_ohmmeter_sensor()
        target_active_state = switch_pressed or water_detected or ohm_detected
        
        if target_active_state != is_active:
            if target_active_state:
                # Identify which sensor triggered activation
                if switch_pressed:
                    source = "Switch"
                elif water_detected:
                    source = f"Water Sensor ({w_volts:.2f}V)"
                else:
                    source = f"Ohmmeter ({resistance:.1f} Ω)"
                    
                print(f"-> ACTIVATED by {source}! Rotating +90°")
                led.value(1)
                rotate_stepper(STEPS_90_DEG, direction=1)
            else:
                print("-> CLEARED! Returning -90°")
                rotate_stepper(STEPS_90_DEG, direction=-1)
                led.value(0)

            is_active = target_active_state

    time.sleep_ms(20)
