 # -*- coding:UTF-8 -*-
 ##
 # | file      	:	LCD_1IN44.py
 # |	version		:	V3.0
 # | date		:	2018-07-16
 # | function	:	On the ST7735S / ST7789 chip driver and clear screen, drawing lines, drawing,
 #					writing and other functions to achieve
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

import LCD_Config
import RPi.GPIO as GPIO
import time
import numpy as np
import os
import json
from PIL import Image as PILImage, ImageOps

# ---------------------------------------------------------------------------
# Display type detection from gui_conf.json
# Supported: "ST7735_128", "ST7735_320", "ST7789_240", "ST7789_320",
#            "ILI9341_320", "ST7789_320_FB", "CARDPUTER_320"
# ---------------------------------------------------------------------------
_DISPLAY_TYPE = "ST7735_128"  # default

_CONF_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_conf.json"),
    "/root/Raspyjack/gui_conf.json",
]
for _p in _CONF_PATHS:
    if os.path.isfile(_p):
        try:
            with open(_p, "r") as _f:
                _conf = json.load(_f)
            _DISPLAY_TYPE = _conf.get("DISPLAY", {}).get("type", _DISPLAY_TYPE)
            _FLIP_180 = _conf.get("DISPLAY", {}).get("flip", False)
        except Exception:
            _FLIP_180 = False
        break
else:
    _FLIP_180 = False

# Hardware auto-detect fallback for CardputerZero
if _DISPLAY_TYPE not in ("CARDPUTER_320", "ST7789_320_FB"):
    for _i in range(4):
        try:
            with open(f"/sys/class/graphics/fb{_i}/name", "r") as _fb:
                if any(n in _fb.read() for n in ("st7789v_m5st", "panel-mipi-dbi")):
                    _DISPLAY_TYPE = "CARDPUTER_320"
                    break
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Resolution constants based on display type
# ---------------------------------------------------------------------------
if _DISPLAY_TYPE == "CARDPUTER_320":
    LCD_WIDTH  = 320
    LCD_HEIGHT = 170
    LCD_X = 0
    LCD_Y = 0
    LCD_X_MAXPIXEL = 320
    LCD_Y_MAXPIXEL = 170
elif _DISPLAY_TYPE == "ST7789_320_FB":
    LCD_WIDTH = 320
    LCD_HEIGHT = 240
    LCD_X = LCD_Y = 0
    LCD_X_MAXPIXEL = 320
    LCD_Y_MAXPIXEL = 240
elif _DISPLAY_TYPE == "ST7789_240":
    LCD_WIDTH  = 240
    LCD_HEIGHT = 240
    LCD_X = 0
    LCD_Y = 0
    LCD_X_MAXPIXEL = 240
    LCD_Y_MAXPIXEL = 240
elif _DISPLAY_TYPE == "ST7789_320":
    # Waveshare 2.8inch RPi LCD (A) Rev2.0/Rev2.1.  The ST7789V has a
    # native 240x320 address space; MADCTL rotates it to 320x240 below.
    LCD_WIDTH = 320
    LCD_HEIGHT = 240
    LCD_X = LCD_Y = 0
    LCD_X_MAXPIXEL = 320
    LCD_Y_MAXPIXEL = 240
elif _DISPLAY_TYPE == "ILI9341_320":
    LCD_WIDTH = 320
    LCD_HEIGHT = 240
    LCD_X = LCD_Y = 0
    LCD_X_MAXPIXEL = 320
    LCD_Y_MAXPIXEL = 240
elif _DISPLAY_TYPE == "ST7735_320":
    # Your 320x240 ST7735R panel. Typical offset for 320x240 modules is
    # X=2, Y=3; if the image is sheared or cut off at an edge, tweak these
    # (and the MADCTL values in LCD_SetGramScanWay) until the panel aligns.
    LCD_WIDTH  = 320
    LCD_HEIGHT = 240
    LCD_X = 2
    LCD_Y = 3
    LCD_X_MAXPIXEL = 336
    LCD_Y_MAXPIXEL = 414
else:
    # ST7735_128 — original 1.44" display (default)
    LCD_WIDTH  = 128
    LCD_HEIGHT = 128
    LCD_X = 2
    LCD_Y = 1
    LCD_X_MAXPIXEL = 132
    LCD_Y_MAXPIXEL = 162

# ---------------------------------------------------------------------------
# Scale helper – payloads import this: from LCD_1in44 import S
# All coordinates are authored for 128; S() adapts them to the actual panel.
# ---------------------------------------------------------------------------
if _DISPLAY_TYPE == "CARDPUTER_320":
    LCD_SCALE = LCD_HEIGHT / 128  # 1.328 — use height (constraining dimension) for widescreen
else:
    LCD_SCALE = LCD_WIDTH / 128  # 1.0 on 128x128, 1.875 on 240x240

def S(v):
    """Scale a 128-base pixel value to the current display resolution."""
    return int(v * LCD_SCALE)

# WebUI frame mirror (used by device_server.py)
_FRAME_MIRROR_PATH = os.environ.get("RJ_FRAME_PATH", "/dev/shm/raspyjack_last.jpg")
_FRAME_MIRROR_ENABLED = os.environ.get("RJ_FRAME_MIRROR", "1") != "0"
_CARDPUTER_FRAME_PATH = os.environ.get("RJ_CARDPUTER_FRAME_PATH", "/dev/shm/raspyjack_cardputer.jpg")
_CARDPUTER_FRAME_ENABLED = os.environ.get("RJ_CARDPUTER_FRAME_ENABLED", "1") != "0"
_CARDPUTER_FRAME_MODE = str(os.environ.get("RJ_CARDPUTER_FRAME_MODE", "stretch") or "stretch").strip().lower()
_CARDPUTER_FRAME_WIDTH = max(1, int(os.environ.get("RJ_CARDPUTER_FRAME_WIDTH", "240")))
_CARDPUTER_FRAME_HEIGHT = max(1, int(os.environ.get("RJ_CARDPUTER_FRAME_HEIGHT", "135")))
_CARDPUTER_FRAME_QUALITY = min(100, max(1, int(os.environ.get("RJ_CARDPUTER_FRAME_QUALITY", "76"))))
try:
    _frame_fps = float(os.environ.get("RJ_FRAME_FPS", "10"))
    _FRAME_MIRROR_INTERVAL = 1.0 / max(1.0, _frame_fps)
except Exception:
    _FRAME_MIRROR_INTERVAL = 0.1
_last_frame_save = 0.0

try:
    _resampling_lanczos = PILImage.Resampling.LANCZOS
except AttributeError:
    _resampling_lanczos = PILImage.LANCZOS


def _build_cardputer_frame(src_image):
    if _CARDPUTER_FRAME_MODE == "stretch":
        return src_image.resize((_CARDPUTER_FRAME_WIDTH, _CARDPUTER_FRAME_HEIGHT), _resampling_lanczos)
    if _CARDPUTER_FRAME_MODE == "contain":
        return ImageOps.contain(src_image, (_CARDPUTER_FRAME_WIDTH, _CARDPUTER_FRAME_HEIGHT), _resampling_lanczos)
    return ImageOps.fit(src_image, (_CARDPUTER_FRAME_WIDTH, _CARDPUTER_FRAME_HEIGHT), _resampling_lanczos)


def _save_cardputer_frame(src_image):
    if not _CARDPUTER_FRAME_ENABLED:
        return
    try:
        cardputer_frame = _build_cardputer_frame(src_image)
        if cardputer_frame.size != (_CARDPUTER_FRAME_WIDTH, _CARDPUTER_FRAME_HEIGHT):
            canvas = PILImage.new("RGB", (_CARDPUTER_FRAME_WIDTH, _CARDPUTER_FRAME_HEIGHT), "black")
            offset_x = max(0, (_CARDPUTER_FRAME_WIDTH - cardputer_frame.width) // 2)
            offset_y = max(0, (_CARDPUTER_FRAME_HEIGHT - cardputer_frame.height) // 2)
            canvas.paste(cardputer_frame, (offset_x, offset_y))
            cardputer_frame = canvas
        cardputer_frame.save(_CARDPUTER_FRAME_PATH, "JPEG", quality=_CARDPUTER_FRAME_QUALITY, subsampling=0)
    except Exception:
        pass

#scanning method
L2R_U2D = 1
L2R_D2U = 2
R2L_U2D = 3
R2L_D2U = 4
U2D_L2R = 5
U2D_R2L = 6
D2U_L2R = 7
D2U_R2L = 8
SCAN_DIR_DFT = U2D_R2L


class LCD:
    def __init__(self):
        self.width = LCD_WIDTH
        self.height = LCD_HEIGHT
        self.LCD_Scan_Dir = SCAN_DIR_DFT
        self.LCD_X_Adjust = LCD_X
        self.LCD_Y_Adjust = LCD_Y
        self.display_type = _DISPLAY_TYPE

    """    Hardware reset     """
    def  LCD_Reset(self):
        GPIO.output(LCD_Config.LCD_RST_PIN, GPIO.HIGH)
        LCD_Config.Driver_Delay_ms(100)
        GPIO.output(LCD_Config.LCD_RST_PIN, GPIO.LOW)
        LCD_Config.Driver_Delay_ms(100)
        GPIO.output(LCD_Config.LCD_RST_PIN, GPIO.HIGH)
        LCD_Config.Driver_Delay_ms(100)

    """    Write register address and data     """
    def  LCD_WriteReg(self, Reg):
        GPIO.output(LCD_Config.LCD_DC_PIN, GPIO.LOW)
        LCD_Config.SPI_Write_Byte([Reg])

    def LCD_WriteData_8bit(self, Data):
        GPIO.output(LCD_Config.LCD_DC_PIN, GPIO.HIGH)
        LCD_Config.SPI_Write_Byte([Data])

    def LCD_WriteData_NLen16Bit(self, Data, DataLen):
        GPIO.output(LCD_Config.LCD_DC_PIN, GPIO.HIGH)
        for i in range(0, DataLen):
            LCD_Config.SPI_Write_Byte([Data >> 8])
            LCD_Config.SPI_Write_Byte([Data & 0xff])

    # ------------------------------------------------------------------
    # ST7735S register initialization (1.44" 128x128)
    # ------------------------------------------------------------------
    def _LCD_InitReg_ST7735(self):
        #ST7735R Frame Rate
        self.LCD_WriteReg(0xB1)
        self.LCD_WriteData_8bit(0x01)
        self.LCD_WriteData_8bit(0x2C)
        self.LCD_WriteData_8bit(0x2D)

        self.LCD_WriteReg(0xB2)
        self.LCD_WriteData_8bit(0x01)
        self.LCD_WriteData_8bit(0x2C)
        self.LCD_WriteData_8bit(0x2D)

        self.LCD_WriteReg(0xB3)
        self.LCD_WriteData_8bit(0x01)
        self.LCD_WriteData_8bit(0x2C)
        self.LCD_WriteData_8bit(0x2D)
        self.LCD_WriteData_8bit(0x01)
        self.LCD_WriteData_8bit(0x2C)
        self.LCD_WriteData_8bit(0x2D)

        #Column inversion
        self.LCD_WriteReg(0xB4)
        self.LCD_WriteData_8bit(0x07)

        #ST7735R Power Sequence
        self.LCD_WriteReg(0xC0)
        self.LCD_WriteData_8bit(0xA2)
        self.LCD_WriteData_8bit(0x02)
        self.LCD_WriteData_8bit(0x84)
        self.LCD_WriteReg(0xC1)
        self.LCD_WriteData_8bit(0xC5)

        self.LCD_WriteReg(0xC2)
        self.LCD_WriteData_8bit(0x0A)
        self.LCD_WriteData_8bit(0x00)

        self.LCD_WriteReg(0xC3)
        self.LCD_WriteData_8bit(0x8A)
        self.LCD_WriteData_8bit(0x2A)
        self.LCD_WriteReg(0xC4)
        self.LCD_WriteData_8bit(0x8A)
        self.LCD_WriteData_8bit(0xEE)

        self.LCD_WriteReg(0xC5)#VCOM
        self.LCD_WriteData_8bit(0x0E)

        #ST7735R Gamma Sequence
        self.LCD_WriteReg(0xe0)
        self.LCD_WriteData_8bit(0x0f)
        self.LCD_WriteData_8bit(0x1a)
        self.LCD_WriteData_8bit(0x0f)
        self.LCD_WriteData_8bit(0x18)
        self.LCD_WriteData_8bit(0x2f)
        self.LCD_WriteData_8bit(0x28)
        self.LCD_WriteData_8bit(0x20)
        self.LCD_WriteData_8bit(0x22)
        self.LCD_WriteData_8bit(0x1f)
        self.LCD_WriteData_8bit(0x1b)
        self.LCD_WriteData_8bit(0x23)
        self.LCD_WriteData_8bit(0x37)
        self.LCD_WriteData_8bit(0x00)
        self.LCD_WriteData_8bit(0x07)
        self.LCD_WriteData_8bit(0x02)
        self.LCD_WriteData_8bit(0x10)

        self.LCD_WriteReg(0xe1)
        self.LCD_WriteData_8bit(0x0f)
        self.LCD_WriteData_8bit(0x1b)
        self.LCD_WriteData_8bit(0x0f)
        self.LCD_WriteData_8bit(0x17)
        self.LCD_WriteData_8bit(0x33)
        self.LCD_WriteData_8bit(0x2c)
        self.LCD_WriteData_8bit(0x29)
        self.LCD_WriteData_8bit(0x2e)
        self.LCD_WriteData_8bit(0x30)
        self.LCD_WriteData_8bit(0x30)
        self.LCD_WriteData_8bit(0x39)
        self.LCD_WriteData_8bit(0x3f)
        self.LCD_WriteData_8bit(0x00)
        self.LCD_WriteData_8bit(0x07)
        self.LCD_WriteData_8bit(0x03)
        self.LCD_WriteData_8bit(0x10)

        #Enable test command
        self.LCD_WriteReg(0xF0)
        self.LCD_WriteData_8bit(0x01)

        #Disable ram power save mode
        self.LCD_WriteReg(0xF6)
        self.LCD_WriteData_8bit(0x00)

        #65k mode
        self.LCD_WriteReg(0x3A)
        self.LCD_WriteData_8bit(0x05)

    # ------------------------------------------------------------------
    # ST7789 register initialization (1.3" 240x240)
    # ------------------------------------------------------------------
    def _LCD_InitReg_ST7789(self):
        # Memory Data Access Control
        self.LCD_WriteReg(0x36)
        self.LCD_WriteData_8bit(0x00)

        # RGB 5-6-5-bit color format
        self.LCD_WriteReg(0x3A)
        self.LCD_WriteData_8bit(0x05)

        # Porch Setting
        self.LCD_WriteReg(0xB2)
        self.LCD_WriteData_8bit(0x0C)
        self.LCD_WriteData_8bit(0x0C)
        self.LCD_WriteData_8bit(0x00)
        self.LCD_WriteData_8bit(0x33)
        self.LCD_WriteData_8bit(0x33)

        # Gate Control
        self.LCD_WriteReg(0xB7)
        self.LCD_WriteData_8bit(0x35)

        # VCOM Setting (higher value reduces ghosting/image retention)
        self.LCD_WriteReg(0xBB)
        self.LCD_WriteData_8bit(0x2B)

        # LCM Control
        self.LCD_WriteReg(0xC0)
        self.LCD_WriteData_8bit(0x2C)

        # VDV and VRH Command Enable
        self.LCD_WriteReg(0xC2)
        self.LCD_WriteData_8bit(0x01)

        # VRH Set (slightly higher for cleaner transitions)
        self.LCD_WriteReg(0xC3)
        self.LCD_WriteData_8bit(0x15)

        # VDV Set
        self.LCD_WriteReg(0xC4)
        self.LCD_WriteData_8bit(0x20)

        # Frame Rate Control in Normal Mode (0x01 = ~111Hz, reduces ghosting)
        self.LCD_WriteReg(0xC6)
        self.LCD_WriteData_8bit(0x01)

        # Power Control 1
        self.LCD_WriteReg(0xD0)
        self.LCD_WriteData_8bit(0xA4)
        self.LCD_WriteData_8bit(0xA1)

        # Positive Voltage Gamma Control
        self.LCD_WriteReg(0xE0)
        self.LCD_WriteData_8bit(0xD0)
        self.LCD_WriteData_8bit(0x04)
        self.LCD_WriteData_8bit(0x0D)
        self.LCD_WriteData_8bit(0x11)
        self.LCD_WriteData_8bit(0x13)
        self.LCD_WriteData_8bit(0x2B)
        self.LCD_WriteData_8bit(0x3F)
        self.LCD_WriteData_8bit(0x54)
        self.LCD_WriteData_8bit(0x4C)
        self.LCD_WriteData_8bit(0x18)
        self.LCD_WriteData_8bit(0x0D)
        self.LCD_WriteData_8bit(0x0B)
        self.LCD_WriteData_8bit(0x1F)
        self.LCD_WriteData_8bit(0x23)

        # Negative Voltage Gamma Control
        self.LCD_WriteReg(0xE1)
        self.LCD_WriteData_8bit(0xD0)
        self.LCD_WriteData_8bit(0x04)
        self.LCD_WriteData_8bit(0x0C)
        self.LCD_WriteData_8bit(0x11)
        self.LCD_WriteData_8bit(0x13)
        self.LCD_WriteData_8bit(0x2C)
        self.LCD_WriteData_8bit(0x3F)
        self.LCD_WriteData_8bit(0x44)
        self.LCD_WriteData_8bit(0x51)
        self.LCD_WriteData_8bit(0x2F)
        self.LCD_WriteData_8bit(0x1F)
        self.LCD_WriteData_8bit(0x1F)
        self.LCD_WriteData_8bit(0x20)
        self.LCD_WriteData_8bit(0x23)

        # Display Inversion On (ST7789 needs this for correct colors)
        self.LCD_WriteReg(0x21)

    def _LCD_InitReg_ST7789_Waveshare28(self):
        """Waveshare 2.8-inch RPi LCD (A) Rev2.1 ST7789V/IPS sequence."""
        for register, values in (
            (0x3A, (0x55,)),                    # RGB565
            (0xB2, (0x05, 0x05, 0x00, 0x33, 0x33)),
            (0xB7, (0x75,)),
            (0xC2, (0x01, 0xFF)),
            (0xC3, (0x13,)),
            (0xC4, (0x20,)),
            (0xBB, (0x22,)),
            (0xC5, (0x20,)),
            (0xD0, (0xA4, 0xA1)),
            (0xE0, (0xD0, 0x05, 0x0A, 0x09, 0x08, 0x05, 0x2E,
                    0x44, 0x45, 0x0F, 0x17, 0x16, 0x2B, 0x33)),
            (0xE1, (0xD0, 0x05, 0x0A, 0x09, 0x08, 0x05, 0x2E,
                    0x43, 0x45, 0x0F, 0x16, 0x16, 0x2B, 0x33)),
            (0x21, ()),                         # IPS inversion
        ):
            self.LCD_WriteReg(register)
            for value in values:
                self.LCD_WriteData_8bit(value)

    # ------------------------------------------------------------------
    # Dispatch to the correct init register sequence
    # ------------------------------------------------------------------
    def LCD_InitReg(self):
        if self.display_type == "ST7789_320":
            self._LCD_InitReg_ST7789_Waveshare28()
        elif self.display_type == "ST7789_240":
            self._LCD_InitReg_ST7789()
        elif self.display_type == "ILI9341_320":
            self._LCD_InitReg_ILI9341()
        else:
            self._LCD_InitReg_ST7735()

    def _LCD_InitReg_ILI9341(self):
        """ILI9341 RGB565, SPI four-wire mode."""
        for register, values in (
            (0x01, ()),       # software reset
            (0xCF, (0x00, 0xC1, 0x30)),
            (0xED, (0x64, 0x03, 0x12, 0x81)),
            (0xE8, (0x85, 0x00, 0x78)),
            (0xCB, (0x39, 0x2C, 0x00, 0x34, 0x02)),
            (0xF7, (0x20,)),
            (0xEA, (0x00, 0x00)),
            (0xC0, (0x23,)),
            (0xC1, (0x10,)),
            (0xC5, (0x3E, 0x28)),
            (0xC7, (0x86,)),
            (0xB1, (0x00, 0x18)),
            (0xB6, (0x08, 0x82, 0x27)),
            (0xF2, (0x00,)),
            (0x26, (0x01,)),
            (0x3A, (0x55,)),  # 16-bit pixels
        ):
            self.LCD_WriteReg(register)
            if register == 0x01:
                LCD_Config.Driver_Delay_ms(150)
            for value in values:
                self.LCD_WriteData_8bit(value)

    #********************************************************************************
    #function:	Set the display scan and color transfer modes
    #parameter:
    #		Scan_dir   :   Scan direction
    #		Colorchose :   RGB or GBR color format
    #********************************************************************************
    def LCD_SetGramScanWay(self, Scan_dir):
        #Get the screen scan direction
        self.LCD_Scan_Dir = Scan_dir

        if self.display_type == "ILI9341_320":
            # Native controller coordinates are 240x320; MV makes the UI landscape.
            self.width, self.height = LCD_WIDTH, LCD_HEIGHT
            self.LCD_X_Adjust = self.LCD_Y_Adjust = 0
            self.LCD_WriteReg(0x36)
            self.LCD_WriteData_8bit(0x28)  # MV + BGR
            return
        if self.display_type in ("ST7789_240", "ST7789_320"):
            # ST7789: simpler MADCTL handling
            if (Scan_dir == L2R_U2D) or (Scan_dir == L2R_D2U) or (Scan_dir == R2L_U2D) or (Scan_dir == R2L_D2U):
                self.width  = LCD_HEIGHT
                self.height = LCD_WIDTH
            else:
                self.width  = LCD_WIDTH
                self.height = LCD_HEIGHT

            madctl = 0x00
            if Scan_dir == L2R_U2D:
                madctl = 0x00
            elif Scan_dir == L2R_D2U:
                madctl = 0x80
            elif Scan_dir == R2L_U2D:
                madctl = 0x40
            elif Scan_dir == R2L_D2U:
                madctl = 0xC0
            elif Scan_dir == U2D_L2R:
                madctl = 0x20
            elif Scan_dir == U2D_R2L:
                madctl = 0x60
            elif Scan_dir == D2U_L2R:
                madctl = 0xA0
            else:  # D2U_R2L
                madctl = 0xE0

            self.LCD_X_Adjust = LCD_X
            self.LCD_Y_Adjust = LCD_Y

            self.LCD_WriteReg(0x36)
            self.LCD_WriteData_8bit(madctl)
            return

        # ST7735S: original logic
        #Get GRAM and LCD width and height
        if (Scan_dir == L2R_U2D) or (Scan_dir == L2R_D2U) or (Scan_dir == R2L_U2D) or (Scan_dir == R2L_D2U) :
            self.width	= LCD_HEIGHT
            self.height 	= LCD_WIDTH
            if Scan_dir == L2R_U2D:
                MemoryAccessReg_Data = 0X00 | 0x00
            elif Scan_dir == L2R_D2U:
                MemoryAccessReg_Data = 0X00 | 0x80
            elif Scan_dir == R2L_U2D:
                MemoryAccessReg_Data = 0x40 | 0x00
            else:		#R2L_D2U:
                MemoryAccessReg_Data = 0x40 | 0x80
        else:
            self.width	= LCD_WIDTH
            self.height 	= LCD_HEIGHT
            if Scan_dir == U2D_L2R:
                MemoryAccessReg_Data = 0X00 | 0x00 | 0x20
            elif Scan_dir == U2D_R2L:
                MemoryAccessReg_Data = 0X00 | 0x40 | 0x20
            elif Scan_dir == D2U_L2R:
                MemoryAccessReg_Data = 0x80 | 0x00 | 0x20
            else:		#R2L_D2U
                MemoryAccessReg_Data = 0x40 | 0x80 | 0x20

        #please set (MemoryAccessReg_Data & 0x10) != 1
        if (MemoryAccessReg_Data & 0x10) != 1:
            self.LCD_X_Adjust = LCD_Y
            self.LCD_Y_Adjust = LCD_X
        else:
            self.LCD_X_Adjust = LCD_X
            self.LCD_Y_Adjust = LCD_Y

        # Set the read / write scan direction of the frame memory
        self.LCD_WriteReg(0x36)		#MX, MY, RGB mode
        self.LCD_WriteData_8bit( MemoryAccessReg_Data | 0x08)	#0x08 set RGB

    #/********************************************************************************
    #function:
    #			initialization
    #********************************************************************************/
    def LCD_Init(self, Lcd_ScanDir=None):
        if (LCD_Config.GPIO_Init() != 0):
            return -1

        if self.display_type in ("CARDPUTER_320", "ST7789_320_FB"):
            return 0

        # Set SPI speed based on display type
        if self.display_type == "ST7789_240":
            LCD_Config.SPI.max_speed_hz = 62000000  # ST7789 max: 62.5MHz
        elif self.display_type == "ST7789_320":
            # Rev2.1 boards vary in SPI signal quality.  1 MHz is deliberately
            # conservative and prevents the snow/stripe corruption seen on
            # marginal HAT connectors while remaining usable for this UI.
            LCD_Config.SPI.max_speed_hz = 1000000
        elif self.display_type == "ILI9341_320":
            # 8 MHz is reliable on the Waveshare 2.8-inch HAT and leaves
            # enough signal margin on a Zero 2 W.  Faster clocks can produce
            # random pixels and horizontal stripes when the connector or
            # board revision has weaker SPI signal integrity.
            LCD_Config.SPI.max_speed_hz = 8000000
        else:
            LCD_Config.SPI.max_speed_hz = 9000000

        #Turn on the backlight
        GPIO.output(LCD_Config.LCD_BL_PIN,GPIO.HIGH)

        #Hardware reset
        self.LCD_Reset()

        # Waveshare Rev2.1 follows the order from its official ST7789V
        # framebuffer driver: sleep-out first, then panel tuning registers.
        if self.display_type == "ST7789_320":
            self.LCD_WriteReg(0x11)
            LCD_Config.Driver_Delay_ms(120)
            self.LCD_InitReg()
            self.LCD_SetGramScanWay(Lcd_ScanDir or SCAN_DIR_DFT)
            self.LCD_WriteReg(0x29)
            LCD_Config.Driver_Delay_ms(20)
            return

        #Set the initialization register
        self.LCD_InitReg()

        #Set the display scan and color transfer modes
        self.LCD_SetGramScanWay(Lcd_ScanDir or SCAN_DIR_DFT)
        LCD_Config.Driver_Delay_ms(200)

        #sleep out
        self.LCD_WriteReg(0x11)
        LCD_Config.Driver_Delay_ms(120)

        #Turn on the LCD display
        self.LCD_WriteReg(0x29)

    #/********************************************************************************
    #function:	Sets the start position and size of the display area
    #parameter:
    #	Xstart 	:   X direction Start coordinates
    #	Ystart  :   Y direction Start coordinates
    #	Xend    :   X direction end coordinates
    #	Yend    :   Y direction end coordinates
    #********************************************************************************/
    def LCD_SetWindows(self, Xstart, Ystart, Xend, Yend):
        #set the X coordinates
        self.LCD_WriteReg(0x2A)
        self.LCD_WriteData_8bit((Xstart + self.LCD_X_Adjust) >> 8)
        self.LCD_WriteData_8bit((Xstart + self.LCD_X_Adjust) & 0xff)
        self.LCD_WriteData_8bit((Xend - 1 + self.LCD_X_Adjust) >> 8)
        self.LCD_WriteData_8bit((Xend - 1 + self.LCD_X_Adjust) & 0xff)

        #set the Y coordinates
        self.LCD_WriteReg(0x2B)
        self.LCD_WriteData_8bit((Ystart + self.LCD_Y_Adjust) >> 8)
        self.LCD_WriteData_8bit((Ystart + self.LCD_Y_Adjust) & 0xff)
        self.LCD_WriteData_8bit((Yend - 1 + self.LCD_Y_Adjust) >> 8)
        self.LCD_WriteData_8bit((Yend - 1 + self.LCD_Y_Adjust) & 0xff)

        self.LCD_WriteReg(0x2C)

    def LCD_Clear(self):
        if self.display_type in ("CARDPUTER_320", "ST7789_320_FB"):
            LCD_Config.fb_write(b'\x00' * LCD_Config.FB_SIZE)
            return
        _buffer = [0x00]*(self.width * self.height * 2)
        self.LCD_SetWindows(0, 0, self.width, self.height)
        GPIO.output(LCD_Config.LCD_DC_PIN, GPIO.HIGH)
        for i in range(0,len(_buffer),4096):
            LCD_Config.SPI_Write_Byte(_buffer[i:i+4096])

    def LCD_ShowImage(self,Image,Xstart,Ystart):
        if (Image == None):
            return
        if _FLIP_180:
            Image = Image.rotate(180)
        imwidth, imheight = Image.size
        if imwidth != self.width or imheight != self.height:
            Image = Image.resize((self.width, self.height))

        if self.display_type in ("CARDPUTER_320", "ST7789_320_FB"):
            img = Image.convert("RGB")
            arr = np.asarray(img)
            r = (arr[..., 0].astype(np.uint16) >> 3) << 11
            g = (arr[..., 1].astype(np.uint16) >> 2) << 5
            b = arr[..., 2].astype(np.uint16) >> 3
            rgb565 = (r | g | b).astype(np.uint16).tobytes()
            LCD_Config.fb_write(rgb565)
        else:
            img = np.asarray(Image.convert("RGB"))
            pix = np.zeros((self.height,self.width,2), dtype = np.uint8)
            pix[...,[0]] = np.add(np.bitwise_and(img[...,[0]],0xF8),np.right_shift(img[...,[1]],5))
            pix[...,[1]] = np.add(np.bitwise_and(np.left_shift(img[...,[1]],3),0xE0),np.right_shift(img[...,[2]],3))
            pix = pix.flatten().tolist()
            self.LCD_SetWindows(0, 0, self.width , self.height)
            GPIO.output(LCD_Config.LCD_DC_PIN, GPIO.HIGH)
            for i in range(0,len(pix),4096):
                LCD_Config.SPI_Write_Byte(pix[i:i+4096])

        # Mirror the LCD frame for remote clients (throttled)
        if _FRAME_MIRROR_ENABLED or _CARDPUTER_FRAME_ENABLED:
            global _last_frame_save
            try:
                now = time.monotonic()
                if (now - _last_frame_save) >= _FRAME_MIRROR_INTERVAL:
                    if _FRAME_MIRROR_ENABLED:
                        Image.save(_FRAME_MIRROR_PATH, "JPEG", quality=80)
                    # Raw frame for HDMI mirror (no compression, no decode needed)
                    try:
                        raw = Image.convert("RGB").tobytes()
                        with open("/dev/shm/raspyjack_raw.rgb", "wb") as _rf:
                            _rf.write(raw)
                    except Exception:
                        pass
                    _save_cardputer_frame(Image)
                    _last_frame_save = now
            except Exception:
                pass
