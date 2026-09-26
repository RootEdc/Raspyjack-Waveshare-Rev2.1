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
pokrywy wynosi 0,30 mm. Jeżeli połączenie jest zbyt ciasne lub luźne, zmień
`cap_gap` w `generate_case.py` i ponownie wygeneruj STL.

Ustawienia startowe:

- materiał: PETG lub PLA,
- warstwa: 0,20 mm,
- 4 obrysy,
- 20–30% wypełnienia,
- podpory: wyłącznie pod mostami otworów portów, jeśli slicer ich wymaga,
- druk podstawy dnem na stole, ramki płaską stroną na stole.

Montaż wykorzystuje otwory M2.5 w rozstawie 58×23 mm. Otwory modelu mają
2,8 mm, a słupki 6,2 mm średnicy.

## Wymiary projektowe

- LCD PCB: 85,01×56,44 mm,
- Raspberry Pi Zero 2 W i hub: 65×30 mm,
- zewnętrzny korpus: około 91,1×62,5×29,5 mm,
- pełna wysokość po założeniu ramki: około 32,1 mm.

Model ma szerokie okna dla USB1/USB4 na krótkich bokach oraz USB2/USB3 i
USB-UART na długim boku. Osobne wycięcia zapewniają dojście do złączy Pi i
karty microSD.

## Edycja i generowanie

`raspyjack_case.scad` jest czytelnym modelem referencyjnym OpenSCAD.
Zweryfikowane pliki STL generuje skrypt Python:

```bash
python3 -m venv .venv-case
.venv-case/bin/pip install numpy trimesh manifold3d
.venv-case/bin/python hardware/case-waveshare-2.8/generate_case.py
```

Wszystkie wartości są w milimetrach. Po pierwszym fizycznym przymierzeniu
najczęściej wystarczy zmienić `pcb_clearance`, `cap_gap` lub wysokość
`base_height` w sekcji `CONFIG`.

## Źródła wymiarów

- [Waveshare USB HUB HAT 12694](https://www.waveshare.com/product/usb-hub-hat.htm)
- [Waveshare 2.8inch RPi LCD (A)](https://www.waveshare.com/product/2.8inch-rpi-lcd-a.htm)
- [Raspberry Pi Zero 2 W — rysunek mechaniczny](https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-mechanical-drawing.pdf)
