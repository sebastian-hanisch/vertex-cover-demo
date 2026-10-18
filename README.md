# Knotenüberdeckung: Approximation, Kernbildung, Verzweigen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-vertex-cover-demo.streamlit.app/)** -->

Drittes Stück der **Härte-und-Struktur-Reihe** der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Reihe fragt, welche Struktur ein auf Graphen schweres Problem leicht macht. Das erste Stück ([bron-kerbosch-demo](https://github.com/sebastian-hanisch/bron-kerbosch-demo)) zählt alle maximalen Cliquen auf, das zweite ([max-clique-demo](https://github.com/sebastian-hanisch/max-clique-demo)) sucht die größte. Dieses Stück stellt die Frage vom anderen Ende: **Wie wenige Sendungen muss man auslagern, damit kein Konflikt mehr übrig bleibt?** Das ist eine **Knotenüberdeckung** im **Konfliktgraphen** einer Sammelladung (Sendung = Knoten, **Kante = „dürfen nicht zusammen verladen werden“**, also umgekehrt zu den beiden Cliquen-Demos). Die kleinste Überdeckung τ und die größte unabhängige Menge α ergeben zusammen n; die Sendungen außerhalb einer kleinsten Überdeckung sind eine größte konfliktfreie Fuhre (Kante `idee` zu den Cliquen-Stücken über das Komplement). Anders als die Fall-Demos zeigt die Demo ein Verfahren an einem wachsenden Beispiel.

```
Bron–Kerbosch: alle maximalen Cliquen (Wurzel)
 ├─ Größte Clique: Färbungsschranke und Kernzahl
 ├─ Knotenüberdeckung: Approximation, Kernbildung, Verzweigen            [DIESES STÜCK]
 ├─ Chordale und perfekte Graphen
 │    └─ Baumweite ─ Dynamische Programmierung auf der Baumzerlegung
 ├─ Kantenclique-Überdeckung und Kernbildung
 └─ Unabhängige Menge im großen Maßstab: Reduktionen und Lokalsuche
```

## Warum dieses Problem

Konflikte zwischen Sendungen entstehen oft an wenigen Stellen: ein paar Gefahrgut- oder Sonderfälle, die mit vielen anderen nicht zusammenpassen. Wer diese auslagert, löst alles. Die Demo geht drei Wege auf einer Kette: **Näherung** (schnell, nicht optimal: Matching-Verfahren, Greedy nach Höchstgrad, LP-Rundung), **Kern** (vorab entscheiden, was sich entscheiden lässt: LP-Kern nach Nemhauser und Trotter, Grad-1-Regel, Buss) und **Verzweigen** („gibt es eine Überdeckung der Größe ≤ k?“: auf einer Kante gegen auf dem Knoten höchsten Grades). Die Kernfragen: **Wie weit liegt die einfache Näherung vom Optimum, und wann zahlt sich ein kleiner Parameter k aus?**

Abgrenzung: Die Knotenüberdeckung kommt in `hopcroft-karp-demo`, `augmenting-path-demo` und `fahrzeugflotte-demo` nur als **König-Beweis** vor (bipartit, aus dem Matching abgeleitet); als Optimierungsproblem auf allgemeinen Graphen ist sie neu. Formal ist sie ein Spezialfall der Mengenüberdeckung (jede Kante hat genau zwei überdeckende Knoten; `ems_demo`, `shift_demo`, `crew-pairing-demo`, `p-center-demo`); hier geht es graphtheoretisch um den Faktor 2, den Kern und das Verzweigen, nicht um ein Standortmodell.

## Modell

Ungerichteter Konfliktgraph G = (V, E). Eine Überdeckung ist eine Sendungsmenge, die jede Kante berührt. Graphtypen: **Zufallsregeln** (jedes Paar unabhängig im Konflikt), **Zeitfenster** (Konflikt, wenn die Fenster überlappen: ein Intervallgraph), **Klassenregeln** (sechs Klassen, ein Klassenpaar steht im Konflikt oder nicht), **Wenige Verursacher** (⌈n/20⌉ Sendungen stehen mit dem eingestellten Anteil der übrigen im Konflikt, dazu ebenso viele Zufallskonflikte zwischen den übrigen). Feste Vergleichsgraphen: Baum, Gitter, skalenfrei, vollständig bipartit, die Greedy-Falle. Alle Graphen sind synthetisch; der Zufall kommt aus `random.Random(seed)`, die Algorithmen sind vollständig deterministisch (Gleichstand: kleinster Index). Formeln und Literatur stehen im 📐-Expander der App.

## Methodik

| Verfahren | Idee |
|---|---|
| **Matching-Verfahren** | Kanten in fester Reihenfolge; eine Kante wird genommen, wenn beide Enden frei sind; die Überdeckung sind alle Endpunkte. Es gilt \|M\| ≤ τ ≤ 2\|M\|. |
| **Greedy nach Höchstgrad** | Immer die Sendung mit den meisten offenen Konflikten auslagern. |
| **LP-Rundung** | Der LP (x_u + x_v ≥ 1) wird **selbst** gelöst: Jeder Knoten wird im bipartiten Doppelgraphen zu v_L und v_R, ein größtes Matching und die König-Überdeckung liefern eine optimale halbganzzahlige Lösung. Dazu die **Sondierung**: Wird der LP-Wert gehalten, wenn man eine Sendung auf 1 (oder auf 0 mit allen Nachbarn auf 1) setzt, ist das wieder eine optimale halbganzzahlige Lösung und die Sendung persistent. Gerundet wird die Menge „x = 1“ plus Kern. |
| **Buss** | Eine Sendung mit mehr als k offenen Konflikten gehört in jede Überdeckung der Größe ≤ k; danach hat ein Ja-Kern höchstens k′² Kanten. |
| **Grad-1-Regel** | Hat eine Sendung nur einen Konflikt, gibt es eine kleinste Überdeckung mit deren Partner. |
| **Verzweigen auf einer Kante** | u oder v hinein: Suchbaum mit 2^k Blättern. |
| **Verzweigen auf dem Grad** | Sendung mit dem höchsten Grad d ≥ 3: sie hinein oder alle ihre Partner hinein; bei Maximalgrad ≤ 2 (Pfade und Kreise) exakt in Polynomialzeit. |
| **Exakt** | LP-Kern, dann iterative Vertiefung über k ab der LP-Untergrenze mit Gradregel und Grad-1-Regel. Die Gegenprobe in den Tests ist HiGHS (`scipy.optimize.milp`). |

Die App hat zwei Tabs („Näherung“ und „Verzweigen und Kerne“), vergleicht alle Verfahren und Regeln live und rechnet vier Experimente.

## Befunde (gemessen, keine Behauptungen)

Jede Zahl steht in `tests/test_claims.py`. Alle Zähl- und Größenwerte sind ganzzahlig und plattformunabhängig exakt. Die Strukturtabellen sind Mediane über drei feste Graphen (`SWEEP_SEEDS`); Faktoren = Größe der Überdeckung / τ. In der Hauptansicht ist jede Regel auf 200 000 Knoten begrenzt, in den Sweeps auf 5 000 (Kantenregel: 2 000).

| Frage | Befund |
|---|---|
| Standardfall (10 Sendungen, 30 %, Seed 3)? | τ = 4. Matching-Verfahren 6 (Faktor 1,50), Greedy 4, LP-Rundung 4. LP-Kern: 4 hinein, 6 heraus, kein Kern. Für k = 4: Kante 9 Knoten, Grad 3, Grad + Grad-1-Regel 1, Buss 1. |
| Wie nah kommt das Matching-Verfahren dem Optimum? | Median-Faktor **1,15 bis 2,00** über elf Strukturen; **genau 2,00 auf dem Gitter 10 × 10** (perfektes Matching), im ungünstigsten der drei Graphen auch bei Klassenregeln (n = 60) und wenigen Verursachern (n = 200); nie darüber. Zufall n = 60, 5 %: 1,67; Baum: 1,64. |
| Und Greedy nach Höchstgrad? | **Faktor höchstens 1,11 in allen elf Strukturen** (Median 1,00 bis 1,04), also fast optimal. **Aber ohne Garantie:** Auf der Greedy-Falle (τ = a) wächst der Faktor 1,00 (a = 4), 1,33 (6), 1,50 (8), 1,92 (12), **2,13 (16), 2,50 (24)**, während das Matching-Verfahren dort überall genau 2,00 bleibt; ab a = 16 liegt Greedy über dessen Garantie. |
| Und die LP-Rundung? | **Exakt (Faktor 1,00)**, wo der LP ganzzahlig ist: Baum, Gitter, skalenfrei m = 2, wenige Verursacher. **Bis 1,89** (skalenfrei n = 200, m = 4: überall x = ½, die Rundung nimmt alle 200 Sendungen gegen τ = 108), dort schlechter als das Matching-Verfahren (1,46). LP-Wert / τ: 0,58 (Zeitfenster) bis 1,00. |
| Wie viel entscheidet der LP-Kern? | **Bipartit (Baum, Gitter): kein Kern**, und τ ist gleich der Matchinggröße (Satz von König, bestätigt). Dünne Zufalls- und Klassengraphen: Teilkern (Zufall n = 60, 5 %: 19 von 60; Klassenregeln: 6 von 60; Zufall n = 100, 3 %: 48 von 100). **Der ganze Graph** bleibt Kern bei Zufall n = 40 (20 % und 50 %), Zeitfenster n = 60 und skalenfrei m = 4. Wenige Verursacher: 20 hinein, 180 heraus, kein Kern. |
| Wie lange braucht das Verzweigen? | Preset „Dicht“ (40 Sendungen, 50 %, k = τ = 33): **Kante > 200 000 Knoten (abgebrochen)**, Grad 47, Grad + Grad-1-Regel 33, Buss 33. Preset „Dünn“ (60 Sendungen, 5 %, k = τ = 27): Kante > 200 000, Grad 17, **Grad + Grad-1-Regel und Buss je 1 Knoten**. Preset „Zeitfenster“ (k = τ − 1 = 31, Nein-Instanz): Kante > 200 000, Grad 3 929, Grad + Grad-1-Regel und Buss 2 887: Hier muss die Verzweigung die Nichtexistenz beweisen. |
| Wann hilft die Kernbildung nach Buss? | **Nur bei kleinem k.** Preset „Dicht“: k′ = 33 und alle 412 Kanten bleiben, alle 40 Sendungen haben einen Konflikt (Buss streicht nichts). Preset „Wenige Verursacher“ (60 Sendungen, k = 5, Nein-Instanz): **k′ = 2, 3 Kanten, 6 Sendungen**, die Antwort fällt mit 1 Knoten. Experiment 4 (n = 100, k = τ − 1): Bei 16 Verursachern bleiben von 541 Kanten **16** im Kern, im Zufallsgraphen mit denselben 541 Kanten alle 541. |
| Wie unterscheiden sich wenige Verursacher von Zufall bei gleicher Kantenzahl? | Bei 2, 4, 8, 12, 16 Verursachern: Grad + Grad-1-Regel 1, 1, 1, 1, 4 Knoten, Grad ohne Grad-1-Regel 3, 5, 9, 13, 19 (Zufall mit gleichen Kanten: 2 067, > 5 000, > 5 000, 54, 85), Kantenregel bei 2 und 4 Verursachern 15 und 255 Knoten, danach über 2 000. Der Zufallsgraph wird durch die Grad-1-Regel ebenfalls schnell (1, 8, 24, 37, 50 Knoten, dort steht für τ teils die Greedy-Größe, siehe unten): der Gewinn von Buss liegt im Kern, nicht in der Knotenzahl allein. |
| Gilt τ = n − α? | Ja, auf dem Standardgraph mit 14 Sendungen: τ = 7 = 14 − 7, geprüft gegen das Aufzählen aller Teilmengen des Komplements (ohne Verzweigen). |

## Befunde und Korrekturen gegenüber dem Plan

Vor dem Bau lag eine Vormessung vor (LP-Lösung per HiGHS, exakte Werte per HiGHS). **Das Bild blieb im Kern, einzelne Zahlen änderten sich, weil der LP jetzt selbst gelöst wird:** Die erste König-Lösung aus dem Doppelgraphen ist auf Graphen mit perfektem Matching überall ½ (auch auf einem Pfad); erst die **Sondierung** macht daraus eine ganzzahlige Zerlegung auf Bäumen und Gittern. Der Kern ist dadurch teils größer als die Ecke von HiGHS (Zufall n = 100, 3 %: 48 gegen 38 von 100 in der Vormessung), teils kleiner (Zufall n = 60, 5 %: 19 gegen 36 von 60). Weitere Abweichungen vom Einzelplan: Die Vormessung nannte für wenige Verursacher „Grad + Grad-1-Regel: 1 Knoten in allen fünf Instanzen“; mit den endgültigen Instanzen (n = 100, 2 bis 16 Verursacher) sind es 1, 1, 1, 1 und 4 Knoten. Die Grad-1-Regel macht auch den Zufallsgraphen gleicher Kantenzahl für die Gradregel handhabbar; die Aussage der Demo ist deshalb nicht „Zufall ist unlösbar“, sondern „der **Kern** schrumpft nur bei kleinem k“. Kein PDF-Export (Konzepte-Demos haben üblicherweise keinen). Kein scipy zur Laufzeit: LP und exakte Lösung sind selbst gebaut, `scipy` und `networkx` stehen nur in `requirements-dev.txt` für die Gegenproben.

## Ehrliche Grenzen

- **Knoten statt Laufzeit.** Die Demo zählt Knoten des Suchbaums, keine Laufzeit; jeder Knoten kostet je nach Regel verschieden viel.
- **Der Kern ist nicht kanonisch.** Der LP hat meist viele optimale Lösungen; die Sondierung findet eine, nicht die mit dem kleinsten Kern. Andere Löser (HiGHS-Ecke) liefern andere Kerne.
- **Zufallsvergleich mit Greedy-Bezug.** In Experiment 4 wurde die exakte Lösung auf 20 000 Knoten begrenzt; beim Zufallsgraphen mit 8, 12 und 16 Verursachern (2, 3 und 3 von 3 Graphen) steht für τ die Greedy-Größe, k = Greedy − 1.
- **Rekordalgorithmen und Branch-and-Reduce** (viele weitere Regeln, Lokalsuche) lösen Graphen mit Millionen Kanten; hier nur als Einordnung im Mathematik-Expander.
- **Ungewichtet.** Mit Kosten je Sendung ändern sich Matching-Verfahren und Greedy.
- **Paarkonflikte.** Regeln für Dreiergruppen sind eine Mengenüberdeckung im Hypergraphen.
- **Kleine Graphen, synthetische Daten.** Hauptansicht bis n = 60, Strukturen bis n = 200; keine echten Sendungsdaten.

## Verifikation

- **Kern:** jede Einheit (`maximal_matching`, `greedy_degree_cover`, `lp_solution`, `nt_split`, `lp_kernel`, `buss_kernel`, `reduce_degree_one`, `cover_paths_and_cycles`, `decide`, `exact_cover`) gegen Handrechnung auf den Mini-Instanzen (Pfad, Fünfeck, Dreieck mit Pendel, Stern); Knotenzahlen der Verzweigungsregeln von Hand gerechnet (Pfad: Kante 3 und 4 Knoten für k = 1 und 2, Grad 1).
- **Orakel (`tests/test_oracle_vertex_cover.py`):** τ aus `exact_cover` gleich `scipy.optimize.milp` (HiGHS), gleich n − α(G) mit α aus `networkx.max_weight_clique` auf dem Komplement, auf über 300 festen Zufalls-, Zeitfenster-, Klassen-, Verursacher-, Baum-, Gitter- und Sonderinstanzen; gleich Brute Force (n ≤ 14); LP-Wert gleich `scipy.optimize.linprog`; auf bipartiten Graphen τ gleich der Größe des größten Matchings von `networkx` (König) und der LP-Kern leer; alle vier Verzweigungsregeln antworten für k = τ − 1 und k = τ wie HiGHS; das Matching-Verfahren hält \|M\| ≤ τ ≤ 2\|M\|.
- **Invarianten:** Nemhauser–Trotter: τ(G) = \|forced\| + τ(Kern), und Sendungen mit x = 0 haben nur Nachbarn in `forced` (gegen Brute Force, 30 Instanzen); Greedy-Falle reproduziert 8, 23, 60 gegen 6, 12, 24; K_{a,a}: Matching nimmt 2a.
- **Zweige (`tests/test_branches.py`):** jede Regel, die Sondierung (ohne sie bliebe ein Pfad ganz im Kern), die Grad-1-Regel, Buss weichen auf mindestens einer Instanz ab; die Rechengrenzen greifen; jeder Regler an jeder Grenze.
- **Zahlen:** `tests/test_claims.py` rechnet jede Zahl dieser README über dieselben Auswertungsfunktionen wie die App nach.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum, jede Regelart, jedes Verfahren, jede Regel, Extrem-Seeds, Permalink, Preset-Hervorhebung, fester Kopf) und Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: zwei Tabs, Kernfragen, vier Experimente, Brücken, Grenzen, Mathematik |
| `vcv_algorithm.py` | Kern: Näherungen, LP über den Doppelgraphen, Sondierung, Buss, Grad-1-Regel, Verzweigungsregeln, exakte Lösung |
| `vcv_constants.py` | Regler-Grenzen, Rechengrenzen, Farben, Presets |
| `vcv_evaluation.py` | Einstellungen, Analyse, Strukturtabelle, Greedy-Falle, Verursacher-Vergleich, Komplement-Prüfung |
| `vcv_layout.py` | fester Kopf (Gerüst aus `new_demo.py`) |
| `vcv_presets.py` | Permalink (Begrenzen), Presets in der Seitenleiste mit Hervorhebung, Zufalls-Seed-Button |
| `vcv_scenario.py` | Graphen: Zufall, Zeitfenster, Klassenregeln, wenige Verursacher, Baum, Gitter, skalenfrei, K_{a,a}, Greedy-Falle |
| `vcv_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest, networkx und scipy (nur für die Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Algorithmus, Orakel, Zweige, Szenarien, Zahlen, Figuren, Presets, Layout, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Rekordalgorithmus und Branch-and-Reduce** (viele weitere Reduktionsregeln, Dominanz, Falten von Grad-2-Knoten, Lokalsuche): Einordnung im Mathematik-Expander.
- **Gewichtete Überdeckung** und **Hypergraphen** (Mengenüberdeckung).
- **PDF-Export** (siehe Korrekturen oben).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Literatur

- Nemhauser, G. L., & Trotter, L. E. (1975). *Vertex packings: structural properties and algorithms.* Mathematical Programming 8, 232–248.
- Buss, J. F., & Goldsmith, J. (1993). *Nondeterminism within P.* SIAM Journal on Computing 22(3), 560–572.
- Harris, D. G., & Narayanaswamy, N. S. (2024). *A faster algorithm for vertex cover parameterized by solution size.* STACS 2024, arXiv:2205.08022.

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
