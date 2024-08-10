# 8x16 LED Matrix Audio Visualizer with AiP1640 for moOde

## Overview

This implementation creates an audio visualizer using an 8x16 LED matrix display, controlled by the AiP1640 chip, intended as a companion project for use with the moOde audio player on a Raspberry Pi. It captures audio output from ALSA (Advanced Linux Sound Architecture), processes it with CAVA (Console-based Audio Visualizer for ALSA), and displays a real-time visualization on the LED matrix.

The primary motivation behind this implementation was to create a tangible audio visualizer for music streamers the use USB Audio output. As a benefit, this approach ensures that the analog audio signal remains completely unaffected, while still offering an engaging visual representation of the music.

This project offers a Python driver for the AiP1640 LED driver chip and a control script, making it easier for DIY tinkerers and sound aficionados to work with this cheap and fun LED matrix display module.

## Features

- Utilizes an 8x16 LED matrix display with AiP1640 chip controller
- Real-time processing of audio from moOde audio player
- Seamless CAVA start and stop processes
- Adjustable display brightness

## Hardware Requirements

- Raspberry Pi running moOde audio player
- 8x16 LED matrix display based on AiP1640 chip
- Appropriate connections between Raspberry Pi and LED matrix

## Software Requirements

- moOde audio player
- CAVA (Console-based Audio Visualizer for ALSA)

## Installation

1. Install the Python scripts:

   There are two ways to set up this visualizer:

   - Clone this repository:
     ```
     git clone https://github.com/yourusername/8x16-led-audio-visualizer.git
     cd 8x16-led-audio-visualizer
     ```

   - Direct script copy (quickest method):
     Given the simplicity of the project, you can also just copy the two essential Python scripts:
     - `aip1640_driver.py`: The driver script for the AIP1640 LED controller
     - `visu.py`: The main controller script for the visualizer

     You can create these two files in your preferred directory and copy the code directly into them.

2. Install CAVA:
   
   On Raspberry Pi, you can install CAVA very easily:
   ```
   sudo apt update
   sudo apt install cava
   ```

   If you prefer to install from source or are using a different system, follow these steps:
   ```
   sudo apt install libfftw3-dev libasound2-dev libncursesw5-dev libpulse-dev libtool automake
   git clone https://github.com/karlstav/cava.git
   cd cava
   ./autogen.sh
   ./configure
   make
   sudo make install
   ```

3. Configure ALSA loopback in moOde:
   - Go to moOde interface
   - Navigate to Configure -> Audio
   - Under "ALSA Options", set Loopback to "on"

## Usage

Run the visualizer with the built-in CAVA configuration:

```
python3 visu.py
```

## Configuration

Edit `visu.py` to change GPIO pins or other settings:

```python
CLOCK_PIN = 3
DATA_PIN = 2
DEFAULT_BRIGHTNESS = 0
```

The CAVA configuration for the display is already included in the `visu.py` script.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

As the creator of this project, I want to clarify that I'm a beginner and hobbyist, not a professional at this. I'm an enthusiastic music lover who discovered in Linux audio a way to combine my passion for music with learning new stuff. My code is primarily aimed at my personal DIY music streamer projects using Raspberry Pi and microcontrollers. 

If you're also a hobbyist or enthusiast in this area, don't hesitate to contribute or suggest improvements. This is all about learning and enjoying the process!

## License

This project is released under the GNU General Public License v3.0. If you distribute this software or any derivative works, you must do so under the same license (GPL-3.0).

## Acknowledgments

- [AIP1640 LED Driver Datasheet](https://www.lcsc.com/datasheet/lcsc_datasheet_AiP1640_C82650.pdf)
- [moOde audio player](https://moodeaudio.org/)
- [CAVA (Console-based Audio Visualizer for ALSA)](https://github.com/karlstav/cava)
- [MPD (Music Player Daemon)](https://www.musicpd.org/)
- [ALSA (Advanced Linux Sound Architecture)](https://alsa-project.org/)

## Version and Compatibility

Current version: 0.1

This project has been tested with:
- moOde audio player version 9.0.6
- CAVA version 0.10.2
