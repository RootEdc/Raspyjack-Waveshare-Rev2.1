# Kontrola zestawu na zdjęciach bocznych

Sprawdzony zestaw, od dołu: Raspberry Pi Zero 2 W, Waveshare 12694 USB HUB
HAT, Waveshare 2.8inch RPi LCD (A) Rev2.1. Skalę kontrolną stanowi moneta
1 euro o średnicy 23,25 mm. Położenie płytek sprawdzono również względem
znanych wymiarów Pi i huba 65×30 mm oraz rozstawu otworów 58×23 mm.

## Wyniki

- Pi i hub są przesunięte pod krawędź LCD zgodnie z przesunięciem modelu
  `10,005 mm` w osi X i `13,22 mm` w osi Y.
- Odległość płaszczyzny Pi od huba na bocznym zdjęciu wynosi około 13 mm.
- Odległość huba od płytki LCD wynosi około 19 mm.
- Cały zestaw od dolnej płaszczyzny montażowej obudowy do frontu LCD wymaga
  około 42 mm. Korpus ma dlatego 39,5 mm, a założona ramka daje 42,1 mm.
- Środki gniazd USB-A huba wypadają około 24 mm nad spodem obudowy. Boczne
  otwory USB1 i USB4 zostały podniesione do tej wysokości.
- USB2 i USB3 na długiej krawędzi są schowane pod LCD. USB1 na przeciwnym
  krótkim boku jest cofnięty o około 20 mm. Tunele od ścian obudowy do tych
  gniazd byłyby za głębokie dla zwykłej wtyczki, więc trzy otwory usunięto.
  Z czterech portów hosta zostaje USB4, który dochodzi do obrysu LCD. Osobno
  pozostaje mniejsze okno serwisowe USB-UART.
- Złącza mini-HDMI, USB danych, USB zasilania i microSD Raspberry Pi pozostają
  na wysokości dolnej płytki i nie kolidują z hubem.

Pomiary zdjęciowe mają niepewność około 1 mm ze względu na perspektywę i
różną odległość monety od aparatu. Wymiary X/Y płytek oparto na dokumentacji,
a zdjęcia służyły do ustalenia konfiguracji, przesunięcia i wysokości stosu.
