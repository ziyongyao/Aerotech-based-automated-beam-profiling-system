import socket
import automation1 as a1
import time

# Replace with your Laptop's IP Address (Check using `ipconfig`)
LAPTOP_IP = "192.168.2.11"
PORT = 5005  # Must match the server port on the laptop
PORT_LOOP = 5006
def my_callback(args: a1.ControllerTaskCallbackArguments):
    print("Callback triggered from AeroScript")

    try:
        # Extract parameters from AeroScript
        i = 0
        for string in args.aeroscript_string_inputs:
            if i == 0:
                output_dir = string
            if i == 1:
                name_frame = string
            i += 1

        for integer in args.aeroscript_integer_inputs:
            num_frames = integer

        for real in args.aeroscript_real_inputs:
            frame_interval = real

        # Send data to the laptop and wait for completion signal
        send_data_to_laptop(output_dir, name_frame, num_frames, frame_interval)

    except Exception as e:
        print(f"Error in callback: {e}")

def my_callback_loop(args: a1.ControllerTaskCallbackArguments):
    print("Callback triggered from AeroScript_loop")

    try:
        # Extract parameters from AeroScript
        i = 0
        for string in args.aeroscript_string_inputs:
            if i == 0:
                output_dir = string
            if i == 1:
                name_frame = string
            i += 1

        for integer in args.aeroscript_integer_inputs:
            num_frames = integer

        for real in args.aeroscript_real_inputs:
            frame_interval = real

        # Send data to the laptop and wait for completion signal
        send_data_to_laptop_loop(output_dir, name_frame, num_frames, frame_interval)

    except Exception as e:
        print(f"Error in callback: {e}")


def send_data_to_laptop(output_dir, name_frame, num_frames, frame_interval):
    """Send frame recording parameters to the laptop and wait for response."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LAPTOP_IP, PORT))
            message = f"{output_dir}|{name_frame}|{num_frames}|{frame_interval}"
            s.sendall(message.encode())
            print(f"Sent data to laptop: {message}")

            # Wait for the "DONE" message from the laptop
            response = s.recv(1024).decode()
            if response == "DONE":
                print("Laptop finished processing the frames.")

    except Exception as e:
        print(f"Error sending data to laptop: {e}")
def send_data_to_laptop_loop(output_dir, name_frame, num_frames, frame_interval):
    """
    Repeatedly attempts to send a "TRIGGER" message to the laptop on PORT_LOOP (5006)
    until a "DONE" response is received.
    """
    success = False
    attempt = 0
    while not success:
        attempt += 1
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((LAPTOP_IP, PORT_LOOP))
                s.sendall("TRIGGER".encode())
                print(f"[Main] Attempt {attempt}: Sent TRIGGER.")
                response = s.recv(1024).decode().strip()
                if response == "DONE":
                    print(f"[Main] Attempt {attempt}: Received DONE. Trigger successful.")
                    success = True
                else:
                    print(f"[Main] Attempt {attempt}: Unexpected response: {response}")
        except Exception as e:
            print(f"[Main] Attempt {attempt}: Error sending TRIGGER: {e}")
        if not success:
            time.sleep(1)  # Wait a moment before retrying
# Setup AeroScript Controller
controller = a1.Controller.connect()
controller.start()

# Register the callback for a designated task (here we use task 1 with event id 1)
controller.runtime.tasks[1].callback.register(1, my_callback)
controller.runtime.tasks[1].callback.register(2, my_callback_loop)

# Keep the script running (or integrate it into your main control loop)
time.sleep(10000)
