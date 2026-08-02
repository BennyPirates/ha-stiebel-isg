# Quellen

## Offizielle STIEBEL-ELTRON-Dokumentation

- **Modbus TCP/IP – Software-Dokumentation**, Dokumentkennung
  `DM0000040850-hqy`, PDF-Metadaten vom 09.11.2020, abgerufen am 02.08.2026:
  <https://www.stiebel-eltron.de/static/ste/docportal/manual/DM0000040850-hqy.pdf>
- Nur lokal vorgehaltene, nicht veröffentlichte Kopie:
  `docs/vendor/stiebel-isg-modbus-official.pdf`
- Mittels `pdftotext -layout` erzeugte, ebenfalls nicht veröffentlichte
  Arbeitsextraktion:
  `docs/vendor/stiebel-isg-modbus-official.txt`

Für WPL 17 ICS classic mit WPMsystem werden Kapitel 4 (Protokoll und
Datentypen) sowie Kapitel 6 (Wärmepumpen mit WPM, Spalte WPMsystem) verwendet.
Der separate Abschnitt für WPM G wird nicht als Registerquelle benutzt.

Wesentliche Vorgaben der Quelle: Port 502, feste Slave-/Unit-ID 1, 16-Bit-
Register, FC04 für Input Register, FC03 zum Lesen von Holding Registern,
Ersatzwert 32768/0x8000 bei nicht verfügbaren Objekten und 1-basierte
ISG-Adressen mit möglichem Offset von 1.

## PyModbus

- Offizielle API-Dokumentation (3.13.1):
  <https://pymodbus.readthedocs.io/en/v3.13.1/source/client.html>
