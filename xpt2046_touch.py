"""XPT2046 touch input on SPI0 CE1 for the 2.8-inch Waveshare LCD.

Each completed touch produces one existing RaspyJack button name. Swipes navigate;
screen edges navigate on taps and the center confirms. Calibration is configurable.
"""

import statistics
import time


class TouchInput:
    def __init__(self, config=None, gpio=None, spi=None, width=320, height=240):
        config = config or {}
        if gpio is None:
            import RPi.GPIO as gpio
        if spi is None:
            import spidev
            spi = spidev.SpiDev(0, int(config.get("cs", 1)))
        self.gpio, self.spi = gpio, spi
        self.spi.mode = 0
        self.spi.max_speed_hz = 2000000
        self.width, self.height = width, height
        self.irq = int(config.get("irq_pin", 17))
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.setup(self.irq, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
        self.x_min = int(config.get("x_min", 200))
        self.x_max = int(config.get("x_max", 3900))
        self.y_min = int(config.get("y_min", 200))
        self.y_max = int(config.get("y_max", 3900))
        self.swap_xy = bool(config.get("swap_xy", False))
        self.invert_x = bool(config.get("invert_x", False))
        self.invert_y = bool(config.get("invert_y", False))
        self.flip = bool(config.get("flip", False))
        self._start = None
        self._last = None
        self._last_sample = 0.0

    def close(self):
        self.spi.close()

    def _read_axis(self, command):
        data = self.spi.xfer2([command, 0, 0])
        return ((data[1] << 8) | data[2]) >> 3

    def _point(self):
        samples = [(self._read_axis(0xD0), self._read_axis(0x90)) for _ in range(5)]
        x, y = (int(statistics.median(axis)) for axis in zip(*samples))
        if self.swap_xy:
            x, y = y, x
        def scale(raw, low, high, limit):
            if high == low:
                return 0
            return max(0, min(limit - 1, round((raw - low) * (limit - 1) / (high - low))))
        x = scale(x, self.x_min, self.x_max, self.width)
        y = scale(y, self.y_min, self.y_max, self.height)
        if self.invert_x:
            x = self.width - 1 - x
        if self.invert_y:
            y = self.height - 1 - y
        if self.flip:
            x, y = self.width - 1 - x, self.height - 1 - y
        return x, y

    def poll(self):
        """Return a button on finger release, or None while idle/pressed."""
        pressed = self.gpio.input(self.irq) == 0
        if pressed:
            now = time.monotonic()
            if now - self._last_sample >= 0.015:
                point = self._point()
                if self._start is None:
                    self._start = point
                self._last = point
                self._last_sample = now
            return None
        if self._start is None:
            return None
        start, end = self._start, self._last or self._start
        self._start = self._last = None
        dx, dy = end[0] - start[0], end[1] - start[1]
        if max(abs(dx), abs(dy)) >= 35:
            if abs(dx) > abs(dy):
                return "KEY_RIGHT_PIN" if dx > 0 else "KEY_LEFT_PIN"
            return "KEY_DOWN_PIN" if dy > 0 else "KEY_UP_PIN"
        x, y = end
        if x < self.width * 0.2:
            return "KEY_LEFT_PIN"
        if x >= self.width * 0.8:
            return "KEY_RIGHT_PIN"
        if y < self.height * 0.25:
            return "KEY_UP_PIN"
        if y >= self.height * 0.75:
            return "KEY_DOWN_PIN"
        return "KEY_PRESS_PIN"


class EvdevTouchInput:
    """Gesture adapter for the kernel ADS7846 touchscreen driver."""

    def __init__(self, config=None, width=320, height=240):
        from evdev import InputDevice, ecodes, list_devices
        config = config or {}
        self.ecodes = ecodes
        candidates = [InputDevice(path) for path in list_devices()]
        self.device = next(
            (dev for dev in candidates if "ADS7846" in dev.name.upper()), None
        )
        if self.device is None:
            for dev in candidates:
                dev.close()
            raise RuntimeError("ADS7846 Touchscreen input device not found")
        for dev in candidates:
            if dev is not self.device:
                dev.close()
        self.width, self.height = width, height
        self.flip = bool(config.get("flip", False))
        self.invert_x = bool(config.get("invert_x", False))
        self.invert_y = bool(config.get("invert_y", False))
        self.swap_xy = bool(config.get("swap_xy", False))
        self._raw_x = self._raw_y = 0
        self._start = self._last = None
        self._pressed = False
        xinfo = self.device.absinfo(ecodes.ABS_X)
        yinfo = self.device.absinfo(ecodes.ABS_Y)
        # The ADS7846 reports a nominal 0..4095 range, but the resistive
        # surface reaches a smaller calibrated range.  Honour the per-panel
        # values from gui_conf.json so edge taps remain inside edge zones.
        self.x_min = int(config.get("x_min", xinfo.min))
        self.x_max = int(config.get("x_max", xinfo.max))
        self.y_min = int(config.get("y_min", yinfo.min))
        self.y_max = int(config.get("y_max", yinfo.max))

    def close(self):
        self.device.close()

    @staticmethod
    def _scale(value, low, high, limit):
        if high == low:
            return 0
        return max(0, min(limit - 1, round((value - low) * (limit - 1) / (high - low))))

    def _point(self):
        x, y = self._raw_x, self._raw_y
        if self.swap_xy:
            x, y = y, x
            x_min, x_max, y_min, y_max = self.y_min, self.y_max, self.x_min, self.x_max
        else:
            x_min, x_max, y_min, y_max = self.x_min, self.x_max, self.y_min, self.y_max
        x = self._scale(x, x_min, x_max, self.width)
        y = self._scale(y, y_min, y_max, self.height)
        if self.invert_x:
            x = self.width - 1 - x
        if self.invert_y:
            y = self.height - 1 - y
        if self.flip:
            x, y = self.width - 1 - x, self.height - 1 - y
        return x, y

    def _button(self, start, end):
        dx, dy = end[0] - start[0], end[1] - start[1]
        if max(abs(dx), abs(dy)) >= 35:
            if abs(dx) > abs(dy):
                return "KEY_RIGHT_PIN" if dx > 0 else "KEY_LEFT_PIN"
            return "KEY_DOWN_PIN" if dy > 0 else "KEY_UP_PIN"
        x, y = end
        if x < self.width * 0.2:
            return "KEY_LEFT_PIN"
        if x >= self.width * 0.8:
            return "KEY_RIGHT_PIN"
        if y < self.height * 0.25:
            return "KEY_UP_PIN"
        if y >= self.height * 0.75:
            return "KEY_DOWN_PIN"
        return "KEY_PRESS_PIN"

    def poll(self):
        result = None
        try:
            # evdev.read() returns a generator; EAGAIN may be raised while
            # consuming it rather than while creating it.
            events = list(self.device.read())
        except BlockingIOError:
            return None
        for event in events:
            if event.type == self.ecodes.EV_ABS:
                if event.code == self.ecodes.ABS_X:
                    self._raw_x = event.value
                elif event.code == self.ecodes.ABS_Y:
                    self._raw_y = event.value
            elif event.type == self.ecodes.EV_KEY and event.code == self.ecodes.BTN_TOUCH:
                if event.value:
                    self._pressed = True
                    # ABS coordinates belonging to this contact arrive in the
                    # following event frame.  Reusing the previous contact's
                    # coordinates here turns taps into random swipes.
                    self._start = self._last = None
                elif self._pressed:
                    self._pressed = False
                    start, end = self._start, self._last or self._start
                    self._start = self._last = None
                    if start is not None:
                        result = self._button(start, end)
            elif (event.type == self.ecodes.EV_SYN and
                  event.code == self.ecodes.SYN_REPORT and self._pressed):
                point = self._point()
                if self._start is None:
                    self._start = point
                self._last = point
        return result
