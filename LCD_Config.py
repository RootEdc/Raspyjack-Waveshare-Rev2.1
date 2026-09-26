##
 #  @filename   :   DEV_Config.py
 #  @brief      :   LCD hardware interface implements (GPIO, SPI)
 #                   Supports: SPI displays (ST7735, ST7789) + CardputerZero framebuffer
 #  @author     :   Yehui from Waveshare (original), 7h30th3r0n3 (CardputerZero)
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documnetation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to  whom the Software is
 # furished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 #

import os
import time

# ---------------------------------------------------------------------------
# Display type detection from gui_conf.json
# ---------------------------------------------------------------------------
_DISPLAY_TYPE = "ST7735_128"
_DISPLAY_SETTINGS = {}
try:
    import json as _json
    for _p in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_conf.json"),
        "/root/Raspyjack/gui_conf.json",
    ]:
        if os.path.isfile(_p):
            with open(_p, "r") as _f:
                _DISPLAY_SETTINGS = _json.load(_f).get("DISPLAY", {})
                _DISPLAY_TYPE = _DISPLAY_SETTINGS.get("type", _DISPLAY_TYPE)
            break
except Exception:
    pass

# Hardware auto-detect fallback: if gui_conf.json says ST7735 but we're on a CardputerZero
if _DISPLAY_TYPE != "CARDPUTER_320":
    for _i in range(4):
        try:
            with open(f"/sys/class/graphics/fb{_i}/name", "r") as _fb:
                if any(n in _fb.read() for n in ("st7789v_m5st", "panel-mipi-dbi")):
                    _DISPLAY_TYPE = "CARDPUTER_320"
                    break
        except Exception:
            pass


_FRAMEBUFFER_DISPLAY = _DISPLAY_TYPE in ("CARDPUTER_320", "ST7789_320_FB")

if _FRAMEBUFFER_DISPLAY:
    # ===================================================================
    # CardputerZero: framebuffer stub (no SPI, no GPIO for display)
    # ===================================================================
    import mmap

    LCD_RST_PIN = -1
    LCD_DC_PIN = -1
    LCD_CS_PIN = -1
    LCD_BL_PIN = -1

    _FB_NAMES = ("st7789v_m5st", "panel-mipi-dbi", "fb_st7789v", "st7789v")
    FB_DEVICE = os.environ.get("RJ_FB_DEVICE", "")
    if not FB_DEVICE:
        FB_DEVICE = "/dev/fb0"
        for _i in range(4):
            _fb_name_path = f"/sys/class/graphics/fb{_i}/name"
            try:
                with open(_fb_name_path) as _fn:
                    fb_name = _fn.read()
                    if any(n in fb_name for n in _FB_NAMES):
                        FB_DEVICE = f"/dev/fb{_i}"
                        break
            except Exception:
                pass
    FB_WIDTH = 320
    FB_HEIGHT = 170 if _DISPLAY_TYPE == "CARDPUTER_320" else 240
    FB_BPP = 16
    FB_SIZE = FB_WIDTH * FB_HEIGHT * (FB_BPP // 8)

    _fb_fd = None
    _fb_mmap = None

    class _SpiStub:
        max_speed_hz = 0
        mode = 0
        def writebytes(self, data):
            pass

    SPI = _SpiStub()

    def _open_fb():
        global _fb_fd, _fb_mmap
        if _fb_mmap is not None:
            return _fb_mmap
        _fb_fd = os.open(FB_DEVICE, os.O_RDWR)
        _fb_mmap = mmap.mmap(
            _fb_fd, FB_SIZE, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ
        )
        return _fb_mmap

    def fb_write(data: bytes):
        fb = _open_fb()
        fb.seek(0)
        fb.write(data)

    def epd_digital_write(pin, value):
        pass

    def Driver_Delay_ms(xms):
        pass

    def SPI_Write_Byte(data):
        pass

    def _unblank_fb():
        blank_path = FB_DEVICE.replace("/dev/", "/sys/class/graphics/") + "/blank"
        try:
            with open(blank_path, "w") as f:
                f.write("0")
        except Exception:
            pass

    def GPIO_Init():
        _open_fb()
        _unblank_fb()
        return 0

else:
    # ===================================================================
    # Standard Raspberry Pi: SPI + GPIO for Waveshare HAT displays
    # ===================================================================
    import spidev
    import RPi.GPIO as GPIO

    # Default pin mapping for Waveshare 1.44" ST7735HAT (128x128) and
    # 1.3" ST7789 (240x240). Pin selection by display type so multiple
    # panels do not clobber each other.
    if _DISPLAY_TYPE in ("ST7735_320", "ILI9341_320", "ST7789_320"):
        # Your 320x240 ST7735R panel (user-specified pins).
        LCD_RST_PIN = 27
        LCD_DC_PIN  = 22   # Waveshare 2.8-inch LCD: physical pin 15
        LCD_CS_PIN  = 8
        LCD_BL_PIN  = 18   # PWM0 backlight
        if _DISPLAY_TYPE in ("ILI9341_320", "ST7789_320"):
            LCD_RST_PIN = int(_DISPLAY_SETTINGS.get("rst_pin", LCD_RST_PIN))
            LCD_DC_PIN = int(_DISPLAY_SETTINGS.get("dc_pin", LCD_DC_PIN))
            LCD_BL_PIN = int(_DISPLAY_SETTINGS.get("bl_pin", LCD_BL_PIN))
    else:
        LCD_RST_PIN = 27
        LCD_DC_PIN = 25
        LCD_CS_PIN = 8
        LCD_BL_PIN = 24

    SPI = spidev.SpiDev(0, 0)

    def epd_digital_write(pin, value):
        GPIO.output(pin, value)

    def Driver_Delay_ms(xms):
        time.sleep(xms / 1000.0)

    def SPI_Write_Byte(data):
        SPI.writebytes(data)

    def GPIO_Init():
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(LCD_RST_PIN, GPIO.OUT)
        GPIO.setup(LCD_DC_PIN, GPIO.OUT)
        if _DISPLAY_TYPE not in ("ILI9341_320", "ST7789_320"):
            GPIO.setup(LCD_CS_PIN, GPIO.OUT)
        GPIO.setup(LCD_BL_PIN, GPIO.OUT)
        SPI.max_speed_hz = 9000000
        SPI.mode = 0b00
        SPI.cshigh = False
        SPI.lsbfirst = False
        SPI.threewire = False
        SPI.bits_per_word = 8
        return 0

### END OF FILE ###
