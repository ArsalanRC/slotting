# slotting

[English](./README.md) · **Deutsch**

Welcher Artikel liegt in welchem Fach, damit der Kommissionierer weniger läuft.

Artikel nach Zugriffshäufigkeit sortieren und die häufigen nach vorne an die
Rampe legen: So steht es in jedem Lehrbuch, und es ist nicht falsch. Nur löst
es die falsche Aufgabe.

Niemand läuft zu einem Artikel und kommt zurück. Gelaufen wird **eine Tour**
über die ganze Pickliste und zurück zur Rampe. Bezahlt wird also die Tourlänge
pro Auftrag, nicht die Summe der Einzelwege. Das sind zwei verschiedene Zahlen,
und der Unterschied ist der Punkt: Zwei Artikel, die immer zusammen bestellt
werden, gehören nebeneinander, auch wenn keiner von beiden für sich häufig ist.
Eine Häufigkeitssortierung findet das nie, weil sie Gemeinsamkeit gar nicht
sehen kann.

Dieses Paket misst, was das Lager wirklich kostet, und sucht dagegen.

```python
from slotting import Layout, OrderHistory, optimise

layout = Layout(aisles=8, bays_per_aisle=20)
history = OrderHistory(orders)  # ein Auftrag = die Artikel einer Pickliste

result = optimise(layout, history)
print(f"{result.improvement:.1%} weniger Laufweg")
```

## Ausprobieren, ganz ohne eigene Daten

```bash
git clone https://github.com/ArsalanRC/slotting.git
cd slotting && pip install -e .
slotting --demo --before before.svg --after after.svg
```

```
orders            600
SKUs              52
lines per order   3.98
routing           s-shape

frequency slotting       27,947 m
optimised                26,202 m
saved                     1,745 m   6.2%

77 swaps over 4 passes
```

Heraus kommen zwei SVG-Heatmaps der Lagerfläche, auf einer gemeinsamen
Farbskala, damit man sie ehrlich vergleichen kann. Mit echten Daten statt der
Demo:

```bash
slotting orders.csv --aisles 8 --bays 20 --after after.svg
```

Eine Pickliste pro Zeile, Artikelnummern in den Zellen. Genau so sieht der
Export aus jedem WMS ohnehin aus.

## Was es nicht sagt

**Es behauptet nie ein Optimum.** Slotting ist ein quadratisches
Zuordnungsproblem und damit NP-schwer. `optimise` liefert eine bessere
Zuordnung und sagt dazu, um wie viel besser. `result.converged` sagt, ob der
Suche die verbessernden Tauschzüge ausgegangen sind oder die Durchläufe. Das
sind zwei verschiedene Antworten.

**Sechs Prozent sind ein realistischer Wert, kein enttäuschender.** Die
Literatur nennt je nach Ausgangslage etwa fünf bis zwanzig Prozent. Wer fünfzig
verspricht, misst gegen eine zufällige Ausgangsbelegung oder misst etwas
anderes.

**Bei einzeiligen Aufträgen hilft das hier nicht**, und das Programm sagt es
selbst. Ein Artikel pro Auftrag heißt: keine Gemeinsamkeit, also liegt die
Häufigkeitssortierung schon fast richtig. Das ist eine Eigenschaft der
Nachfrage und keine Schwäche des Werkzeugs. Ein Paket, das hier zweistellige
Verbesserungen meldet, misst Rauschen.

## Die drei Stellen, die zählen

**Entfernung wird über den Gassengraphen gerechnet, nie in Luftlinie.** Zwei
Fächer, die sich durch ein Regal hindurch gegenüberliegen, sind einen Meter
auseinander und zu Fuß dreißig. Luftlinie ist dafür keine Näherung, sondern
eine andere Zahl, die zufällig kleiner ist, und zwar am kleinsten genau dort,
wo sie am falschesten ist. Ein Test schlägt fehl, falls das je zurückfällt.

**Die Wegstrategie ist eine Entscheidung und ändert das Ergebnis.** `s-shape`
ist die Vorgabe, weil die meisten Lager genau so arbeiten: in jede Gasse mit
einem Pick hinein, durchlaufen, weiter. Die Kosten hängen davon ab, **welche**
Gassen berührt werden, und kaum davon, wie viele Artikel je Gasse liegen. Genau
deshalb zahlt es sich aus, zusammengehörende Artikel nebeneinander zu legen.
`return` ist die Alternative. `optimal_route` gibt es auch, per vollständiger
Aufzählung, und außer den Tests ruft sie niemand auf: Sie sagt, wie weit die
Heuristiken vom echten Minimum entfernt sind, statt das zu unterstellen.

**Die Suche bewertet das echte Ziel.** Jeder Tauschzug wird daran gemessen, was
er an tatsächlicher Tourlänge über tatsächliche Aufträge ändert, nicht an einem
Ersatzmaß. Naiv wäre das viel zu langsam, deshalb werden beim Tausch zweier
Artikel nur die Aufträge neu gerechnet, die einen von beiden enthalten. Die
laufende Summe wird danach weggeworfen und komplett neu berechnet, denn ein
Fehler in dieser Buchführung würde sonst eine Ersparnis melden, die die
Zuordnung gar nicht liefert. Das ist der eine Fehler, den dieses Werkzeug nicht
haben darf.

## Exit-Codes

| | |
|---|---|
| `0` | gelaufen, und es gibt eine Verbesserung |
| `1` | gelaufen, und es gibt nichts zu tun |
| `2` | konnte nicht laufen |

Steckt "nichts zu tun" in `0`, meldet ein Cron-Job Erfolg und tut still nichts.
Steckt es in `2`, sieht jedes bereits gut sortierte Lager kaputt aus.

## Installation

Python ab 3.10. **Keine Laufzeit-Abhängigkeiten**, mit Absicht: Das läuft als
geplanter Job auf einem Lagerserver, und jede Abhängigkeit ist ein Grund, warum
es dort im Ernstfall nicht läuft. Die Heatmap ist als Text geschriebenes SVG
statt einer Grafikbibliothek.

```bash
git clone https://github.com/ArsalanRC/slotting.git
cd slotting && pip install -e ".[dev]"
pytest
```

50 Tests, `ruff` und `mypy --strict` sauber, auf Python 3.10 bis 3.13.

## Autor

Arsalan Khadim, Softwarearchitekt und Full-Stack-Engineer.
Lager- und ERP-Integration ist der Tagesjob, und daher kommt dieses Problem.

- [Portfolio](https://arsalanrc.github.io)
- [LinkedIn](https://www.linkedin.com/in/muhammad-arsalan-khadim-b87550259/)
- [GitHub](https://github.com/ArsalanRC)

## Lizenz

MIT, siehe [LICENSE](./LICENSE).
