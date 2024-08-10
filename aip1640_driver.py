from gpiozero import LEDBoard
from time import sleep

__version__ = '0.1'

DATA_COMMAND = 0x40
ADDRESS_COMMAND = 0xC0
DISPLAY_CONTROL_COMMAND = 0x80
DISPLAY_ON = 0x08
DELAY = 0.000001

class AIP1640:
    def __init__(self, clk_pin, dio_pin, brightness=5):
        self.pins = LEDBoard(clk=clk_pin, dio=dio_pin, pwm=False)
        if not 0 <= brightness <= 7:
            raise ValueError("Brightness out of range (0-7)")
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
        self._write_byte(DISPLAY_CONTROL_COMMAND | DISPLAY_ON | self.brightness)
        self._stop_communication()

    def _write_byte(self, byte):
        for i in range(8):
            self.pins.dio.value = (byte >> i) & 1
            self.pins.clk.on()
            self.pins.clk.off()
        sleep(DELAY)

    def set_brightness(self, brightness=None):
        if brightness is None:
            return self.brightness
        if not 0 <= brightness <= 7:
            raise ValueError("Brightness out of range (0-7)")
        self.brightness = brightness
        self._set_display_control()
        return self.brightness

    def write(self, rows, pos=0):
        if not 0 <= pos <= 15:
            raise ValueError("Position out of range (0-15)")
        if len(rows) > 16:
            raise ValueError('Too many rows for 8x16 display (max 16)')
        
        self._send_data_command()
        self._start_communication()
        self._write_byte(ADDRESS_COMMAND | pos)
        for row in rows:
            self._write_byte(row)
        self._stop_communication()
        self._set_display_control()

    def write_int(self, value, pos=0, length=8):
        self.write(value.to_bytes(length, 'big'), pos)

    def write_high_to_low(self, buf, pos=0):
        self._send_data_command()
        self._start_communication()
        self._write_byte(ADDRESS_COMMAND | pos)
        for i in range(7 - pos, -1, -1):
            self._write_byte(buf[i])
        self._stop_communication()
        self._set_display_control()
