from machine import Pin
from time import sleep

# Pin setup
switch = Pin(9, Pin.IN, Pin.PULL_UP)
led = Pin(10, Pin.OUT)

while True:
    # Switch is LOW when pressed
    if switch.value() == 0:
        led.value(1)
        print("Switch pressed!")
    else:
        led.value(0)

    sleep(0.01)

