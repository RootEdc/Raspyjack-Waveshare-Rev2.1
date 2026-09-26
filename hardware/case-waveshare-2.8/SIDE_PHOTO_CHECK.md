# Kontrola całego zestawu na zdjęciach

Sprawdzony zestaw, od dołu: Raspberry Pi Zero 2 W, Waveshare 12694 USB HUB
HAT, Waveshare 2.8inch RPi LCD (A) Rev2.1. Przejrzano wszystkie siedem zdjęć
sprzętu z folderu Pobrane. Skalę pomocniczą stanowi moneta 1 euro o średnicy
23,25 mm. Perspektywę kontrolowano znanymi wymiarami płytek 65×30 mm,
LCD 85,01×56,44 mm i rozstawem otworów 58×23 mm.

## Co pokazują poszczególne zdjęcia

| Zdjęcie | Wniosek użyty w modelu |
| --- | --- |
| `215857626` | Położenie szkła dotykowego, widocznego LCD i czterech przycisków względem PCB. |
| `220637802` | Gniazda na długiej krawędzi są cofnięte pod LCD. |
| `220701400` | Widok od tyłu: po odbiciu lustrzanym Pi i hub wypadają przy lewej i górnej krawędzi widoku frontowego; microSD jest po stronie przycisków. |
| `220714509` | Przekrój całego stosu oraz wysokości Pi→hub i hub→LCD. |
| `222006457` | Złącza GPIO i dystanse mieszczą się w obrysie płytek; kontrola wysokości z drugiej strony. |
| `222017834` | Żaden element nie wychodzi poza prostokątny obrys PCB. |
| `222022702` | Potwierdzenie położenia przewodów i elementów pod LCD bez potrzeby bocznych kieszeni. |

## Wymiary wynikowe

- Układ współrzędnych modelu jest zgodny z frontem LCD: przyciski są po lewej,
  a góra zdjęcia jest górą modelu. Zdjęcia Pi i huba wykonano od tyłu, dlatego
  przed porównaniem z frontem wymagają odbicia lustrzanego.
- Po prawidłowym odbiciu Pi i hub 65×30 mm są dosunięte do lewej i górnej
  krawędzi LCD. Daje to przesunięcie środka `−10,005 mm` w osi X i
  `−13,22 mm` w osi Y.
- Przeciwległy krótki bok Pi/huba jest cofnięty względem LCD o 20,01 mm,
  a przeciwległa długa krawędź o 26,44 mm. Wyjaśnia to, dlaczego tylko port
  przy lewej krawędzi może dochodzić do ściany obudowy.
- Wewnętrzny obrys obudowy ma 86,31×57,74 mm, czyli po 0,65 mm luzu od każdej
  krawędzi PCB LCD.
- Korpus ma 91,11×62,54×40,00 mm. Ramka zwiększa wymiar zewnętrzny do
  94,81×66,24 mm, a pełną wysokość do 42,60 mm.
- Zdjęcia boczne wskazują około 13 mm pomiędzy Pi i hubem oraz około 19 mm
  pomiędzy hubem i PCB LCD. Wysokość 42,60 mm zawiera około 0,5 mm zapasu
  względem odczytanego stosu.
- Widoczny ekran ma otwór 67,40×48,70 mm przesunięty o 1,105 mm w lewo i
  2,770 mm w stronę bliższej krawędzi PCB.
- Środek jedynego dostępnego portu USB-A wypada 24 mm nad spodem na lewym
  krótkim boku, czyli po stronie czterech przycisków. Otwór ma 17×12 mm.
- Otwór microSD pozostaje na tym samym lewym krótkim boku, ze środkiem 6 mm
  nad spodem i wymiarem 17×6,5 mm.
- Luz ramki 0,25 mm na stronę został potwierdzony fizycznym wydrukiem próbki.

## Porty

Na zewnątrz pozostają tylko:

1. jeden boczny port hosta USB-A po stronie przycisków,
2. karta microSD.

Pozostałe trzy USB-A, USB-UART, mini-HDMI, USB danych i USB zasilania
Raspberry Pi są cofnięte pod LCD. Ich ściany są pełne. Panelowe gniazdo
microUSB zasilania zostanie dodane dopiero po sprawdzeniu dopasowania
pierwszego wydruku i poznaniu wymiarów wybranego elementu panelowego.

Moneta jest trzymana w nieco innej płaszczyźnie niż zestaw, dlatego nie służy
jako jedyne źródło skali. Wymiar X/Y opiera się na dokumentacji płytek, a
moneta i rozstaw otworów służą do wzajemnej kontroli pomiaru wysokości.
