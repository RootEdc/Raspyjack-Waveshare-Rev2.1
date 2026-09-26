# Obudowa RaspyJack — Pi Zero 2 W + Waveshare 12694 + LCD 2.8 Rev2.1

Parametryczna, dwuczęściowa obudowa dla stosu, od dołu:

1. Raspberry Pi Zero 2 W,
2. Waveshare 12694 USB HUB HAT (cztery USB 2.0 + USB-UART),
3. Waveshare 2.8inch RPi LCD (A), 320×240, Rev2.1.

## Pliki do druku

- `stl/raspyjack_28_base.stl` — dolna część,
- `stl/raspyjack_28_bezel.stl` — górna ramka ekranu,
- `stl/cap_clearance_test.stl` — mała próbka luzu pokrywy,
- `stl/assembly_preview.stl` — podgląd złożenia, nie służy do druku.

## Pierwszy wydruk

Najpierw wydrukuj `cap_clearance_test.stl`. Na stole powstaną dwa osobne
elementy: prostokątny trzpień oraz kanał w kształcie litery U. Zdejmij oba
elementy ze stołu i wsuń trzpień w kanał od jego krótszego końca. Domyślny luz
pokrywy wynosi 0,25 mm na każdą stronę. Jeżeli połączenie jest zbyt ciasne lub
luźne, zmień `cap_clearance` w `generate_case.py` i ponownie wygeneruj STL.

Ustawienia startowe:

- materiał: PETG lub PLA,
- warstwa: 0,20 mm,
- 4 obrysy,
- 20–30% wypełnienia,
- podpory: zwykle nie są potrzebne; sprawdź podgląd warstw przy otworach USB,
- podstawa jest już ustawiona dnem na stole, a ramka płaskim frontem na stole.

Montaż wykorzystuje otwory M2.5 w rozstawie 58×23 mm. Otwory modelu mają
2,8 mm, a słupki 6,2 mm średnicy.

## Wymiary projektowe

- LCD PCB: 85,01×56,44 mm,
- Raspberry Pi Zero 2 W i hub: 65×30 mm,
- zewnętrzny korpus: około 91,1×62,5×39,5 mm,
- pełna wysokość po założeniu ramki: około 42,1 mm.

Model udostępnia jeden port hosta USB-A: USB4 na krótkim boku, gdzie krawędź
huba dochodzi do obrysu LCD. USB1 po przeciwnej stronie jest cofnięty o około
20 mm, a USB2/USB3 są głęboko pod większą płytką LCD, dlatego ich niepraktyczne
otwory usunięto. Pozostają mniejsze okno serwisowe USB-UART oraz osobne
wycięcia dla złączy Pi i karty microSD.

Położenie otworu dotyku i czterech przycisków zmierzono z wyprostowanego
perspektywicznie zdjęcia egzemplarza Rev2.1. Otwór 67,4×48,7 mm jest przesunięty
o 1,105 mm w lewo i 2,770 mm ku górnej krawędzi względem środka PCB. Szczegóły
pomiaru znajdują się w `PHOTO_MEASUREMENTS.md`.

Wysokość i położenie złączy sprawdzono na dodatkowych zdjęciach boków zestawu
z monetą 1 euro. Wyniki i założenia opisuje `SIDE_PHOTO_CHECK.md`.

## Edycja i generowanie

`raspyjack_case.scad` jest czytelnym modelem referencyjnym OpenSCAD.
Zweryfikowane pliki STL generuje skrypt Python:

```bash
python3 -m venv .venv-case
.venv-case/bin/pip install numpy trimesh manifold3d
.venv-case/bin/python hardware/case-waveshare-2.8/generate_case.py
```

Wszystkie wartości są w milimetrach. Po pierwszym fizycznym przymierzeniu
najczęściej wystarczy zmienić `pcb_clearance`, `cap_clearance` lub wysokość
`base_height` w sekcji `CONFIG`.

## Źródła wymiarów

- [Waveshare USB HUB HAT 12694](https://www.waveshare.com/product/usb-hub-hat.htm)
- [Waveshare 2.8inch RPi LCD (A)](https://www.waveshare.com/product/2.8inch-rpi-lcd-a.htm)
- [Raspberry Pi Zero 2 W — rysunek mechaniczny](https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-mechanical-drawing.pdf)
