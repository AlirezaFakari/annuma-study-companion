"""
build_db.py
-----------
Knowledge database builder for the AnNuMa Study Companion.

This script creates a SQLite database (knowledge.db) that stores AnNuMa
lecture summaries together with a recall question and its answer. Both the
MCP server (agent interface) and the Flask web app read from this same
database in READ-ONLY mode.

Design note:
    Each row is one focused sub-topic and carries a ready-made recall
    question and answer. This lets the self-contained web app present real
    flashcards without needing an LLM, while the content stays grounded in
    the student's verified study material.

Table schema:
    id        : unique auto-increment id
    topic     : sub-topic, e.g. "Geometrische Reihe"
    source    : which lecture it comes from, e.g. "V6"
    type      : content type: "summary"
    content   : the full study content (German, as in the course)
    question  : a recall question for this sub-topic
    answer    : the answer, drawn from the content
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge.db")


def build_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE knowledge (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            topic    TEXT NOT NULL,
            source   TEXT NOT NULL,
            type     TEXT NOT NULL,
            content  TEXT NOT NULL,
            question TEXT NOT NULL,
            answer   TEXT NOT NULL
        )
    """)

    # ---- Real AnNuMa study content (V1 and V6) ----
    # content = study material (German, as in the course)
    # question / answer = a recall flashcard derived from that content
    data = [
        # ===================== V1: Logik & Mengenlehre =====================
        (
            "Aussagen und Aussageformen", "V1", "summary",
            "Eine Aussage ist eine sprachliche Feststellung, die entweder wahr (w) "
            "oder falsch (f) ist. Eine Aussageform ist eine Feststellung, deren "
            "Wahrheitswert von einer oder mehreren Variablen abhaengt (z.B. x > y); "
            "setzt man feste Werte ein, wird sie zur Aussage.",
            "What is the difference between an Aussage and an Aussageform?",
            "An Aussage is a statement that is definitely true or false. An "
            "Aussageform contains variables, so its truth value depends on what is "
            "substituted; fixing the variables turns it into an Aussage."
        ),
        (
            "Junktoren", "V1", "summary",
            "Junktoren verknuepfen Aussagen. Negation, Konjunktion (UND, wahr nur wenn "
            "beide wahr), Disjunktion (ODER, falsch nur wenn beide falsch), Implikation "
            "(A => B, falsch nur wenn A wahr und B falsch), Aequivalenz. De Morgan: "
            "NICHT(A ODER B) = (NICHT A) UND (NICHT B). Implikation: A => B = (NICHT A) ODER B.",
            "When is the implication A => B false, and how can it be rewritten without =>?",
            "A => B is false only when A is true and B is false. It can be rewritten as "
            "(NOT A) OR B."
        ),
        (
            "Quantoren", "V1", "summary",
            "Allquantor (fuer alle x gilt A(x)). Existenzquantor (es existiert ein x mit "
            "A(x)). Verneinung: NICHT(fuer alle x: A(x)) = es existiert x mit NICHT A(x); "
            "NICHT(es existiert x: A(x)) = fuer alle x gilt NICHT A(x).",
            "How do you negate the statement 'for all x: A(x)'?",
            "It becomes 'there exists an x such that NOT A(x)'. Negation swaps the "
            "quantifier (for-all becomes exists) and negates the inner statement."
        ),
        (
            "Beweistechniken", "V1", "summary",
            "Direkter Beweis: V => A1 => ... => B. Indirekter Beweis (Kontraposition): "
            "NICHT B => ... => NICHT V. Widerspruchsbeweis: (V UND NICHT B) => Widerspruch. "
            "Fallunterscheidung: ist V = V1 ODER V2, zeige V1 => B und V2 => B getrennt.",
            "Name the four proof techniques from V1 and the core idea of each.",
            "Direct (V leads step by step to B), contraposition (assume NOT B, derive NOT V), "
            "contradiction (assume V and NOT B, reach a contradiction), and case distinction "
            "(split V into cases and prove each)."
        ),
        (
            "Mengen und Mengenoperationen", "V1", "summary",
            "Teilmenge A Teilmenge B: jedes a aus A ist auch in B. Schnitt: Elemente in A und B. "
            "Vereinigung: Elemente in A oder B. Differenz A ohne B: in A und nicht in B. "
            "Komplement: Elemente der Grundmenge nicht in A. Disjunkt: Schnitt ist leer.",
            "What does it mean for two sets to be disjunkt (disjoint)?",
            "Two sets are disjoint when their intersection is empty, i.e. they share no elements."
        ),
        (
            "Potenzmenge", "V1", "summary",
            "Die Potenzmenge P(A) ist die Menge aller Teilmengen von A. Stets ist die leere "
            "Menge in P(A) und A in P(A). Anzahl der Elemente von P(A) = 2 hoch (Anzahl "
            "Elemente von A).",
            "If a set A has n elements, how many elements does its power set P(A) have?",
            "2^n. The power set contains all subsets of A, including the empty set and A itself."
        ),
        (
            "Kartesisches Produkt und Tupel", "V1", "summary",
            "Ein geordnetes Paar (a,b) beachtet die Reihenfolge. Das kartesische Produkt "
            "A x B ist die Menge aller geordneten Paare (a,b) mit a aus A und b aus B. "
            "Im Allgemeinen ist A x B ungleich B x A. A x B ist leer genau dann wenn A "
            "oder B leer ist.",
            "When is the cartesian product A x B empty?",
            "A x B is empty exactly when A is empty or B is empty (or both)."
        ),

        # ===================== V6: Reihen & Konvergenzkriterien =====================
        (
            "Reihe und Partialsumme", "V6", "summary",
            "Eine Reihe ist die Folge der Partialsummen. Aus einer Folge (a_n) bildet man "
            "s_n = a_1 + ... + a_n. Die Reihe IST die Folge (s_n). Konvergiert (s_n), heisst "
            "der Grenzwert die Summe. 'Reihe konvergiert' bedeutet 'Folge der Partialsummen "
            "konvergiert'.",
            "What does it mean, precisely, for a series (Reihe) to converge?",
            "A series converges exactly when its sequence of partial sums $s_n$ converges. "
            "Convergence of a series is always reduced to convergence of the partial sums."
        ),
        (
            "Geometrische Reihe", "V6", "summary",
            "Formel (auswendig): Summe x^k von k=0 bis unendlich = 1/(1-x) fuer |x| < 1. "
            "Konvergiert nur wenn |x| < 1; fuer |x| >= 1 divergiert sie. "
            "Beispiel: x = 1/2 gibt Summe 2; x = -1/2 gibt Summe 2/3.",
            "Under what condition does the geometric series $\\sum_{k=0}^{\\infty} x^k$ converge, and what is its sum?",
            "It converges if and only if $|x| < 1$, and the sum is $\\frac{1}{1-x}$. For $|x| \\ge 1$ it diverges."
        ),
        (
            "Nullfolgenkriterium", "V6", "summary",
            "Notwendiges Kriterium: Ist (a_n) keine Nullfolge, dann divergiert die Reihe. "
            "Aber: a_n geht gegen 0 garantiert NICHT Konvergenz (Gegenbeispiel: harmonische "
            "Reihe). Das Kriterium ist nur notwendig, nicht hinreichend.",
            "If the terms a_n of a series go to 0, does the series necessarily converge?",
            "No. Going to 0 is necessary but not sufficient. The harmonic series is the classic "
            "counterexample: its terms go to 0 but the series diverges."
        ),
        (
            "Harmonische Reihe", "V6", "summary",
            "Die Reihe Summe 1/k divergiert. Beweis-Trick: Bloecke buendeln, jeder Block ist "
            ">= 1/2, also werden die Partialsummen unbeschraenkt. Dient als Minorante und "
            "zeigt, dass Nullfolge nicht reicht.",
            "Does the harmonic series (sum of 1/k) converge or diverge?",
            "It diverges. Grouping the terms into blocks, each block is >= 1/2, so the partial "
            "sums grow without bound."
        ),
        (
            "Leibniz-Kriterium", "V6", "summary",
            "Fuer alternierende Reihen: Ist (a_n) eine monoton fallende Nullfolge mit a_n >= 0, "
            "dann konvergiert die Reihe Summe (-1)^n a_n. Drei Bedingungen pruefen: a_n >= 0, "
            "monoton fallend, geht gegen 0.",
            "Which three conditions must $a_n$ satisfy for the Leibniz criterion to guarantee convergence?",
            "$a_n \\ge 0$, $a_n$ is monotonically decreasing, and $a_n \\to 0$. If all three "
            "hold, the alternating series $\\sum (-1)^n a_n$ converges."
        ),
        (
            "Majoranten- und Minorantenkriterium", "V6", "summary",
            "Majorante (Konvergenz): a_n <= c_n und Summe c_n konvergiert => Summe a_n "
            "konvergiert. Minorante (Divergenz): a_n >= c_n >= 0 und Summe c_n divergiert => "
            "Summe a_n divergiert. Standard-Vergleiche: geometrische Reihe und Summe 1/k^2.",
            "What does the majorant criterion let you conclude, and in which direction?",
            "If $a_n \\le c_n$ and the larger series $\\sum c_n$ converges, then $\\sum a_n$ "
            "also converges (absolutely). A majorant only shows convergence; a minorant only "
            "shows divergence."
        ),
        (
            "Quotientenkriterium", "V6", "summary",
            "Gilt |a_(n+1)/a_n| <= c < 1 fuer fast alle n, dann konvergiert die Reihe absolut. "
            "Erste Wahl bei Fakultaeten (k!) und Potenzen (x^n). Falle: Grenzwert = 1 gibt "
            "KEINE Aussage; es braucht ein echtes c < 1.",
            "For the ratio test (Quotientenkriterium), what happens if the ratio's limit equals 1?",
            "The test gives no conclusion. You need a genuine bound c < 1; a limit of exactly 1 "
            "means the criterion fails and another method is required."
        ),
        (
            "Wurzelkriterium", "V6", "summary",
            "Gilt die n-te Wurzel aus |a_n| <= c < 1 fuer fast alle n, dann konvergiert die "
            "Reihe absolut. Erste Wahl wenn a_n eine n-te Potenz ist. Bei Grenzwert = 1 keine "
            "Aussage.",
            "When is the root test (Wurzelkriterium) the natural first choice?",
            "When a_n is an n-th power, e.g. a_n = (something)^n. You check whether the n-th root "
            "of |a_n| stays below some c < 1."
        ),
        (
            "Absolute Konvergenz", "V6", "summary",
            "Eine Reihe heisst absolut konvergent, wenn Summe |a_n| konvergiert. Absolut "
            "konvergent impliziert konvergent, aber nicht umgekehrt (alternierende harmonische "
            "Reihe: konvergent, nicht absolut). Absolut konvergente Reihen darf man umordnen.",
            "Does absolute convergence imply convergence, and does the converse hold?",
            "Absolute convergence implies convergence, but the converse is false. The alternating "
            "harmonic series converges but not absolutely."
        ),

        # ===================== V7: Exponentialfunktion & Reelle Funktionen =====================
        (
            "Exponentialreihe", "V7", "summary",
            "Die zentrale Reihendarstellung der Exponentialfunktion: exp(x) = Summe x^k/k! "
            "von k=0 bis unendlich = 1 + x + x^2/2 + x^3/6 + ... Sie konvergiert fuer jedes "
            "reelle x absolut (Nachweis per Quotientenkriterium, da der Quotient |x|/(n+1) "
            "gegen 0 geht). Falle: das k! im Nenner nicht vergessen - exp(x) ist NICHT Summe x^k.",
            "What is the exponential series for $\\exp(x)$, and for which $x$ does it converge?",
            "$\\exp(x) = \\sum_{k=0}^{\\infty} \\frac{x^k}{k!} = 1 + x + \\frac{x^2}{2} + \\dots$ "
            "It converges absolutely for every real $x$. The key is the $k!$ in the denominator."
        ),
        (
            "Funktionalgleichung von exp", "V7", "summary",
            "Die wichtigste Eigenschaft der Exponentialfunktion: exp(x + y) = exp(x) * exp(y) "
            "fuer alle reellen x, y. Beweis ueber das Cauchy-Produkt der beiden Reihen plus "
            "binomischen Lehrsatz. Folgerungen: exp(-x) = 1/exp(x), exp(x) > 0 fuer alle x, "
            "und exp(n) = e^n fuer ganze Zahlen n.",
            "State the functional equation of exp and one important consequence.",
            "exp(x+y) = exp(x)*exp(y). A key consequence is exp(-x) = 1/exp(x), which also "
            "shows exp(x) is always positive."
        ),
        (
            "Grenzwert einer Funktion", "V7", "summary",
            "Zwei aequivalente Definitionen. Folgen-Definition (Heine): lim_{x->a} f(x) = c "
            "genau dann, wenn fuer JEDE Folge x_n aus D mit x_n -> a gilt f(x_n) -> c. "
            "Epsilon-Delta: zu jedem epsilon > 0 gibt es ein delta > 0, sodass |x - a| < delta "
            "impliziert |f(x) - c| < epsilon. Die Folgen-Definition eignet sich gut, um einen "
            "Grenzwert zu widerlegen (eine passende Folge finden).",
            "Give the sequence-based (Heine) definition of the limit of a function at a point.",
            "$\\lim_{x\\to a} f(x) = c$ means: for EVERY sequence $x_n$ in the domain with "
            "$x_n \\to a$, the images satisfy $f(x_n) \\to c$. It is equivalent to the "
            "epsilon-delta definition."
        ),

        # ===================== V8: Stetigkeit, Nullstellensatz, Umkehrfunktion =====================
        (
            "Stetigkeit", "V8", "summary",
            "Eine Funktion f ist stetig in a genau dann, wenn lim_{x->a} f(x) = f(a) "
            "(kein Sprung - der Grenzwert ist der Funktionswert). Epsilon-Delta: zu jedem "
            "epsilon > 0 gibt es delta > 0 mit |x - a| < delta => |f(x) - f(a)| < epsilon. "
            "Summe, Produkt, Vielfaches, Kehrwert und Komposition stetiger Funktionen sind "
            "stetig; Polynome und rationale Funktionen sind auf ihrem Definitionsbereich stetig.",
            "What is the definition of f being continuous at a point a?",
            "f is continuous at a exactly when lim x->a f(x) = f(a): the limit exists and equals "
            "the function value, so there is no jump."
        ),
        (
            "Nullstellensatz (Bolzano)", "V8", "summary",
            "Ist f stetig auf einem abgeschlossenen Intervall [a,b] und haben f(a) und f(b) "
            "verschiedene Vorzeichen (z.B. f(a) < 0 < f(b)), dann gibt es ein c in [a,b] mit "
            "f(c) = 0. Anschaulich: wechselt das Vorzeichen, muss irgendwo eine Nullstelle "
            "liegen. Beweis-Idee: Intervallhalbierung.",
            "State the Nullstellensatz (Bolzano's theorem) and its intuition.",
            "If f is continuous on [a,b] and f(a), f(b) have opposite signs, then f has a zero "
            "c in [a,b]. Intuitively: a sign change forces a root somewhere in between."
        ),
        (
            "Satz vom Minimum und Maximum", "V8", "summary",
            "Ist f stetig auf einem ABGESCHLOSSENEN Intervall [a,b], dann ist f beschraenkt "
            "und nimmt sein Maximum und Minimum tatsaechlich an. Warnung: das gilt NICHT auf "
            "offenen Intervallen - Gegenbeispiel f(x) = 1/x auf (0,1) ist stetig, aber "
            "unbeschraenkt.",
            "On what kind of interval does a continuous function attain its max and min, and why the restriction?",
            "On a closed interval [a,b]. It fails on open intervals: f(x)=1/x on (0,1) is "
            "continuous but unbounded, so it attains no maximum."
        ),
        (
            "Umkehrfunktion", "V8", "summary",
            "Ist f stetig und streng monoton auf [a,b], dann ist f bijektiv auf sein "
            "Bildintervall, und die Umkehrfunktion f^{-1} ist ebenfalls stetig und streng "
            "monoton. Streng wachsend bedeutet: x < y impliziert f(x) < f(y). "
            "Beispiel: x^k und die k-te Wurzel sind zueinander invers.",
            "Which conditions on f guarantee that a continuous inverse function exists?",
            "If f is continuous and strictly monotonic on [a,b], it is bijective onto its image "
            "and its inverse is also continuous and strictly monotonic."
        ),

        # ===================== V9: Differentialrechnung =====================
        (
            "Ableitung (Definition)", "V9", "summary",
            "Die Ableitung ist der Grenzwert des Differenzenquotienten: f'(x) = lim_{h->0} "
            "(f(x+h) - f(x))/h. Anschaulich die Steigung der Tangente / momentane "
            "Aenderungsrate. Schluessel-Satz: differenzierbar impliziert stetig, aber die "
            "Umkehrung ist falsch - |x| ist in 0 stetig, aber nicht differenzierbar "
            "(links Steigung -1, rechts +1).",
            "Define the derivative f'(x) as a limit, and does differentiability imply continuity?",
            "f'(x) = lim h->0 (f(x+h)-f(x))/h. Differentiability implies continuity, but not "
            "the reverse: |x| is continuous at 0 yet not differentiable there."
        ),
        (
            "Ableitungsregeln", "V9", "summary",
            "Produktregel: (fg)' = f'g + fg'. Quotientenregel: (f/g)' = (f'g - fg')/g^2. "
            "Kettenregel: (g(f(x)))' = g'(f(x)) * f'(x). Umkehrregel: (f^{-1})'(y) = "
            "1/f'(f^{-1}(y)). Grund-Ableitungen: (x^n)' = n*x^(n-1), exp' = exp, ln'(x) = 1/x, "
            "(a^x)' = a^x * ln(a).",
            "State the product rule and the chain rule for derivatives.",
            "Product rule: (fg)' = f'g + fg'. Chain rule: (g(f(x)))' = g'(f(x)) * f'(x)."
        ),
        (
            "Hoehere Ableitungen", "V9", "summary",
            "Wiederholtes Ableiten. Wichtige Formeln: (x^n)^(k) = n!/(n-k)! * x^(n-k) fuer "
            "k <= n; exp^(k) = exp; (a^x)^(n) = (ln a)^n * a^x. Leibnizregel fuer das k-te "
            "Ableiten eines Produkts: (fg)^(k) = Summe_{i=0}^k (k ueber i) f^(k-i) g^(i).",
            "What is the n-th derivative of a^x?",
            "(a^x)^(n) = (ln a)^n * a^x. Each differentiation brings down another factor of ln(a)."
        ),

        # ===================== V10: Ableitungssaetze =====================
        (
            "Mittelwertsatz (MWT)", "V10", "summary",
            "Ist f auf [a,b] stetig und auf (a,b) differenzierbar, dann gibt es ein c in (a,b) "
            "mit (f(b) - f(a))/(b - a) = f'(c): irgendwo ist die momentane Steigung gleich der "
            "mittleren Steigung. Zentral, weil daraus Monotonie, Konvexitaet und 'f' = 0 "
            "impliziert f konstant' folgen. Beweis ueber den Satz von Rolle.",
            "State the Mean Value Theorem (Mittelwertsatz).",
            "If $f$ is continuous on $[a,b]$ and differentiable on $(a,b)$, there is a "
            "$c \\in (a,b)$ with $\\frac{f(b)-f(a)}{b-a} = f'(c)$: the instantaneous slope "
            "equals the average slope somewhere."
        ),
        (
            "Ableitung und Monotonie", "V10", "summary",
            "Das Vorzeichen der Ableitung steuert die Monotonie: f' >= 0 auf einem Intervall "
            "bedeutet f waechst, f' > 0 bedeutet streng wachsend, f' <= 0 faellt, f' < 0 "
            "streng fallend. Folgt aus dem Mittelwertsatz.",
            "How does the sign of f' determine whether f is increasing or decreasing?",
            "f' >= 0 means f is increasing (f' > 0 strictly increasing); f' <= 0 means decreasing "
            "(f' < 0 strictly). This follows from the Mean Value Theorem."
        ),
        (
            "Konvexitaet", "V10", "summary",
            "Eine Funktion ist konvex, wenn ihr Graph unter jeder Sekante liegt: "
            "f(c*x + (1-c)*y) <= c*f(x) + (1-c)*f(y) fuer c in [0,1]. Kriterium ueber die "
            "zweite Ableitung: f'' >= 0 genau dann konvex, f'' <= 0 genau dann konkav.",
            "What is the second-derivative criterion for convexity?",
            "f is convex exactly when f'' >= 0 (graph lies below its secants), and concave exactly "
            "when f'' <= 0."
        ),
        (
            "Regel von L'Hospital", "V10", "summary",
            "Bei einem unbestimmten Ausdruck der Form 0/0 oder (plus/minus unendlich)/(plus/minus "
            "unendlich) gilt lim f/g = lim f'/g', sofern die rechte Seite existiert und g' "
            "ungleich 0 ist. Man leitet Zaehler und Nenner getrennt ab (nicht die Quotientenregel!).",
            "When can you apply L'Hospital's rule, and what does it say?",
            "For indeterminate forms $\\frac{0}{0}$ or $\\frac{\\infty}{\\infty}$, "
            "$\\lim \\frac{f}{g} = \\lim \\frac{f'}{g'}$, differentiating numerator and "
            "denominator separately, provided the right-hand limit exists."
        ),

        # ===================== V11: Integralrechnung =====================
        (
            "Hauptsatz der Differential- und Integralrechnung (HDI)", "V11", "summary",
            "Der zentrale Satz der Integralrechnung. Ist F(x) = Integral von a bis x von f(t) dt, "
            "dann ist F' = f. Fuer eine Stammfunktion F gilt Integral von a bis b von f(x) dx = "
            "F(b) - F(a) = [F(x)] von a bis b. Zwei Stammfunktionen unterscheiden sich nur um "
            "eine Konstante.",
            "State the Fundamental Theorem of Calculus (HDI).",
            "If F(x) = integral from a to x of f, then F' = f. And the definite integral from a to b "
            "of f equals F(b) - F(a) for any antiderivative F."
        ),
        (
            "Substitutionsregel", "V11", "summary",
            "Integrationsregel aus der Kettenregel: Integral von a bis b von f(g(t))*g'(t) dt = "
            "Integral von g(a) bis g(b) von f(x) dx. Wichtiger Spezialfall: Integral von g'/g = "
            "ln|g|. Man ersetzt g(t) durch eine neue Variable x und passt die Grenzen an.",
            "State the substitution rule for integration and its useful special case.",
            "Integral of f(g(t))*g'(t) dt = integral of f(x) dx with substituted bounds. Special "
            "case: integral of g'/g equals ln|g|."
        ),
        (
            "Partielle Integration", "V11", "summary",
            "Integrationsregel aus der Produktregel: Integral von a bis b von f*g' = "
            "[f*g] von a bis b - Integral von a bis b von f'*g. Nuetzlich, wenn ein Faktor beim "
            "Ableiten einfacher wird. Beispiel: Integral von ln(x) dx = x*(ln(x) - 1).",
            "State the formula for integration by parts.",
            "Integral of f*g' = [f*g] minus integral of f'*g. You trade the integral of f*g' for "
            "the integral of f'*g, which is often simpler."
        ),

        # ===================== V12: Komplexe Zahlen =====================
        (
            "Komplexe Zahlen - Grundlagen", "V12", "summary",
            "Eine komplexe Zahl ist ein Punkt z = a + b*i in der Gaussschen Zahlenebene, mit "
            "Realteil a und Imaginaerteil b und der imaginaeren Einheit i, wobei i^2 = -1. "
            "Rechnen: (a+bi)+(c+di) = (a+c)+(b+d)i; (a+bi)*(c+di) = (ac-bd)+(ad+bc)i. "
            "Achtung: C ist KEIN angeordneter Koerper - es gibt kein sinnvolles Kleiner-als.",
            "What defines the imaginary unit i, and can complex numbers be ordered by size?",
            "i is defined by i^2 = -1. Complex numbers cannot be ordered: C is not an ordered "
            "field, so there is no meaningful < on C."
        ),
        (
            "Konjugierte und Betrag", "V12", "summary",
            "Die konjugiert komplexe Zahl ist z-quer = a - b*i (Spiegelung an der reellen Achse). "
            "Der Betrag ist |z| = sqrt(z * z-quer) = sqrt(a^2 + b^2), also der Abstand vom "
            "Ursprung. Die Division ist der typische Rechenschritt: man erweitert Zaehler und "
            "Nenner mit dem Konjugierten des Nenners, um den Nenner reell zu machen.",
            "How do you divide two complex numbers?",
            "Multiply numerator and denominator by the conjugate of the denominator. This makes "
            "the denominator real (|denominator|^2), and you can read off real and imaginary parts."
        ),
        (
            "Polarform und Einheitswurzeln", "V12", "summary",
            "Eulersche Formel: e^(i*x) = cos(x) + i*sin(x), mit Betrag 1. Jede komplexe Zahl "
            "schreibt sich als z = r * e^(i*phi) mit r = |z| und Argument phi. Multiplikation "
            "in Polarform: Betraege multiplizieren, Winkel addieren. Die Gleichung z^n = 1 hat "
            "genau n Loesungen, die n-ten Einheitswurzeln z_k = e^(i*2*k*pi/n) fuer k = 0..n-1, "
            "gleichmaessig auf dem Einheitskreis verteilt.",
            "How many solutions does z^n = 1 have, and what form do they take?",
            "Exactly n solutions, the n-th roots of unity z_k = e^(i*2*k*pi/n) for k = 0..n-1, "
            "spread evenly around the unit circle."
        ),

        # ===================== V13: Computerzahlen =====================
        (
            "Zweierkomplement", "V13", "summary",
            "Darstellung ganzer Zahlen im Rechner. Eine negative Zahl entsteht durch Invertieren "
            "aller Bits plus 1. Der Bereich bei N Bits ist [-2^(N-1), 2^(N-1) - 1] - also "
            "ASYMMETRISCH (ein negativer Wert mehr). Vorteile gegenueber dem Einerkomplement: "
            "eindeutige Null und direkte Addition auch bei gemischten Vorzeichen. Deshalb "
            "Standard in der Praxis.",
            "What is the range of an N-bit two's complement integer, and why is it asymmetric?",
            "The range is [-2^(N-1), 2^(N-1) - 1], asymmetric because there is one more negative "
            "value than positive. This gives a unique zero and direct addition."
        ),
        (
            "Gleitkommaformat", "V13", "summary",
            "Normalisierte Darstellung reeller Zahlen: Wert = (-1)^s * d * 2^e, mit Mantisse "
            "d = 1 + (Nachkommabits) im Bereich [1, 2) und Exponent e = (Exponentbits) - Bias. "
            "Der maximale RELATIVE Fehler ist kleiner als 2^(-M) bei M Mantissenbits. "
            "Hidden bit: die fuehrende 1 der Mantisse wird nicht gespeichert.",
            "In a normalized floating-point number, what range does the mantissa lie in, and what is the 'hidden bit'?",
            "The mantissa d lies in [1, 2). The leading 1 is not stored (the hidden bit), which "
            "gives one extra bit of precision for free."
        ),
        (
            "IEEE 754", "V13", "summary",
            "Der Standard fuer Gleitkommazahlen. Einfache Genauigkeit: 32 Bit (1 Vorzeichen, "
            "23 Mantisse, 8 Exponent, Bias 127), etwa 7 Dezimalstellen. Doppelte Genauigkeit: "
            "64 Bit (52 Mantisse, 11 Exponent, Bias 1023), etwa 16 Dezimalstellen. "
            "Sonderfaelle ueber reservierte Exponenten: Null, plus/minus Unendlich, NaN und "
            "denormalisierte Zahlen (schliessen die Luecke um 0).",
            "How many bits and roughly how many decimal digits do single and double IEEE 754 precision have?",
            "Single: 32 bits, about 7 decimal digits. Double: 64 bits, about 16 decimal digits."
        ),

        # ===================== V14: Fehlerrechnung =====================
        (
            "Maschinengenauigkeit (eps)", "V14", "summary",
            "Die Maschinengenauigkeit eps = (1/2) * 2^(-M) ist der maximale relative Fehler bei "
            "korrekter Rundung (M = Mantissenbits). Ideale Arithmetik (auch IEEE 754): a op b = "
            "rd(a * b), sodass das Ergebnis um den Faktor (1 + epsilon) mit |epsilon| <= eps "
            "verfaelscht ist. Merke: Gleichheit von Maschinenzahlen nie mit x == y pruefen, "
            "sondern |x - y| <= eps.",
            "What is the machine epsilon, and why should you never test machine numbers with x == y?",
            "eps = (1/2)*2^(-M), the largest relative rounding error. Because rounding perturbs "
            "every result, equality must be tested as |x - y| <= eps, not exact =="
        ),
        (
            "Kondition und Stabilitaet", "V14", "summary",
            "Zwei verschiedene Begriffe, die man nie verwechseln darf. KONDITION ist eine "
            "Eigenschaft des PROBLEMS: wie stark wirken sich Eingabefehler auf das Ergebnis aus "
            "(relative Kondition = |x * f'(x) / f(x)|). STABILITAET ist eine Eigenschaft des "
            "ALGORITHMUS: liefert er fuer leicht gestoerte Eingaben akzeptable Resultate. "
            "Fazit: nur fuer gut konditionierte Probleme lohnt sich ein stabiler Algorithmus.",
            "What is the difference between condition and stability?",
            "Condition is a property of the PROBLEM (how input errors affect the result); "
            "stability is a property of the ALGORITHM. A good algorithm cannot rescue an "
            "ill-conditioned problem."
        ),
        (
            "Ausloeschung", "V14", "summary",
            "Ausloeschung tritt bei der Subtraktion fast gleicher Zahlen auf: stimmen zwei "
            "n-stellige Zahlen in den ersten k Stellen ueberein, gehen k signifikante Stellen "
            "verloren (und die Information darueber). Deshalb ist die Subtraktion relativ "
            "schlecht konditioniert fuer a ungefaehr gleich b. Wenn moeglich, durch Umformung "
            "vermeiden.",
            "What is cancellation (Ausloeschung), and when does it occur?",
            "Cancellation is loss of significant digits when subtracting nearly equal numbers: "
            "if they agree in the first k digits, k significant digits are lost."
        ),

        # ===================== V15: Polynominterpolation I =====================
        (
            "Interpolation - Existenz und Eindeutigkeit", "V15", "summary",
            "Gegeben n+1 Stuetzpunkte mit PAARWEISE VERSCHIEDENEN x-Werten und beliebigen "
            "y-Werten, gibt es GENAU EIN Polynom P vom Grad hoechstens n mit P(x_i) = y_i. "
            "Beweisidee: die Differenz zweier Loesungen haette n+1 Nullstellen und waere nach "
            "dem Fundamentalsatz der Algebra das Nullpolynom. Wichtig: die Stuetzstellen muessen "
            "paarweise verschieden sein.",
            "Given n+1 points with distinct x-values, how many interpolating polynomials of degree <= n exist?",
            "Exactly one. Distinct x-values and any y-values determine a unique polynomial of "
            "degree at most n."
        ),
        (
            "Lagrange-Interpolation", "V15", "summary",
            "Die Lagrange-Basispolynome sind L_i(x) = Produkt ueber j ungleich i von "
            "(x - x_j)/(x_i - x_j). Sie erfuellen L_i(x_i) = 1 und L_i(x_j) = 0 fuer j ungleich i. "
            "Interpolationsformel: P(x) = Summe y_i * L_i(x). Vorteil: die Koeffizienten sind "
            "direkt die y_i. Aufwand: Aufstellen O(n), Auswerten O(n^2).",
            "What special property do the Lagrange basis polynomials L_i have at the nodes?",
            "L_i(x_i) = 1 and L_i(x_j) = 0 for j != i. This makes the interpolant simply "
            "P(x) = sum of y_i * L_i(x), with the y_i as coefficients."
        ),
        (
            "Aitken-Neville-Algorithmus", "V15", "summary",
            "Ein Verfahren, das das Interpolationspolynom NUR AN EINER festen Stelle auswertet, "
            "ohne es explizit aufzustellen. Es baut die Loesung rekursiv aus den Loesungen fuer "
            "weniger Stuetzpunkte auf, in einem Dreiecks-Tableau, wobei jede Spalte einem Grad "
            "hoeher entspricht. Aufwand O(n^2). Nuetzlich bei wenigen Auswertungsstellen.",
            "What does the Aitken-Neville algorithm compute, and what does it NOT produce?",
            "It evaluates the interpolating polynomial at a single point via a triangular tableau. "
            "It does not produce the explicit polynomial, only the value P(x) at that point."
        ),

        # ===================== V16: Polynominterpolation II =====================
        (
            "Newton-Interpolation", "V16", "summary",
            "Darstellung mit Newton-Basispolynomen N_i(x) = Produkt (x - x_0)...(x - x_{i-1}). "
            "P(x) = a_0 + a_1(x-x_0) + a_2(x-x_0)(x-x_1) + ... Das zugehoerige Gleichungssystem "
            "hat Dreiecksform. Grosser Vorteil: kommt ein neuer Stuetzpunkt hinzu, muss man nur "
            "eine neue Diagonale anhaengen - die alten Koeffizienten bleiben (anders als bei "
            "Lagrange oder Monombasis).",
            "What is the key advantage of Newton interpolation when a new data point is added?",
            "Only one new coefficient (a new diagonal) has to be computed; the existing "
            "coefficients stay the same. Lagrange and monomial bases must be redone."
        ),
        (
            "Dividierte Differenzen", "V16", "summary",
            "Effiziente Methode zur Berechnung der Newton-Koeffizienten in einem Dreiecksschema. "
            "Rekursion (mit f_i = y_i): f[m..m+k] = (f[m+1..m+k] - f[m..m+k-1]) / (x_{m+k} - x_m). "
            "Die obere Diagonale liefert die Koeffizienten. Aufwand O(n^2), Auswerten dann mit "
            "dem Horner-Schema in O(n).",
            "How are the Newton coefficients computed efficiently, and at what cost?",
            "Via divided differences in a triangular scheme, using the recursion "
            "f[m..m+k] = (f[m+1..m+k] - f[m..m+k-1])/(x_{m+k} - x_m), at cost O(n^2)."
        ),
        (
            "Interpolationsfehler und Runge-Phaenomen", "V16", "summary",
            "Fuer y_i = f(x_i) gilt f(x) - P(x) = omega(x) * f^(n+1)(xi) / (n+1)!, wobei "
            "omega(x) = Produkt (x - x_i) und xi ein Punkt im Intervall ist. Wichtige Warnungen: "
            "Extrapolation vermeiden (omega waechst ausserhalb schnell); und das Runge-Phaenomen: "
            "mehr aequidistante Stuetzstellen fuehren NICHT unbedingt zu kleinerem Fehler - die "
            "Polynomfolge konvergiert nicht gleichmaessig.",
            "What is Runge's phenomenon in polynomial interpolation?",
            "Adding more equidistant nodes does not necessarily reduce the error; the interpolating "
            "polynomials fail to converge uniformly to f, oscillating near the interval ends."
        ),

        # ===================== V17: Splineinterpolation =====================
        (
            "Kubische Splines", "V17", "summary",
            "Ein kubischer Spline verbindet Datenpunkte durch stueckweise kubische Polynome und "
            "ist zweimal stetig differenzierbar (in C^2). Auf jedem Teilintervall gilt "
            "S(x) = alpha_i + beta_i(x-x_i) + gamma_i(x-x_i)^2 + delta_i(x-x_i)^3. Man arbeitet "
            "ueber die Momente M_i = S''(x_i). Grosser Vorteil gegenueber Polynominterpolation: "
            "bei feiner werdender Unterteilung konvergiert der Spline gleichmaessig - KEIN "
            "Runge-Phaenomen. Aufwand O(n) ueber ein Tridiagonalsystem.",
            "What continuity does a cubic spline have, and what is its advantage over polynomial interpolation?",
            "A cubic spline is twice continuously differentiable (C^2). Unlike polynomial "
            "interpolation, it converges uniformly as the mesh is refined - no Runge phenomenon."
        ),
        (
            "Spline-Randbedingungen", "V17", "summary",
            "Bei n kubischen Stuecken bleiben nach Interpolation und Glattheitsbedingungen genau "
            "2 Freiheitsgrade uebrig, daher braucht man 2 Randbedingungen. Drei Typen: "
            "(a) natuerlich: S''=0 an beiden Raendern, also M_0 = M_n = 0; (b) periodisch: "
            "gleiche erste und zweite Ableitung an den Raendern (fuer y_0 = y_n); (c) vollstaendig: "
            "vorgegebene erste Ableitungen an den Raendern.",
            "Why does a cubic spline need boundary conditions, and name the three standard types.",
            "After interpolation and smoothness there are 2 degrees of freedom left, so 2 boundary "
            "conditions are needed: natural (S''=0 at ends), periodic, and complete (given end slopes)."
        ),

        # ===================== V18: Funktionenreihen =====================
        (
            "Punktweise und gleichmaessige Konvergenz", "V18", "summary",
            "Bei punktweiser Konvergenz darf das noetige N von x abhaengen (N(x, epsilon)). "
            "Bei gleichmaessiger Konvergenz muss EIN N fuer ALLE x reichen (N haengt nicht von x "
            "ab). Gleichmaessig impliziert punktweise, aber nicht umgekehrt. Der gleichmaessige "
            "Limes stetiger Funktionen ist wieder stetig. Standardgegenbeispiel: f_n(x) = x^n auf "
            "[0,1] konvergiert nur punktweise gegen eine unstetige Grenzfunktion.",
            "What is the key difference between pointwise and uniform convergence?",
            "For pointwise, the required N may depend on x; for uniform, one N must work for ALL x. "
            "Uniform convergence preserves continuity; pointwise need not."
        ),
        (
            "Taylor-Reihe", "V18", "summary",
            "Die Taylor-Reihe einer unendlich oft differenzierbaren Funktion f am Entwicklungspunkt "
            "a ist Summe f^(n)(a)/n! * (x-a)^n. Satz von Taylor: f(x) = T_k(x) + R_{k+1}(x). "
            "Lagrange-Restglied: R_{k+1}(x) = f^(k+1)(xi)/(k+1)! * (x-a)^(k+1) fuer ein xi "
            "zwischen a und x. Die Reihe konvergiert genau dort gegen f, wo das Restglied gegen "
            "0 geht.",
            "Write the Taylor series of $f$ about $a$, and state the Lagrange form of the remainder.",
            "$T(x) = \\sum \\frac{f^{(n)}(a)}{n!}\\,(x-a)^n$. Lagrange remainder: "
            "$R = \\frac{f^{(k+1)}(\\xi)}{(k+1)!}\\,(x-a)^{k+1}$ for some $\\xi$ between $a$ and $x$."
        ),
        (
            "Fourier-Reihe", "V18", "summary",
            "Fuer eine 2*pi-periodische, integrierbare Funktion: F(x) = a_0/2 + Summe "
            "(a_k*cos(kx) + b_k*sin(kx)), mit a_k = (1/pi)*Integral f(t)cos(kt) dt und "
            "b_k = (1/pi)*Integral f(t)sin(kt) dt ueber eine Periode. Grundlage sind die "
            "Orthogonalitaetsrelationen der trigonometrischen Funktionen. An Sprungstellen "
            "unstetiger Funktionen treten Ueber- und Unterschwinger auf (Gibbs-Phaenomen).",
            "What are the Fourier coefficient formulas a_k and b_k, and what is the Gibbs phenomenon?",
            "$a_k = \\frac{1}{\\pi}\\int f(t)\\cos(kt)\\,dt$, $b_k = \\frac{1}{\\pi}\\int "
            "f(t)\\sin(kt)\\,dt$ over a period. Gibbs: over/undershoot near jump discontinuities."
        ),

        # ===================== V19: Trigonometrische Interpolation =====================
        (
            "Diskrete Fourier-Transformation (DFT)", "V19", "summary",
            "Fuer N Abtastwerte: DFT (Analyse) c_k = (1/N) * Summe f_j * omega^(-jk), und "
            "IDFT (Synthese) f_j = Summe c_k * omega^(jk), mit omega = exp(2*pi*i/N). Die "
            "Koeffizienten c_k sind im Allgemeinen komplex, auch bei reellen f_j. Achtung auf "
            "die Vorzeichen: DFT hat den negativen Exponenten UND den Faktor 1/N, die IDFT den "
            "positiven Exponenten OHNE 1/N. Beispiel N=4: omega = i.",
            "In the DFT/IDFT convention here, which transform carries the 1/N factor and the negative exponent?",
            "The DFT (analysis) carries both the factor $\\frac{1}{N}$ and the negative "
            "exponent $\\omega^{-jk}$; the IDFT (synthesis) uses the positive exponent and "
            "no $\\frac{1}{N}$."
        ),
        (
            "Schnelle Fourier-Transformation (FFT)", "V19", "summary",
            "Die FFT berechnet die DFT statt in O(N^2) in nur O(N log N). Idee (fuer N = 2M): "
            "Aufspaltung in geraden und ungeraden Teil ergibt zwei DFTs halber Laenge, verbunden "
            "durch die Butterfly-Symmetrie f_{k+M} = f_gerade - omega^k * f_ungerade. Rekursive "
            "Anwendung fuer N = 2^m ergibt O(N log N). Bit-Reversal sortiert die Indizes vorab "
            "fuer eine In-Place-Berechnung.",
            "What complexity does the FFT achieve versus the direct DFT, and via what idea?",
            "$O(N \\log N)$ instead of $O(N^2)$, by recursively splitting into even and odd "
            "parts (two half-length DFTs joined by the butterfly symmetry)."
        ),
    ]

    cur.executemany(
        "INSERT INTO knowledge (topic, source, type, content, question, answer) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        data
    )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM knowledge")
    count = cur.fetchone()[0]

    print(f"OK - database created: {DB_PATH}")
    print(f"OK - row count: {count}")
    print()
    print("Current database contents:")
    cur.execute(
        "SELECT id, source, topic FROM knowledge "
        "ORDER BY CAST(SUBSTR(source, 2) AS INTEGER), id"
    )
    for row in cur.fetchall():
        print(f"  [{row[0]:>2}] {row[1]} - {row[2]}")

    conn.close()


if __name__ == "__main__":
    build_database()
