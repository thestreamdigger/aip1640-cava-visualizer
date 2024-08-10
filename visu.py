import time
import os
import fcntl
import subprocess
import signal
from threading import Thread, Event
from aip1640_driver import AIP1640

__version__ = '0.1'

CLOCK_PIN = 3
DATA_PIN = 2
SLEEP_TIME = 0.005
DEFAULT_BRIGHTNESS = 0
CAVA_OUTPUT_PATH = '/tmp/cava_output.raw'
CAVA_CONFIG_PATH = '/tmp/cava_config'

class LEDDisplay:
    def __init__(self, clk_pin=CLOCK_PIN, dio_pin=DATA_PIN, brightness=DEFAULT_BRIGHTNESS):
        self.display = AIP1640(clk_pin=clk_pin, dio_pin=dio_pin, brightness=brightness)
        self.images = {}
        self.current_image_name = "initial"
        self.stop_event = Event()
        self.update_event = Event()
        self.bitmap = [0] * 16
        self.cava_process = None

    def set_brightness(self, brightness):
        try:
            self.display.set_brightness(brightness)
        except ValueError:
            pass

    def add_image(self, name, data):
        self.images[name] = data

    def remove_image(self, name):
        self.images.pop(name, None)

    def update_display(self):
        while not self.stop_event.is_set():
            self.update_event.wait()
            try:
                self.display.write(self.bitmap)
            except Exception:
                pass
            self.update_event.clear()

    def read_cava_output(self, file_path):
        with open(file_path, 'r') as file:
            fd = file.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            buffer = ""
            while not self.stop_event.is_set():
                try:
                    part = file.read()
                    if part:
                        buffer += part
                        if '\n' not in buffer:
                            time.sleep(SLEEP_TIME)
                            continue
                        lines = buffer.split('\n')
                        buffer = lines[-1]
                        for line in lines[:-1]:
                            values = line.strip().split(';')
                            filtered_values = [value for value in values if value]
                            if len(filtered_values) == 16:
                                left_data = [int(value) for value in filtered_values[:8]]
                                right_data = [int(value) for value in filtered_values[8:]]
                                self.bitmap = self.transform_to_bitmap(left_data, right_data)
                                self.update_event.set()
                except IOError:
                    time.sleep(SLEEP_TIME)
                except TypeError:
                    buffer = ""
                    time.sleep(SLEEP_TIME)

    @staticmethod
    def transform_to_bitmap(left_data, right_data):
        def reverse_bits(byte):
            return int(f'{byte:08b}'[::-1], 2)

        def create_column(value):
            column = sum(1 << i for i in range(value))
            return reverse_bits(column)

        left_bitmap = [create_column(value) for value in left_data]
        right_bitmap = [create_column(value) for value in right_data]

        left_rotated = [
            sum((1 << (7 - j)) for j in range(8) if left_bitmap[j] & (1 << i))
            for i in range(8)
        ]

        right_rotated = [
            sum((1 << j) for j in range(8) if right_bitmap[j] & (1 << (7 - i)))
            for i in range(8)
        ]

        return left_rotated + right_rotated

    def create_cava_config(self):
        config = """
[general]
bars = 16
framerate = 30

[input]
method = alsa
source = hw:Loopback,1,0
channels = stereo

[output]
method = raw
raw_target = /tmp/cava_output.raw
data_format = ascii
ascii_max_range = 8

[smoothing]
integral = 25
monstercat = 1
waves = 0
gravity = 300
ignore = 0

[eq]
1 = 1.2
2 = 1.2
3 = 1.1
4 = 1.1
5 = 1
6 = 1
7 = 1
8 = 1
"""
        with open(CAVA_CONFIG_PATH, 'w') as f:
            f.write(config)

    def start_cava(self):
        self.create_cava_config()
        self.cava_process = subprocess.Popen(['sudo', 'cava', '-p', CAVA_CONFIG_PATH], 
                                             stdout=subprocess.DEVNULL, 
                                             stderr=subprocess.DEVNULL)

    def stop_cava(self):
        if self.cava_process:
            subprocess.run(['sudo', 'kill', '-SIGINT', str(self.cava_process.pid)])
            self.cava_process.wait()

    def run(self, cava_output_path=CAVA_OUTPUT_PATH):
        def signal_handler(signum, frame):
            self.stop_event.set()
            self.update_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            self.start_cava()
            time.sleep(2)
            reader_thread = Thread(target=self.read_cava_output, args=(cava_output_path,))
            updater_thread = Thread(target=self.update_display)
            reader_thread.start()
            updater_thread.start()

            while not self.stop_event.is_set():
                time.sleep(0.1)

            reader_thread.join()
            updater_thread.join()
        finally:
            self.stop_cava()

if __name__ == '__main__':
    display = LEDDisplay()
    display.run()