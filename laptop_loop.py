import socket
import os
import time
import sys
import csv
import numpy as np
import clr

PORT = 5005  # Port number to match the main computer client
PORT_LOOP = 5006
# Ensure pythonnet is installed
try:
    import clr
except ImportError:
    print("pythonnet is not installed. Please install it using 'pip install pythonnet'")
    sys.exit(1)

# Update this path to the actual location of your BeamGage DLL files
path2BGP = r'C:\Program Files\Spiricon\BeamGage Professional'

# Add reference to BeamGage assemblies
try:
    clr.AddReference(os.path.join(path2BGP, 'Spiricon.Automation.dll'))
    clr.AddReference(os.path.join(path2BGP, 'Spiricon.BeamGage.Automation.dll'))
    clr.AddReference(os.path.join(path2BGP, 'Spiricon.Interfaces.ConsoleService.dll'))
    clr.AddReference(os.path.join(path2BGP, 'Spiricon.TreePattern.dll'))
except Exception as e:
    print(f"Failed to add reference to BeamGage assemblies: {e}")
    sys.exit(1)

# Import the .NET namespaces
try:
    import Spiricon.Automation as SpA
except ImportError as e:
    print(f"Failed to import Spiricon.Automation: {e}")
    sys.exit(1)

# BeamGage Wrapper Class
class BeamGagePy:
    def __init__(self, instance_name, show_gui):
        self.beamgage = SpA.AutomatedBeamGage(instance_name, show_gui)
        self.data_source = DataSource(self.beamgage)

    def shutdown(self):
        del self.data_source
        self.beamgage.Instance.Shutdown()
        self.beamgage.Dispose()

    def get_frame_data(self):
        return self.beamgage.ResultsPriorityFrame

# DataSource Class
class DataSource:
    def __init__(self, beamgage_instance):
        self.beamgage = beamgage_instance

    def start(self):
        self.beamgage.DataSource.Start()

    def stop(self):
        self.beamgage.DataSource.Stop()

    def ultracal(self):
        self.beamgage.Calibration.Ultracal()
        time.sleep(2)

    @property
    def status(self):
        return self.beamgage.DataSource.Status

# Recorder Class for Frame Recording
class BeamGageRecorder:
    def __init__(self, instance_name, show_gui, output_dir, name_frame,conn):
        self.beamgage = BeamGagePy(instance_name, show_gui)
        self.output_dir = output_dir
        self.name_frame = name_frame
        self.conn = conn
        os.makedirs(self.output_dir, exist_ok=True)

    def start_acquisition(self):
        self.beamgage.data_source.start()

    def stop_acquisition(self):
        self.beamgage.data_source.stop()

    def record_frames(self, num_frames, frame_interval, name_frame,conn):
        #self.beamgage.data_source.ultracal()
        self.start_acquisition()
        time.sleep(1)
        # Send "DONE" message back to the main computer
        conn.sendall("DONE".encode())
        print("Sent job completion confirmation to main computer.")
                                # Start BeamGage recordving
        time.sleep(1)
        for i in range(num_frames):
            #time.sleep(1)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as loop_socket:
                loop_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                loop_socket.bind(("", PORT_LOOP))
                loop_socket.listen(1)
                print("Laptop server is waiting for connection inside the loop")
                while True:
                    # Wait to receive a trigger command from the main computer
                    conn_client, addr =  loop_socket.accept()
                    print("successfully accept")
                    with conn_client:
                        print(f"Connected to {addr}")
                        data = conn_client.recv(1024).decode()
                        if not data:
                            continue
                        print(data)
                        trigger = str(data)
                    #trigger = conn.recv(1024).decode().strip()
                        if trigger == "TRIGGER":
                            print(f"Received TRIGGER for frame {i}")
                            # Acquire frame and save to CSV
                            frame = self.beamgage.get_frame_data()
                            self.save_frame_to_csv(frame, i, name_frame)
                            # After saving, send back a "DONE" message
                            conn_client.sendall("DONE".encode())
                            print(f"Frame {i} processed and DONE sent")
                            #time.sleep(frame_interval)
                            break
                #else:
                #    print(f"Unexpected message for frame {i}: {trigger}")

        self.stop_acquisition()

    def save_frame_to_csv(self, frame, frame_index, name_frame):
        filename = os.path.join(self.output_dir, f'{name_frame}{frame_index}.csv')
        frame_data = frame.DoubleData
        width = frame.Width
        height = frame.Height
        frame_array = np.array(frame_data).reshape((height, width))

        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            for row in frame_array:
                writer.writerow(row)

    def shutdown(self):
        self.beamgage.shutdown()

# TCP Server Function
def start_server():
    """Laptop acts as a server to receive parameters from the main computer."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("", PORT))
        server_socket.listen()
        print("Laptop server is waiting for connection...")

        while True:
            conn, addr = server_socket.accept()
            print("successfully accept")
            with conn:
                print(f"Connected to {addr}")
                data = conn.recv(1024).decode()
                if not data:
                    continue

                # Parse received data
                output_dir, name_frame, num_frames, frame_interval = data.split("|")
                num_frames = int(num_frames)
                frame_interval = float(frame_interval)

                print(f"Received parameters: {output_dir}, {name_frame}, {num_frames}, {frame_interval}")

                # Start BeamGage recording
                #instance_name = "camera"
                #show_gui = False
                #print("before gui")
                #recorder = BeamGageRecorder(instance_name, show_gui, output_dir, name_frame)
                #print("reach")
                #try:
                #    recorder.record_frames(num_frames, frame_interval, name_frame)
                #finally:
                #    recorder.shutdown()

                # Send "DONE" message back to the main computer
                #conn.sendall("DONE".encode())
                #print("Sent job completion confirmation to main computer.")
                #                # Start BeamGage recordving
                instance_name = "camera"
                show_gui = False
                print("before gui")
                recorder = BeamGageRecorder(instance_name, show_gui, output_dir, name_frame,conn)
                #print("reach")
                try:
                    recorder.record_frames(num_frames, frame_interval, name_frame,conn)
                finally:
                    recorder.shutdown()

if __name__ == "__main__":
    start_server()
