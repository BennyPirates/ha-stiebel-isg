# STIEBEL ISG Read-only Diagnosewerkzeug

Ein separates Diagnosewerkzeug für **WPL 17 ICS classic + WPMsystem + ISG
Connect**. Es liest ausschließlich Modbus FC04 (Input Register) und FC03
(Holding Register). Der Quellcode enthält keine Schreibaufrufe.

## Sicherheit

- Keine FC06/FC16-Operationen, keine Änderungen am ISG, keine HA-Installation.
- Standard: Unit-ID 1, Timeout 3 s, 80 ms Pause je einzelner Abfrage.
- Automatische Prüfung der Dokument→PDU-Offsets `-1` und `0` an fünf
  dokumentierten Registern. Bei uneindeutigem Ergebnis wird abgebrochen.
- `0x8000`/32768 wird vor Signed-Dekodierung als „nicht verfügbar“ erkannt.
- Der optionale Kandidatenscan umfasst nur kleine Bereiche direkt neben den
  offiziellen Blöcken. Unbekannten Registern wird keine Bedeutung zugeschrieben.
- Die gefährlichen Reset-/Restart-Holding-Register 1520 und 1521 werden auch
  nicht in die Kernliste aufgenommen.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Ausführung

Zuerst nur die dokumentierten Kernregister:

```bash
python stiebel_isg_probe.py 192.168.1.100
```

Danach kontrolliert mit kleinen angrenzenden Kandidatenbereichen:

```bash
python stiebel_isg_probe.py 192.168.1.100 --scan-candidates
```

Terminal, JSON und CSV enthalten Dokumentadresse, PDU-Adresse, Registerart,
Funktionscode, Rohwert, Datentyp, Skalierung, dekodierten Wert, Einheit,
Verfügbarkeit und Plausibilität. Ergebnisdateien landen in `results/`.

Ein manueller Offset (`--offset -1` oder `--offset 0`) ist nur für die gezielte
Fehleranalyse gedacht. Weitere Optionen zeigt `--help`.

## Tests

```bash
python -m unittest discover -s tests -v
```

Quellennachweis und lokale Herstellerdokumentation: [docs/SOURCES.md](docs/SOURCES.md).

## Home Assistant

Eine über HACS installierbare, zunächst vollständig lesende Home-Assistant-
Integration ist der nächste Entwicklungsschritt. Das Diagnosewerkzeug bleibt
als separates Hilfsmittel Bestandteil dieses Repositories. Konkrete Messdaten,
private IP-Adressen und Hersteller-PDFs werden nicht veröffentlicht.

## Lizenz

[MIT](LICENSE) – Copyright (c) 2026 Benjamin Pieritz. Die Software wird ohne
Gewährleistung oder Haftungsübernahme bereitgestellt; maßgeblich ist der
vollständige Lizenztext.
