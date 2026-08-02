# STIEBEL ISG für Home Assistant

Eine lokale Home-Assistant-Custom-Integration und ein separates
Diagnosewerkzeug für **WPMsystem + ISG Connect**. Das Diagnosewerkzeug ist
vollständig lesend. Die Home-Assistant-Integration liest mit Modbus FC04 und
FC03 und darf ausschließlich die dokumentierte Betriebsart sowie die
Eco-Raumsolltemperatur für Heizkreis 1 über FC06 ändern.

## Sicherheit

- Kein generischer Registerzugriff und keine FC16-Operationen. Eng begrenzte
  FC06-Schreibpfade existieren ausschließlich für WPMsystem Holding Register
  1501 (Betriebsart) und 1503 (Eco-Raumsolltemperatur Heizkreis 1). Sie
  validieren Werte und Offset und prüfen das Ergebnis durch direktes
  Zurücklesen.
- Standard: Unit-ID 1, Timeout 3 s, 80 ms Pause je einzelner Abfrage.
- Automatische Prüfung der Dokument→PDU-Offsets `-1` und `0` an fünf
  dokumentierten Registern. Bei uneindeutigem Ergebnis wird abgebrochen.
- `0x8000`/32768 wird vor Signed-Dekodierung als „nicht verfügbar“ erkannt.
- Der optionale Kandidatenscan umfasst nur kleine Bereiche direkt neben den
  offiziellen Blöcken. Unbekannten Registern wird keine Bedeutung zugeschrieben.
- Die gefährlichen Reset-/Restart-Holding-Register 1520 und 1521 werden auch
  nicht in die Kernliste aufgenommen.

## Installation in Home Assistant über HACS

[![Open your Home Assistant instance and add this repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=BennyPirates&repository=ha-stiebel-isg&category=integration)

Der Button öffnet die eigene lokale Home-Assistant-Instanz und trägt dieses
Repository als HACS-Integration ein. Alternativ funktioniert die manuelle
Einrichtung:

Die Integration wird als benutzerdefiniertes HACS-Repository verteilt und kann
ohne manuelles Kopieren installiert werden:

1. HACS öffnen und rechts oben **Benutzerdefinierte Repositories** wählen.
2. `https://github.com/BennyPirates/ha-stiebel-isg` als Kategorie
   **Integration** hinzufügen.
3. **STIEBEL ELTRON ISG** herunterladen und Home Assistant neu starten.
4. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach
   **STIEBEL ELTRON ISG** suchen.
5. IP-Adresse des ISG eintragen. Port 502 und Unit-ID 1 sind vorbelegt.

Der Config Flow prüft die Verbindung und erkennt den Dokument-/PDU-Offset
automatisch anhand mehrerer plausibler WPMsystem-Register. Das ISG wird lokal
alle 30 Sekunden abgefragt. `0x8000` wird als nicht verfügbar behandelt;
dadurch werden beispielsweise Kühlentitäten automatisch verfügbar, sobald die
Anlage diese Register später bereitstellt. SG Ready Rohwert 0 wird als
`Disabled` dargestellt.

Updates erscheinen nach neuen GitHub-Releases direkt in HACS. Konfiguration,
Gerät und Entity-IDs bleiben dabei erhalten.

## Diagnosewerkzeug installieren

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Ausführung

Zuerst nur die dokumentierten Kernregister:

```bash
python stiebel_isg_probe.py isg.local
```

Danach kontrolliert mit kleinen angrenzenden Kandidatenbereichen:

```bash
python stiebel_isg_probe.py isg.local --scan-candidates
```

Terminal, JSON und CSV enthalten Dokumentadresse, PDU-Adresse, Registerart,
Funktionscode, Rohwert, Datentyp, Skalierung, dekodierten Wert, Einheit,
Verfügbarkeit und Plausibilität. Ergebnisdateien landen in `results/`.

Ein manueller Offset (`--offset -1` oder `--offset 0`) ist nur für die gezielte
Fehleranalyse gedacht. Weitere Optionen zeigt `--help`.

## Entwicklung und Tests

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
python -m unittest discover -s tests -v
```

Die lokalen Entwicklungsregeln stehen in [AGENTS.md](AGENTS.md), der Status
der Home-Assistant-MCP-Umgebung in
[docs/HA_DEVELOPMENT_ENVIRONMENT.md](docs/HA_DEVELOPMENT_ENVIRONMENT.md).

Quellennachweis und lokale Herstellerdokumentation: [docs/SOURCES.md](docs/SOURCES.md).

## Entwicklungsstand

Die Integration stellt ausgewählte Temperaturen, Drücke, Status-, Energie- und
Laufzeitwerte als Sensoren und binäre Sensoren bereit. Die Betriebsart wird als
Select-Entität angeboten: Notbetrieb, Bereitschaft, Programm, Komfort, Eco und
Warmwasser. Die Eco-Raumsolltemperatur für Heizkreis 1 wird als begrenzte
Number-Entität (5,0 bis 30,0 °C) angeboten. Alle anderen dokumentierten Holding
Register bleiben lesend. Es
gibt keine freie Register-, Number-, Switch- oder Service-Schnittstelle.
Konkrete Messdaten, private IP-Adressen und Hersteller-PDFs werden nicht
veröffentlicht.

## Lizenz

[MIT](LICENSE) – Copyright (c) 2026 Benjamin Pieritz. Die Software wird ohne
Gewährleistung oder Haftungsübernahme bereitgestellt; maßgeblich ist der
vollständige Lizenztext.
