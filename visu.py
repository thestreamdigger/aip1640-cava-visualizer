import time
import os
import fcntl
import subprocess
from threading import Thread, Event, Lock
from mpd import MPDClient, ConnectionError
from aip1640_driver import AIP1640
from bitmaps import char_bitmaps

CLOCK_PIN = 3
DATA_PIN = 2
MPD_HOST = "localhost"
MPD_PORT = 6600
DISPLAY_LENGTH = 16
SCROLL_COLUMNS_PER_SECOND_PAUSE = 24
SCROLL_COLUMNS_PER_SECOND_INTRO = 48
CAVA_OUTPUT_PATH = '/tmp/cava_output.raw'
CAVA_CONFIG_PATH = '/tmp/cava_config'
CAVA_FRAMERATE = 48
CAVA_UPDATE_INTERVAL = 1 / CAVA_FRAMERATE

BRIGHTNESS_PLAY = 2
BRIGHTNESS_PAUSE = 0
BRIGHTNESS_STOP = 0

SCROLL_INTRO_ENABLED = True

class IntegratedLEDDisplay:
    def __init__(self):
        try:
            self.display = AIP1640(clk_pin=CLOCK_PIN, dio_pin=DATA_PIN)
            self.display.set_brightness(BRIGHTNESS_STOP)
            self.display.clear()
        except Exception as e:
            print(f"Error initializing display: {e}")
            self.stop_event.set()
        self.mpd_client = None
        self.stop_event = Event()
        self.cava_data = [0] * DISPLAY_LENGTH
        self.cava_lock = Lock()
        self.current_state = "stop"
        self.bitmap_cache = {}
        self.cava_process = None
        self.scroll_position = 0
        self.display_buffer = []
        self.text = ""
        self.last_scroll_time = 0
        self.scroll_interval_pause = 1 / SCROLL_COLUMNS_PER_SECOND_PAUSE
        self.scroll_interval_intro = 1 / SCROLL_COLUMNS_PER_SECOND_INTRO
        self.current_song = ""
        self.new_song_intro = False
        self.intro_complete = False

    def connect_to_mpd(self):
        self.mpd_client = MPDClient()
        try:
            self.mpd_client.connect(MPD_HOST, MPD_PORT)
        except ConnectionError:
            print("Failed to connect to MPD")
            self.mpd_client = None

    def get_mpd_song_info(self):
        if not self.mpd_client:
            self.connect_to_mpd()
        if self.mpd_client:
            try:
                song = self.mpd_client.currentsong()
                status = self.mpd_client.status()
                self.current_state = status['state']
                track = song.get('track', '')
                artist = song.get('artist', '')
                title = song.get('title', '')
                parts = [p for p in [track, artist, title] if p]
                return " - ".join(parts)
            except ConnectionError:
                print("Lost connection to MPD")
                self.mpd_client = None
        return "No MPD Connection"

    def rotate_bitmap(self, bitmap):
        new_bitmap = [0] * 8
        for i in range(8):
            for j in range(8):
                if bitmap[j] & (1 << i):
                    new_bitmap[7-i] |= (1 << j)
        return new_bitmap

    def get_rotated_bitmap(self, char):
        if char not in self.bitmap_cache:
            char_bitmap = char_bitmaps.get(char, char_bitmaps[' '])
            rotated_bitmap = self.rotate_bitmap(char_bitmap)
            self.bitmap_cache[char] = rotated_bitmap
        return self.bitmap_cache[char]

    def scroll_text(self):
        current_time = time.time()
        scroll_interval = self.scroll_interval_intro if self.new_song_intro else self.scroll_interval_pause
        
        if current_time - self.last_scroll_time < scroll_interval:
            return self.display_buffer[self.scroll_position:self.scroll_position + DISPLAY_LENGTH]
        
        self.last_scroll_time = current_time
        if self.scroll_position == 0:
            self.display_buffer = []
            for char in self.text.upper():
                self.display_buffer.extend(self.get_rotated_bitmap(char))
                self.display_buffer.extend([0x00])
            self.display_buffer.extend([0x00] * DISPLAY_LENGTH)
        
        result = self.display_buffer[self.scroll_position:self.scroll_position + DISPLAY_LENGTH]
        self.scroll_position = (self.scroll_position + 1) % len(self.display_buffer)
        
        if self.scroll_position == 0 and self.new_song_intro:
            self.intro_complete = True
            self.new_song_intro = False
        
        return result

    def create_cava_config(self):
        config = f"""
[general]
bars = {DISPLAY_LENGTH}
framerate = {CAVA_FRAMERATE}

[input]
method = alsa
source = hw:Loopback,1,0
channels = stereo

[output]
method = raw
raw_target = {CAVA_OUTPUT_PATH}
data_format = ascii
ascii_max_range = 8

[smoothing]
integral = 36
monstercat = 1
waves = 0
gravity = 420
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
        try:
            self.cava_process = subprocess.Popen(['cava', '-p', CAVA_CONFIG_PATH], 
                                                 stdout=subprocess.DEVNULL, 
                                                 stderr=subprocess.DEVNULL)
            start_time = time.time()
            while not os.path.exists(CAVA_OUTPUT_PATH):
                if time.time() - start_time > 10:
                    raise TimeoutError("CAVA output file not created within timeout period")
                time.sleep(0.1)
        except Exception as e:
            print(f"Error starting CAVA: {e}")
            self.stop_event.set()

    def read_cava_output(self):
        while not self.stop_event.is_set():
            try:
                with open(CAVA_OUTPUT_PATH, 'rb', buffering=0) as file:
                    fd = file.fileno()
                    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                    while not self.stop_event.is_set():
                        try:
                            line = file.readline().decode().strip()
                            if line:
                                values = [int(v) for v in line.split(';') if v]
                                if len(values) == DISPLAY_LENGTH:
                                    with self.cava_lock:
                                        self.cava_data = values
                        except (IOError, OSError):
                            time.sleep(0.001)
            except FileNotFoundError:
                print("CAVA output file not found. Retrying...")
                time.sleep(1)

    def transform_to_bitmap(self, data):
        def reverse_bits(byte):
            return int(f'{byte:08b}'[::-1], 2)
        def create_column(value):
            column = sum(1 << i for i in range(value))
            return reverse_bits(column)
        left_bitmap = [create_column(value) for value in data[:8]]
        right_bitmap = [create_column(value) for value in data[8:]]
        left_rotated = [
            sum((1 << (7 - j)) for j in range(8) if left_bitmap[j] & (1 << i))
            for i in range(8)
        ]
        right_rotated = [
            sum((1 << j) for j in range(8) if right_bitmap[j] & (1 << (7 - i)))
            for i in range(8)
        ]
        return left_rotated + right_rotated

    def update_display(self):
        try:
            if self.current_state == 'play':
                if SCROLL_INTRO_ENABLED and self.new_song_intro and not self.intro_complete:
                    self.display.set_brightness(BRIGHTNESS_PLAY)
                    self.display.write(self.scroll_text())
                else:
                    self.display.set_brightness(BRIGHTNESS_PLAY)
                    with self.cava_lock:
                        bitmap = self.transform_to_bitmap(self.cava_data)
                    self.display.write(bitmap)
            elif self.current_state == 'pause':
                self.display.set_brightness(BRIGHTNESS_PAUSE)
                self.display.write(self.scroll_text())
            else:
                self.display.set_brightness(BRIGHTNESS_STOP)
                self.display.clear()
        except Exception as e:
            print(f"Error updating display: {e}")

    def check_mpd_state(self):
        if not self.mpd_client:
            self.connect_to_mpd()
        if self.mpd_client:
            try:
                status = self.mpd_client.status()
                new_state = status['state']
                new_song = self.get_mpd_song_info()
                if new_song != self.current_song:
                    self.current_song = new_song
                    self.text = new_song
                    self.scroll_position = 0
                    self.last_scroll_time = 0
                    if SCROLL_INTRO_ENABLED:
                        self.new_song_intro = True
                        self.intro_complete = False
                if new_state != self.current_state:
                    self.current_state = new_state
                    if new_state == 'pause':
                        self.text = new_song
                        self.scroll_position = 0
                        self.last_scroll_time = 0
            except ConnectionError:
                print("Lost connection to MPD")
                self.mpd_client = None

    def run(self):
        self.start_cava()
        cava_thread = Thread(target=self.read_cava_output)
        cava_thread.start()

        try:
            last_update_time = time.time()
            while not self.stop_event.is_set():
                current_time = time.time()
                if current_time - last_update_time >= CAVA_UPDATE_INTERVAL:
                    self.check_mpd_state()
                    self.update_display()
                    last_update_time = current_time
                time.sleep(0.001)
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Stopping...")
        finally:
            self.stop_event.set()
            if self.cava_process:
                self.cava_process.terminate()
            if self.mpd_client:
                self.mpd_client.disconnect()
            print("Cleanup complete. Exiting.")

if __name__ == '__main__':
    display = IntegratedLEDDisplay()
    display.run()
