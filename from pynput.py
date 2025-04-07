from pynput.keyboard import Key, Controller
import time

try:
    keyboard = Controller()
    presskey = input("What key to spam press? (Type 'enter' for the Enter key)\n>")

    try:
        times = float(input("How many times to press? If infinity, type -1\n>"))
        delaytime = float(input("What delay between pressing keys? (seconds)\n>"))
    except ValueError:
        print("Invalid input for times or delaytime. Please try again.")
        exit()

    input("Press Enter to continue...")

    # Determine the correct key to press
    if presskey.lower() == "enter":
        presskey = Key.enter

    for count in range(3, 0, -1):
        print(count)
        time.sleep(1)

    print("Starting key spamming...")

    # Start spamming the key
    if times == -1:
        while True:
            keyboard.press(presskey)
            keyboard.release(presskey)
            time.sleep(delaytime)
    elif times >= 0:
        for _ in range(int(times)):  # Ensure `times` is an integer for range
            keyboard.press(presskey)
            keyboard.release(presskey)
            time.sleep(delaytime)

except Exception as e:
    print(f"An error occurred: {e}")