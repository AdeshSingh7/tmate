import RPi.GPIO as GPIO
import time
import sys

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

PIN = int(sys.argv[1]) if len(sys.argv) > 1 else 17   # default GPIO17
MODE = sys.argv[2].lower() if len(sys.argv) > 2 else "in"  # in / out
PULL = sys.argv[3].lower() if len(sys.argv) > 3 else "none"  # up / down / none

print(f"[GPIO TEST] Pin={PIN} Mode={MODE.upper()} Pull={PULL.upper()}\n")

try:
    if MODE == "in":
        if PULL == "up":
            GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif PULL == "down":
            GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        else:
            GPIO.setup(PIN, GPIO.IN)

        print("INPUT MODE ACTIVE (CTRL+C to exit)")
        print("Reading pin state...\n")

        while True:
            state = GPIO.input(PIN)
            print(f"GPIO {PIN} STATE = {state}")
            time.sleep(0.5)

    elif MODE == "out":
        GPIO.setup(PIN, GPIO.OUT)
        print("OUTPUT MODE ACTIVE (CTRL+C to exit)\n")

        while True:
            GPIO.output(PIN, GPIO.HIGH)
            print(f"GPIO {PIN} -> HIGH")
            time.sleep(0.5)

            GPIO.output(PIN, GPIO.LOW)
            print(f"GPIO {PIN} -> LOW")
            time.sleep(0.5)

    else:
        print("Invalid mode. Use: in or out")

except KeyboardInterrupt:
    print("Test stopped by user")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up. Exit safe.")
