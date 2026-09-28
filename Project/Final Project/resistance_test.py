from machine import ADC, Pin
import time

# --- Configuration Constants ---
VIN = 3.3          # Supply voltage (Volts)
R1 = 220.0       # Reference resistor value in Ohms (10 kΩ)
NUM_SAMPLES = 64   # Number of ADC samples to average for noise reduction

# Set up Pin A0 (GPIO 1 on Arduino Nano ESP32)
adc_pin = Pin(2)
adc = ADC(adc_pin)

# Configure attenuation to measure the full 0V - 3.3V range
adc.atten(ADC.ATTN_11DB)

def read_voltage():
    """Reads raw microvolts from ADC and converts to Volts with oversampling."""
    total_uv = 0
    for _ in range(NUM_SAMPLES):
        total_uv += adc.read_uv()  # Reads voltage in microvolts (µV) directly
        time.sleep_us(100)
    
    avg_uv = total_uv / NUM_SAMPLES
    return avg_uv / 1_000_000  # Convert microvolts to Volts

def calculate_resistance(v_out):
    """Calculates unknown resistance Rx using the voltage divider formula."""
    # Threshold check: If Vout is extremely close to Vin, prongs are disconnected (Open Circuit)
    if v_out >= (VIN - 0.05):
        return None  # Open circuit
    
    # Threshold check: If Vout is close to 0V, prongs are shorted directly together
    if v_out <= 0.02:
        return 0.0
    
    # Voltage divider formula: Rx = R1 * (Vout / (Vin - Vout))
    r_x = R1 * (v_out / (VIN - v_out))
    return r_x

# --- Main Measurement Loop ---
print("--- MicroPython Multimeter (Ohmmeter) Ready ---")

while True:
    v_out = read_voltage()
    r_x = calculate_resistance(v_out)
    
    if r_x is None:
        print("Status: Open Circuit (Probes Disconnected)")
    elif r_x < 1000:
        print(f"Voltage: {v_out:.2f} V | Resistance: {r_x:.1f} Ω")
    elif r_x < 1_000_000:
        print(f"Voltage: {v_out:.2f} V | Resistance: {r_x / 1000:.2f} kΩ")
    else:
        print(f"Voltage: {v_out:.2f} V | Resistance: {r_x / 1_000_000:.2f} MΩ")
        
    time.sleep(0.5)