# Medisana BU 572 – Home Assistant Integration

Custom Integration für das **Medisana BU 572 connect** Blutdruckmessgerät. Die Kommunikation erfolgt lokal über Bluetooth Low Energy (BLE). Unterstützt werden lokale Home-Assistant-Bluetooth-Adapter und **ESPHome Bluetooth Proxies**.

> Dieses Projekt ist ein unabhängiges Community-Projekt und steht in keiner Verbindung zu Medisana.

## Funktionen

- lokale BLE-Kommunikation ohne Cloud
- Bluetooth-Discovery des `BU 572`
- automatische Synchronisation nach einer Messung
- manueller **Synchronisieren**-Button als Fallback
- Unterstützung von **Benutzer 1 und Benutzer 2**
- Systolisch, Diastolisch, MAP und Puls
- originale Messzeit des BU 572
- Messstatus
- Batterie und Bluetooth-RSSI
- persistente Messhistorie
- Unterstützung mehrerer ESPHome Bluetooth Proxies über Home Assistant

## Getestet

Die Integration wurde mit einem **Medisana BU 572 connect** getestet.

Verwendete BLE-GATT-Characteristics:

| Funktion | UUID |
|---|---|
| Blood Pressure Service | `0x1810` |
| Blood Pressure Measurement | `0x2A35` |
| Battery Level | `0x2A19` |
| Current Time | `0x2A2B` |

Das BU 572 liefert SYS, DIA und MAP direkt. Die Integration übernimmt den vom Gerät übertragenen MAP-Wert und berechnet ihn nicht neu.

### Benutzerzuordnung

| Rohwert des BU 572 | Home Assistant |
|---:|---|
| `0` | Benutzer 1 |
| `1` | Benutzer 2 |

Diese Zuordnung wurde mit Messungen beider Benutzer verifiziert.

## Voraussetzungen

- Home Assistant mit aktivierter Bluetooth-Integration
- Bluetooth-Adapter **oder** ESPHome Bluetooth Proxy mit aktiven Verbindungen

Beispiel für einen ESPHome Proxy:

```yaml
esp32_ble_tracker:

bluetooth_proxy:
  active: true
```

Mehrere Bluetooth-Proxys können gleichzeitig verwendet werden. Home Assistant stellt der Integration einen verfügbaren connectable Bluetooth-Pfad bereit.

## Installation

### HACS – Custom Repository

Solange dieses Repository nicht im offiziellen HACS-Katalog enthalten ist:

1. HACS öffnen.
2. **Integrationen** öffnen.
3. Über das Menü **Benutzerdefinierte Repositories / Custom repositories** öffnen.
4. Die URL dieses GitHub-Repositories eintragen.
5. Kategorie **Integration** auswählen.
6. `Medisana BU 572` installieren.
7. Home Assistant vollständig neu starten.

### Manuell

Den Ordner

```text
custom_components/medisana_bu572/
```

nach

```text
/config/custom_components/medisana_bu572/
```

kopieren und Home Assistant vollständig neu starten.

Danach unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Medisana BU 572** suchen. Ein sichtbares BU 572 sollte auch automatisch über Bluetooth entdeckt werden.

## Automatische Synchronisation

Im normalen Betrieb muss der Synchronisieren-Button nicht gedrückt werden.

```text
Blutdruck messen
      ↓
BU 572 wird per Bluetooth sichtbar
      ↓
Home Assistant / Bluetooth Proxy erkennt das Gerät
      ↓
automatische BLE-Verbindung
      ↓
Messwerte werden übernommen
```

Die Integration verwendet zusätzlich einen Erreichbarkeits-Watcher, weil ein bereits im Bluetooth-Manager bekanntes Gerät nicht bei jedem Aufwachen zwingend einen neuen Discovery-Callback auslösen muss. Ein Cooldown verhindert unnötige Mehrfachverbindungen.

## Entitäten

Für jeden Benutzer werden getrennte Entitäten angelegt:

- Systolisch
- Diastolisch
- Mittlerer arterieller Druck (MAP)
- Puls
- Messzeit
- Messstatus
- Messhistorie

Zusätzlich stehen zur Verfügung:

- Batterie
- Bluetooth RSSI
- Letzter Benutzer
- Synchronisieren

## Messhistorie

Die Integration speichert empfangene Messungen persistent. Gespeichert werden unter anderem:

- Messzeit
- SYS
- DIA
- MAP
- Puls
- Benutzer
- Messstatus

Der Diagnose-Sensor `Messhistorie` stellt für Dashboards die letzten Messungen im Attribut `measurements` bereit.

## Beispiel-Dashboard

Unter [`examples/dashboard.yaml`](examples/dashboard.yaml) liegt ein Beispiel für ein Lovelace-Dashboard mit getrennten Bereichen für Benutzer 1 und 2.

Das Beispiel verwendet optional den Helfer:

```text
input_number.bu_572_anzahl_letzte_messungen
```

Empfohlene Einstellungen: Minimum `1`, Maximum `30`, Schrittweite `1`, Startwert `10`.

> Hinweis: Entity-IDs können je nach Home-Assistant-Installation abweichen und müssen im Beispiel-Dashboard gegebenenfalls angepasst werden.

## Fehlerdiagnose

Wenn keine Messwerte automatisch übertragen werden:

1. Prüfen, ob das BU 572 im Home-Assistant-Bluetooth-Monitor sichtbar wird.
2. Bei ESPHome-Proxys prüfen, ob aktive BLE-Verbindungen erlaubt sind.
3. Eine neue Messung durchführen und kurz warten.
4. Testweise **Synchronisieren** drücken.
5. Home-Assistant-Protokoll nach `medisana_bu572` bzw. `BU 572` durchsuchen.

Bei einem GitHub-Issue bitte Home-Assistant-Version, Integrationsversion, Art des Bluetooth-Adapters/Proxys und relevante Logzeilen angeben. **Private Gesundheitsdaten, MAC-Adressen und interne IP-Adressen vorher entfernen.**

## Datenschutz

Die Kommunikation mit dem BU 572 erfolgt lokal über Bluetooth. Diese Integration benötigt für die Gerätekommunikation keinen externen Cloud-Dienst.

## Medizinischer Hinweis

Die Integration dient ausschließlich zur Übertragung und Darstellung der vom Blutdruckmessgerät gelieferten Werte. Sie ist kein Medizinprodukt und ersetzt keine medizinische Diagnose oder Beratung.

## Entwicklung / Beiträge

Fehlerberichte, Tests mit weiteren Geräten und Pull Requests sind willkommen. Bei anderen Medisana-Modellen bitte Modellbezeichnung und anonymisierte technische Informationen beifügen.

## Lizenz

MIT – siehe [`LICENSE`](LICENSE).
