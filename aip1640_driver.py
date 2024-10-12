from gpiozero import LEDBoard
from time import sleep

__version__ = '0.3'

DATA_COMMAND = 0x40
ADDRESS_COMMAND = 0xC0
DISPLAY_CONTROL_COMMAND = 0x80
DISPLAY_ON = 0x08
DELAY = 0.000001

BRIGHTNESS_MAX = 7
DISPLAY_MAX_POS = 15
DISPLAY_MAX_ROWS = 16

class AIP1640:
    def __init__(self, clk_pin, dio_pin, brightness=5):
        self.pins = LEDBoard(clk=clk_pin, dio=dio_pin, pwm=False)
        self._validate_brightness(brightness)
        self.brightness = brightness
        self._initialize_display()

    def _initialize_display(self):
        self._send_data_command()
        self._set_display_control()

    def _start_communication(self):
        self.pins.dio.off()
        self.pins.clk.off()
        sleep(DELAY)

    def _stop_communication(self):
        self.pins.dio.off()
        self.pins.clk.on()
        self.pins.dio.on()
        sleep(DELAY)

    def _send_data_command(self):
        self._start_communication()
        self._write_byte(DATA_COMMAND)
        self._stop_communication()

    def _set_display_control(self):
        self._start_communication()
        control_command = DISPLAY_CONTROL_COMMAND | DISPLAY_ON | self.brightness
        self._write_byte(control_command)
        self._stop_communication()

    def _write_byte(self, byte):
        for i in range(8):
            self.pins.dio.value = (byte >> i) & 1
            self.pins.clk.on()
            self.pins.clk.off()
        sleep(DELAY)

    def _validate_brightness(self, brightness):
        if not 0 <= brightness <= BRIGHTNESS_MAX:
            raise ValueError(f"Brightness out of range (0-{BRIGHTNESS_MAX})")

    def set_brightness(self, brightness=None):
        if brightness is None:
            return self.brightness
        self._validate_brightness(brightness)
        self.brightness = brightness
        self._set_display_control()
        return self.brightness

    def write(self, rows, pos=0):
        if not 0 <= pos <= DISPLAY_MAX_POS:
            raise ValueError(f"Position out of range (0-{DISPLAY_MAX_POS})")
        if len(rows) > DISPLAY_MAX_ROWS:
            raise ValueError(f'Number of rows exceeds the maximum for the display (max {DISPLAY_MAX_ROWS})')

        self._send_data_command()
        self._start_communication()
        self._write_byte(ADDRESS_COMMAND | pos)
        for row in rows:
            self._write_byte(row)
        self._stop_communication()
        self._set_display_control()

    def write_int(self, value, pos=0, length=8):
        value_bytes = value.to_bytes(length, 'big')
        self.write(value_bytes, pos)

    def write_high_to_low(self, buf, pos=0):
        if not 0 <= pos <= DISPLAY_MAX_POS:
            raise ValueError(f"Position out of range (0-{DISPLAY_MAX_POS})")
        if len(buf) > DISPLAY_MAX_ROWS:
            raise ValueError(f'Number of lines in buffer exceeds the maximum (max {DISPLAY_MAX_ROWS})')

        self._send_data_command()
        self._start_communication()
        self._write_byte(ADDRESS_COMMAND | pos)
        for i in range(len(buf) - 1, -1, -1):
            self._write_byte(buf[i])
        self._stop_communication()
        self._set_display_control()
