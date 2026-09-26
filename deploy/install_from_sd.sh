#!/usr/bin/env bash
# Run as root on the Pi after placing raspyjack-ili9341-zero2w.tar.gz beside this script.
set -euo pipefail

if (( EUID != 0 )); then
  echo "Run with: sudo bash /boot/firmware/install-raspyjack-from-sd.sh" >&2
  exit 1
fi

BOOT_DIR=$(cd "$(dirname "$0")" && pwd)
ARCHIVE="$BOOT_DIR/raspyjack-ili9341-zero2w.tar.gz"
DEST=/root/Raspyjack
test -f "$ARCHIVE" || { echo "Archive missing: $ARCHIVE" >&2; exit 1; }
if test -f "$BOOT_DIR/raspyjack-ili9341-zero2w.sha256"; then
  (cd "$BOOT_DIR" && sha256sum -c raspyjack-ili9341-zero2w.sha256)
fi

BACKUP=""
if test -e "$DEST"; then
  BACKUP="${DEST}.before-ili9341-$(date +%Y%m%d-%H%M%S)"
  mv "$DEST" "$BACKUP"
  echo "Previous installation saved at $BACKUP"
fi
mkdir -p "$DEST"
tar -xzf "$ARCHIVE" -C "$DEST"
mkdir -p "$DEST/loot"
if test -n "$BACKUP" && test -f "$BACKUP/gui_conf.json"; then
  cp "$BACKUP/gui_conf.json" "$DEST/gui_conf.json"
fi

python3 - <<'PY'
import json
from pathlib import Path
p = Path('/root/Raspyjack/gui_conf.json')
if p.exists():
    data = json.loads(p.read_text())
else:
    data = {
        'COLORS': {
            'BACKGROUND': '#000000', 'BORDER': '#05ff00',
            'GAMEPAD': '#141494', 'GAMEPAD_FILL': '#eeeeee',
            'SELECTED_TEXT': '#00ff55', 'SELECTED_TEXT_BACKGROUND': '#2d0fff',
            'TEXT': '#05ff00'},
        'LOCK': {'auto_lock_seconds': 0, 'enabled': False, 'pin_hash': ''},
        'PATHS': {
            'IMAGEBROWSER_START': '/root/Raspyjack/img/',
            'SCREENSAVER_GIF': '/root/Raspyjack/img/screensaver/default.gif'},
        'PINS': {
            'KEY1_PIN': 21, 'KEY2_PIN': 20, 'KEY3_PIN': 16,
            'KEY_DOWN_PIN': 19, 'KEY_LEFT_PIN': 5,
            'KEY_PRESS_PIN': 13, 'KEY_RIGHT_PIN': 26, 'KEY_UP_PIN': 6}}
data.setdefault('DISPLAY', {})['type'] = 'ST7789_320_FB'
data['DISPLAY'].setdefault('flip', False)
data.setdefault('TOUCH', {'cs': 1, 'irq_pin': 17})
p.write_text(json.dumps(data, indent=2) + '\n')
PY

python3 -m py_compile "$DEST/LCD_Config.py" "$DEST/LCD_1in44.py" "$DEST/xpt2046_touch.py" "$DEST/raspyjack.py"

MISSING=$(PYTHONPATH="$DEST" python3 - <<'PY'
import importlib.util
required = ('netifaces', 'scapy', 'smbus', 'pyudev', 'serial', 'PIL',
            'RPi.GPIO', 'spidev', 'numpy', 'requests')
print(' '.join(name for name in required if importlib.util.find_spec(name.split('.')[0]) is None))
PY
)
if test -n "$MISSING"; then
  echo "RaspyJack files installed, but these Python modules are missing: $MISSING" >&2
  echo "Dependencies must be installed before enabling the service." >&2
  exit 2
fi

CFG=/boot/firmware/config.txt
test -f "$CFG" || CFG=/boot/config.txt
python3 - "$CFG" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
text = p.read_text()
for line in text.splitlines():
    if line.startswith('dtoverlay=waveshare28a-v2') or line.startswith('dtoverlay=ads7846'):
        text = text.replace(line, '# disabled for RaspyJack direct SPI: ' + line)
if 'dtparam=spi=on' not in text:
    text += '\ndtparam=spi=on\n'
if 'dtoverlay=spi0-2cs' not in text:
    text += 'dtoverlay=spi0-2cs\n'
p.write_text(text)
PY

cat > /etc/systemd/system/raspyjack.service <<'UNIT'
[Unit]
Description=RaspyJack UI Service
After=local-fs.target

[Service]
Type=simple
WorkingDirectory=/root/Raspyjack
ExecStart=/usr/bin/python3 /root/Raspyjack/raspyjack.py
Restart=on-failure
User=root
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=/root/Raspyjack

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable raspyjack.service
echo "RaspyJack installed. Reboot, then check: systemctl status raspyjack.service"
