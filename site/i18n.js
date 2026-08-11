/* Both languages written as themselves, never one translated into the other.
   German engineers say Kommissionierer, Gasse and Rampe; those are the words,
   not "picker" carried across. Where a term genuinely is English in German
   usage it stays English. */

export const STRINGS = {
  en: {
    "meta.title": "slotting · the picker walks one route, not many",
    "nav.source": "Source",
    "nav.portfolio": "Portfolio",
    "nav.linkedin": "LinkedIn",
    "nav.lang": "Deutsch",

    "hero.kicker": "Python 3.10+ · zero dependencies · a warehouse floor",
    "hero.title": "Put the popular items at the front.<br>It is the wrong <em>answer</em>.",
    "hero.lede":
      "Nobody walks to one item and comes back. They walk a single route through a whole pick list. So what you pay is route length per order, and that is not the sum of the distances. Two items always ordered together belong side by side, even when neither is popular.",
    "hero.cta": "Read the code",

    "route.eyebrow": "One route, not many",
    "route.title": "Move one item, and the walk gets shorter",
    "route.lede":
      "The same four items, on the same order, on two different floors. On the left they sit where pick frequency put them. On the right one of them has moved into the aisle the picker was already walking down.",
    "route.play": "Walk the order",
    "route.byFrequency": "By pick frequency",
    "route.optimised": "Optimised",
    "route.caption":
      "The item that moved is not popular. It simply keeps turning up on the same orders as items that are, and that is a fact frequency ranking cannot see.",
    "route.noteTitle": "Why the second aisle is so expensive",
    "route.noteBody":
      "Most warehouses pick in an S-shape: go into every aisle that holds something on the list, walk it end to end, move on. So the cost is set by how many aisles you enter, not by how many items you collect in each. Once the picker is in an aisle, everything else in it is nearly free. That is the whole reason co-locating pays.",

    "heat.eyebrow": "The floor",
    "heat.title": "Where the walking actually happens",
    "heat.lede":
      "Every cell is one storage location, darker where more picks land on it. The dock is the black bar at the bottom. Flip the switch and watch the heat pull in towards it.",
    "heat.switch": "Show the optimised floor",
    "heat.cold": "quiet",
    "heat.hot": "busy",
    "heat.caption":
      "Both floors are drawn on one shared colour scale. Given its own scale each picture would look equally hot, which would make the comparison look like a result while proving nothing.",

    "limits.eyebrow": "What it will not tell you",
    "limits.title": "Three things stated up front",
    "limits.c1t": "It never claims an optimum",
    "limits.c1b":
      "Slotting is a quadratic assignment problem and it is NP-hard. The tool returns a better arrangement and says how much better. It also says whether the search finished or simply ran out of passes, because those are different answers.",
    "limits.c2t": "Seven percent is a real number",
    "limits.c2b":
      "Published slotting work lands somewhere between five and twenty percent, depending on how badly the warehouse started. Anything advertising fifty is measuring against a random arrangement nobody actually has.",
    "limits.c3t": "Single-line orders cannot be helped",
    "limits.c3b":
      "One item per order means nothing is ever picked alongside anything else, so there is no pairing to find and frequency ranking is already close to right. The tool says so and exits accordingly, rather than reporting noise as a saving.",

    "foot.by": "Built by Arsalan Khadim",
  },

  de: {
    "meta.title": "slotting · eine Tour, nicht viele Einzelwege",
    "nav.source": "Quellcode",
    "nav.portfolio": "Portfolio",
    "nav.linkedin": "LinkedIn",
    "nav.lang": "English",

    "hero.kicker": "Python ab 3.10 · keine Abhängigkeiten · eine Lagerfläche",
    "hero.title": "Die häufigen Artikel nach vorne.<br>Die falsche <em>Antwort</em>.",
    "hero.lede":
      "Niemand läuft zu einem Artikel und wieder zurück. Gelaufen wird eine Tour über die ganze Pickliste. Bezahlt wird also die Tourlänge je Auftrag, und die ist nicht die Summe der Einzelwege. Zwei Artikel, die immer zusammen bestellt werden, gehören nebeneinander, auch wenn keiner von beiden häufig ist.",
    "hero.cta": "Zum Code",

    "route.eyebrow": "Eine Tour, nicht viele",
    "route.title": "Ein Artikel zieht um, und der Weg wird kürzer",
    "route.lede":
      "Dieselben vier Artikel, derselbe Auftrag, zwei verschiedene Lagerflächen. Links liegen sie da, wo die Zugriffshäufigkeit sie hingelegt hat. Rechts ist einer davon in die Gasse gezogen, die der Kommissionierer ohnehin schon abläuft.",
    "route.play": "Tour laufen",
    "route.byFrequency": "Nach Zugriffshäufigkeit",
    "route.optimised": "Optimiert",
    "route.caption":
      "Der Artikel, der umgezogen ist, wird selten gebraucht. Er taucht nur immer auf denselben Aufträgen auf wie Artikel, die häufig sind. Genau das sieht eine Häufigkeitssortierung nicht.",
    "route.noteTitle": "Warum die zweite Gasse so teuer ist",
    "route.noteBody":
      "Die meisten Lager kommissionieren im S-Durchlauf: in jede Gasse hinein, in der etwas auf der Liste liegt, einmal durch, weiter. Die Kosten entstehen also dadurch, wie viele Gassen betreten werden, und kaum dadurch, wie viel je Gasse eingesammelt wird. Ist der Kommissionierer erst in der Gasse, kostet alles Weitere darin fast nichts. Deshalb zahlt sich Zusammenlegen aus.",

    "heat.eyebrow": "Die Fläche",
    "heat.title": "Wo tatsächlich gelaufen wird",
    "heat.lede":
      "Jede Zelle ist ein Lagerplatz, dunkler bei mehr Zugriffen. Die Rampe ist der schwarze Balken unten. Schalter umlegen und zusehen, wie die Wärme zur Rampe wandert.",
    "heat.switch": "Optimierte Fläche zeigen",
    "heat.cold": "ruhig",
    "heat.hot": "viel",
    "heat.caption":
      "Beide Flächen liegen auf einer gemeinsamen Farbskala. Je eigener Skala sähe jedes Bild gleich warm aus, und der Vergleich wirkte wie ein Ergebnis, ohne eines zu sein.",

    "limits.eyebrow": "Was es nicht sagt",
    "limits.title": "Drei Dinge gleich vorweg",
    "limits.c1t": "Ein Optimum behauptet es nie",
    "limits.c1b":
      "Slotting ist ein quadratisches Zuordnungsproblem und damit NP-schwer. Das Werkzeug liefert eine bessere Anordnung und sagt, um wie viel besser. Es sagt außerdem, ob die Suche fertig war oder ob ihr die Durchläufe ausgingen. Das sind zwei verschiedene Antworten.",
    "limits.c2t": "Sieben Prozent sind ein echter Wert",
    "limits.c2b":
      "Die Literatur nennt je nach Ausgangslage etwa fünf bis zwanzig Prozent. Wer fünfzig verspricht, misst gegen eine zufällige Anordnung, die so in keinem Lager steht.",
    "limits.c3t": "Bei einzeiligen Aufträgen geht nichts",
    "limits.c3b":
      "Ein Artikel je Auftrag heißt: nichts wird je zusammen mit etwas anderem gegriffen. Es gibt also keine Paarung zu finden, und die Häufigkeitssortierung liegt schon fast richtig. Das Werkzeug sagt das und beendet sich entsprechend, statt Rauschen als Ersparnis zu melden.",

    "foot.by": "Gebaut von Arsalan Khadim",
  },
};
