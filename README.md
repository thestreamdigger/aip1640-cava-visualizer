# 8x16 AiP1640 LED Matrix Audio Spectrum Visualizer for moOde

## Overview

This project implements an audio spectrum visualizer using an 8x16 LED matrix display controlled by the AiP1640 chip. Designed as a companion for the moOde audio player on a Raspberry Pi, it captures audio output from ALSA (Advanced Linux Sound Architecture), processes it with CAVA (Console-based Audio Visualizer for ALSA), and displays a real-time visualization on the LED matrix.

The primary motivation behind this implementation is to create a tangible audio visualizer for SBC music streamers that use USB Audio as output. This approach ensures that the analog audio signal remains unaffected while offering an engaging visual representation of the music.

This project provides a Python driver for the AiP1640 LED driver chip and a control script, making it easier for DIY enthusiasts and audio aficionados to work with this affordable and fun LED matrix display module.

## Features

- Real-time audio spectrum visualization on an 8x16 LED matrix display
- AiP1640 chip controller support
- Seamless integration with moOde audio player
- Non-intrusive audio capture using ALSA loopback
- Automatic CAVA process management
- Adjustable display brightness (8 levels)


## Hardware Requirements

- Raspberry Pi
- 8x16 LED matrix display based on AiP1640 chip
- Jumper wires for connecting Raspberry Pi to LED matrix

## Software Requirements

- moOde audio player (tested with version 9.0.6)
- CAVA (tested with version 0.10.2)
- Python 3+

## Installation

1. **Set up moOde audio player**:
   Follow the official moOde installation guide at [moodeaudio.org](https://moodeaudio.org/).

2. **Install CAVA**:
   ```bash
   sudo apt update
   sudo apt install cava
   ```

3. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/8x16-led-audio-visualizer.git
   cd 8x16-led-audio-visualizer
   ```

4. **Configure ALSA loopback in moOde**:
   - Open the moOde web interface
   - Navigate to Configure -> Audio
   - Under "ALSA Options", set Loopback to "on"
   - Save and reboot your Raspberry Pi

## Usage

1. Connect your LED matrix to the Raspberry Pi GPIO pins as specified in the `visu.py` script.

2. Run the visualizer:
   ```bash
   sudo python3 visu.py
   ```

3. Play music through moOde, and watch the LED matrix come to life!

## Configuration

Edit `visu.py` to customize the visualizer:

```python
CLOCK_PIN = 3  # GPIO pin for clock
DATA_PIN = 2   # GPIO pin for data
DEFAULT_BRIGHTNESS = 0  # Initial brightness (0-7)
```

You can also modify the CAVA configuration within the `create_cava_config()` function in `visu.py` to adjust the audio processing parameters.

## Troubleshooting

- **No display**: Ensure the LED matrix is correctly connected and the GPIO pins are properly configured.
- **No visualization**: Check if ALSA loopback is enabled in moOde and CAVA is installed correctly.
- **Permission errors**: Make sure to run the script with `sudo`.

## Contributing

Contributions are welcome! Please feel free to contribute or suggest improvements. This is all about learning and enjoying the process!

## License

This project is released under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [AIP1640 datasheet](https://www.lcsc.com/datasheet/lcsc_datasheet_AiP1640_C82650.pdf)
- [moOde audio player](https://moodeaudio.org/)
- [CAVA (Console-based Audio Visualizer for ALSA)](https://github.com/karlstav/cava)
- [MPD (Music Player Daemon)](https://www.musicpd.org/)
- [ALSA (Advanced Linux Sound Architecture)](https://alsa-project.org/)

## Version and Compatibility

- Current version: 0.1
- Tested with:
  - moOde audio player version 9.0.6
  - CAVA version 0.10.2
  - Raspberry Pi 4 Model B (but should work with other models)
