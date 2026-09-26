# Pomiary ekranu ze zdjęcia

Zdjęcie egzemplarza Waveshare 2.8inch RPi LCD (A) Rev2.1 zostało skorygowane
homografią do oficjalnego obrysu PCB 85,01×56,44 mm. Moneta 1 euro o średnicy
23,25 mm posłużyła jako kontrola skali. Ponieważ była trzymana trochę powyżej
płaszczyzny PCB, dokładne przeliczenie oparto na wymiarze samej płytki.

Układ współrzędnych odpowiada widokowi poziomemu na `measurement_overlay.png`:
przyciski są po lewej, a początek znajduje się w lewym górnym rogu PCB.

| Element | Wartość |
|---|---:|
| PCB | 85,01×56,44 mm |
| Lewa krawędź otwarcia dotyku | 7,70 mm |
| Prawa krawędź otwarcia dotyku | 75,10 mm |
| Górna krawędź otwarcia dotyku | 1,10 mm |
| Dolna krawędź otwarcia dotyku | 49,80 mm |
| Otwór w ramce | 67,40×48,70 mm |
| Przesunięcie środka otworu X | −1,105 mm |
| Przesunięcie środka otworu Y | −2,770 mm |

Środki przycisków w milimetrach od lewego górnego rogu PCB:

| Przycisk | X | Y |
|---|---:|---:|
| KEY1 | 4,15 | 7,65 |
| KEY2 | 4,15 | 22,15 |
| KEY3 | 4,15 | 36,50 |
| KEY4 | 4,15 | 50,45 |

W modelu każdy przycisk otrzymał zaokrąglony otwór 5,2×7,2 mm. Daje to około
0,5 mm tolerancji wokół metalowej obudowy przełącznika bez osłabiania ramki
jednym długim wycięciem.
