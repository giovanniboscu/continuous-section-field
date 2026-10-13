# CSF–CUF: dall'idea della sezione continua a un framework generale

## Origine del progetto

Il punto di partenza è stato un problema di implementazione: come costruire un software CUF sufficientemente generale da trattare geometrie e materiali differenti, anche variabili lungo l'asse, senza dover sviluppare una formulazione specifica per ogni nuovo caso?

La scelta che ha orientato il lavoro è stata **mantenere la sezione come oggetto continuo lungo l'asse della trave e portarne la dipendenza longitudinale fino ai nuclei CUF**. In altre parole, considerare esplicitamente una sezione `S(x)` e le proprietà costitutive associate alla posizione `x`, anziché fissarle preliminarmente in una descrizione sezionale specializzata.

L'obiettivo non era modificare i principi della formulazione CUF, ma trovare un'organizzazione matematica e computazionale che ne consentisse un'implementazione riutilizzabile.

## 1. La scelta fondamentale: conservare S(x) fino ai nuclei

Nella rappresentazione CUF, il campo di spostamento è approssimato mediante funzioni trasversali e funzioni di forma longitudinali. I contributi alla rigidezza dipendono inoltre dalla geometria e dalle proprietà del materiale.

L'idea è stata mantenere esplicita la dipendenza della sezione dalla coordinata longitudinale anche nel momento in cui vengono valutati i contributi sezionali dei nuclei CUF. In forma schematica, un contributo può essere rappresentato come

```math
\mathcal{K}(x) = \int_{S(x)} \mathcal{B}^{T}(x,y,z)\,\mathbf{C}(x,y,z)\,\mathcal{B}(x,y,z)\,\mathrm{d}S.
```

Questa espressione ha un significato illustrativo: la definizione completa degli operatori, degli indici e dei nuclei adottati va ricercata nella trattazione matematica specifica, non dedotta da questa sintesi.

**Conservare `S(x)` fino a questo livello è stata la decisione determinante.** La geometria e la distribuzione dei materiali restano informazioni valutabili nel punto e nella sezione richiesti dal procedimento numerico.

La derivazione formale è presentata nel documento:

**[Estensione formale CSF–CUF alle sezioni variabili](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md)**.

## 2. La conseguenza immediata: valutare numericamente i contributi sezionali

Da questa impostazione è derivata una conseguenza operativa importante: **non è più necessario ricavare e integrare simbolicamente, caso per caso, le espressioni dipendenti dalla geometria e dai materiali**.

La descrizione fisica della sezione viene interrogata durante la valutazione numerica dei contributi richiesti dalla formulazione. La complessità della geometria e della sua variazione longitudinale viene così gestita dal modello sezionale, mentre il procedimento di costruzione dei nuclei conserva un'organizzazione generale.

Questo passaggio non equivale a eliminare ogni operazione simbolica: riguarda specificamente il trattamento delle quantità geometriche e costitutive nelle integrazioni sezionali.

## 3. Il passo successivo: mantenere le approssimazioni in Python

Una volta separata la geometria dalla valutazione dei nuclei, il passo successivo è stato organizzare le **espansioni trasversali** e le **funzioni di forma longitudinali** come componenti matematici implementati in Python.

Le rispettive espressioni e derivate rimangono definite attraverso i componenti dedicati, mentre geometria e materiali sono forniti autonomamente dal CSF. Le famiglie già implementate possono essere selezionate e riutilizzate; una nuova famiglia richiede lo sviluppo di un componente Python conforme all'interfaccia prevista.

Questa separazione consente di combinare scelte di approssimazione differenti con lo stesso modello fisico, senza riscrivere ogni volta il procedimento generale di assemblaggio.

## 4. La costruzione di CSF–CUF

L'architettura risultante distingue tre responsabilità:

| Componente | Responsabilità |
| --- | --- |
| **CSF** | Descrizione della geometria sezionale e dei materiali, comprese le variazioni lungo l'asse. |
| **Componenti Python di CUF** | Espansioni trasversali, funzioni di forma longitudinali, operatori, valutazione numerica e assemblaggio. |
| **Configurazione YAML** | Collegamento fra modello, problema e scelte di analisi tramite file testuali leggibili e modificabili. |

I file YAML permettono di dichiarare il modello fisico, i carichi e i vincoli, le approssimazioni selezionate e i parametri numerici dell'analisi. Non sono la formulazione matematica: sono lo strumento attraverso il quale si configurano e si combinano i componenti disponibili.

Documentazione di riferimento:

- [Presentazione CSF–CUF per Carrera](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/cuf/CSF_CUF_Continuous_Section_Field_Carrera.md)
- [Riferimento alla configurazione YAML](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/yaml_reference/readme.md)
- [Documentazione del framework CUF](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/readme.md)

## 5. Il principio architetturale

Il principio che ha guidato l'implementazione è **mantenere il nucleo generale CUF indipendente dai dettagli di una specifica geometria, distribuzione dei materiali, famiglia di approssimazioni o condizione di carico**.

Questi elementi vengono forniti attraverso componenti e interfacce dedicate. Il riuso diventa quindi una proprietà dell'architettura: un nuovo caso può essere costruito ricombinando elementi esistenti, mentre le estensioni necessarie vengono sviluppate nei componenti appropriati.

L'aspirazione alla generalità non implica che ogni possibile modello sia già disponibile. Il perimetro operativo dipende dalle famiglie di espansione, dai carichi, dai vincoli e dalle funzionalità effettivamente implementati e verificati.

## 6. Dal principio generale a un caso riproducibile: la sezione a C asimmetrica

**L'idea iniziale era semplice: portare la sezione continua `S(x)` fino ai nuclei CUF.** Il passo successivo è mostrare come questa scelta si traduca in un'analisi effettiva, seguendo senza salti la descrizione fisica, l'espansione trasversale, la configurazione CUF e il problema strutturale.

Il caso scelto è la **sezione a C asimmetrica** del riferimento Carrera–Petrolo, descritta nella [pagina introduttiva del caso](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/readme.md). La sua utilità, qui, è mostrare il collegamento tra oggetti separati dell'architettura, non proporre una nuova formulazione per questa geometria.

### 6.1 Il modello fisico CSF: perché nove rettangoli

Il [modello CSF 9L9](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/models/c_section_chapter9_5_3_9L9_csf.yaml) descrive una sezione prismatica a C asimmetrica con altezza `1000 mm`, spessore `100 mm`, ala superiore `1000 mm`, ala inferiore `500 mm` e lunghezza `20000 mm`. Il materiale è isotropo, con `E = 75000 MPa` e `ν = 0.33`.

La sezione è composta da **nove quadrilateri non sovrapposti**: cinque nell'ala superiore (incluso il raccordo con l'anima), uno nell'anima e tre nell'ala inferiore (incluso il raccordo). Non è una necessità intrinseca della rappresentazione CSF: questa suddivisione riproduce la topologia dei **nove domini trasversali L9** illustrati nella figura 13(b) del riferimento. Ciascun poligono CSF corrisponde così a un dominio dell'espansione L9.

Una distinzione essenziale per la riproducibilità: le coordinate interne delle partizioni delle ali sono **ricostruite dalla figura mediante suddivisioni uguali**, non riportate come quote esplicite nella pubblicazione. Nel file sono indicate le suddivisioni da `225 mm` per la parte libera dell'ala superiore e da `200 mm` per quella dell'ala inferiore. Le sezioni `S0` e `S1` hanno gli stessi poligoni e vertici: il modello considerato è prismatico, pur essendo descritto dall'interfaccia generale `S(x)`.

### 6.2 L'espansione trasversale L9 in Python

L'[implementazione `lagrangeL9_v4.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/expansions/lagrangeL9_v4.py) definisce un'espansione Lagrange quadratica a nove nodi per dominio. I poligoni CSF forniscono i domini fisici; la mappatura isoparametrica collega ogni quadrilatero alle coordinate naturali, mentre i nodi condivisi assicurano la connettività tra domini adiacenti.

È importante distinguere **nove domini** da **nove funzioni globali**: ciascun dominio possiede nove funzioni locali, mentre l'assemblaggio dei punti comuni determina l'insieme delle funzioni globali sulla sezione. L'implementazione comprende la valutazione delle funzioni e delle derivate e interroga la sezione CSF alla coordinata longitudinale richiesta. Il file Python costituisce quindi il componente di approssimazione, distinto dalla definizione fisica della geometria.

### 6.3 Il caso CUF: come si combinano i componenti

Il file [**`c_section_table_9_13_lagrangeL9_E10.yaml`**](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/cases/c_section_table_9_13_lagrangeL9_E10.yaml) mette in relazione il problema strutturale, il plugin L9 e le scelte numeriche. In particolare:

- `problem.yaml` richiama il problema esterno con carichi e vincoli, che a sua volta utilizza il modello CSF;
- `cuf.basis` seleziona il file Python L9; `basis_options` specifica domini da poligoni CSF, mappatura isoparametrica e nodi condivisi;
- `longitudinal` definisce dieci intervalli mediante undici confini normalizzati, funzioni Lagrange di ordine 12 e integrazione di Gauss di ordine 15;
- `section_integration` prescrive l'integrazione sezionale `fixed_gauss_polygon` con ordine 9;
- `solver`, `sampling` e `output` configurano rispettivamente calcolo, campionamento e risultati.

**Nota di lettura del sorgente:** il commento iniziale del file del caso cita ancora una versione preliminare `v1` che non completava la soluzione; la configurazione effettiva punta invece a `lagrangeL9_v4.py`. Per descrivere le funzionalità correnti occorre quindi riferirsi al plugin effettivamente richiamato, non a quel commento storico.

### 6.4 Il modello FEM3D di riferimento: stessa sezione fisica, diversa discretizzazione

Il confronto tridimensionale è costruito con **OpenSeesPy**, mediante elementi solidi esaedrici lineari a otto nodi (`stdBrick`, H8), tre gradi di libertà traslazionali per nodo e materiale elastico isotropo (`ElasticIsotropic`). Il riferimento implementativo è il driver [**`run_c_section_table_9_13_fem3d.py`**](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/fem3d/run_c_section_table_9_13_fem3d.py); lo script [**`fem3dbaseline.sh`**](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/fem3dbaseline.sh) costituisce il punto di lancio della baseline.

**Per comodità, il FEM3D utilizza il modello CSF con un unico poligono a otto vertici**, anziché i nove quadrilateri usati per l'espansione L9. Le due descrizioni rappresentano la **stessa sezione fisica a C**, con lo stesso contorno esterno, le stesse dimensioni e le stesse proprietà del materiale. La partizione 9L9 è una scelta di rappresentazione necessaria all'approssimazione trasversale adottata in quel caso CUF; non costituisce una geometria fisica differente. Il driver FEM3D verifica esplicitamente la topologia del poligono unico.

La mesh solida viene costruita su **tre bande conformi** (ala inferiore, anima, ala superiore), con nodi condivisi alle interfacce. Questo schema di meshing non va confuso né con l'unico poligono di input CSF né con i nove domini L9. Le suddivisioni predefinite del driver sono: `nx=80` lungo la trave; `ny_top_free=18`, `ny_bottom_free=8`, `ny_web=2` nelle rispettive regioni trasversali; `nz_flange=2` e `nz_web=16` nelle direzioni trasversali rimanenti. Questi sono parametri di discretizzazione, modificabili dalla riga di comando; il numero effettivo di elementi va ricavato dall'esecuzione, anche perché la griglia può essere adattata alla posizione del carico.

**Coerenza del problema fisico.** Il driver legge la geometria e i materiali attraverso il lettore CSF, mentre il carico e il vincolo provengono dal medesimo problema CUF, attraverso i suoi adapter. L'incastro della sezione iniziale viene tradotto in `ux=uy=uz=0` per tutti i nodi FEM di quella sezione. La forza concentrata globale lungo `z` viene applicata a un nodo FEM coincidente esattamente con le coordinate richieste: il codice inserisce, se necessario, coordinate di griglia per consentire tale coincidenza e rifiuta una corrispondenza ambigua. Il materiale viene valutato dal CSF alla stazione centrale longitudinale di ciascun elemento; il driver controlla inoltre la compatibilità isotropa `G = E/[2(1+nu)]`.

Le coordinate sono espresse negli assi fisici CUF/FEM3D: `x` longitudinale, `y` e `z` nel piano sezionale. Il campo CSF usa invece la propria stazione longitudinale `z` e coordinate locali sezionali `Pt.x`, `Pt.y`; il driver applica esplicitamente questa corrispondenza. Le unità sono **mm, N, MPa**, senza conversioni.

La soluzione è un'**analisi statica lineare** OpenSees; il sistema lineare viene affrontato con `UmfPack`, con un tentativo alternativo `SparseGeneral -piv` se necessario. Il file `.npz` prodotto conserva nodi, connettività, spostamenti, dati del materiale, posizione del carico, nodi vincolati e metadati necessari ai confronti successivi. L'opzione `--mesh-only` permette di produrre i dati della discretizzazione senza eseguire il solver.

Questa costruzione rende verificabile l'equivalenza di **geometria, materiale, carico e vincoli** fra i due modelli. Non implica identità delle approssimazioni numeriche: CUF e FEM3D conservano discretizzazioni differenti, e proprio questa differenza è oggetto del confronto dei risultati.

### 6.5 Il percorso che verrà approfondito

La trattazione dettagliata del caso seguirà questa sequenza: **geometria e materiali CSF → partizione 9L9 → definizione matematica e implementazione dell'espansione → carichi e vincoli nel problema → parametri del case → integrazione e assemblaggio CUF → costruzione della baseline OpenSees H8 → confronto degli spostamenti e delle tensioni**.

Per ogni passaggio saranno indicati i file sorgente e il significato dei parametri, distinguendo le informazioni direttamente documentate dalle scelte ricostruite o adottate per la riproduzione numerica. Il [documento sull'estensione formale alle sezioni variabili](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md) resta il riferimento matematico per la dipendenza generale da `S(x)`.

### 6.6 Riferimento bibliografico del caso

Il riferimento della sezione a C asimmetrica è il lavoro di **Erasmo Carrera e Marco Petrolo, _Refined beam elements with only displacement variables and plate/shell capabilities_**, in particolare la **sezione 4.3, “Open cross-sections”**, le **figure 12 e 13** e le **tabelle 13 e 14**. La figura 12 definisce la sezione a C; la figura 13(b) mostra la partizione in nove domini L9. Le tabelle 13 e 14 riportano spostamenti e tensioni per i rapporti `L/h = 20` e `L/h = 10` nella configurazione flesso-torsionale. Il confronto del presente caso va interpretato rispetto alla specifica configurazione di carico e ai punti di valutazione dichiarati, senza confondere i risultati pubblicati con quelli prodotti dall'implementazione CSF–CUF e dalla baseline OpenSees.

### 7. Limiti attualmente dichiarati

È importante distinguere il **perimetro delle funzionalità oggi disponibili** dai limiti della **formulazione CUF** e dall'architettura del suo nucleo di calcolo.

Nell'implementazione CSF attualmente considerata, la descrizione geometrica riguarda **sezioni poligonali rigate lungo un asse rettilineo**. La geometria della sezione può variare con la coordinata longitudinale; le proprietà elastiche possono essere specificate **per poligono**, con dipendenza longitudinale `E(x)` e `G(x)`, secondo le funzionalità previste dal modello. Questo è il perimetro dichiarato della rappresentazione fisica disponibile, non un vincolo introdotto nel nucleo generale CUF.

Il **core CUF** è progettato per ricevere dall'esterno le informazioni geometriche e costitutive necessarie alla valutazione dei nuclei, insieme alle espansioni e alle funzioni di forma. La sua separazione dai dettagli di una particolare sezione è una scelta architetturale; non equivale, da sola, a dichiarare già implementate e verificate geometrie, leggi costitutive o tipologie di problema ulteriori.

Analogamente, il campo di applicazione effettivamente utilizzabile dipende dalle **espansioni trasversali**, dalle **funzioni di forma longitudinali**, dai **carichi**, dai **vincoli** e dai **procedimenti numerici** disponibili e verificati. Una scelta non ancora supportata richiede l'estensione del componente corrispondente e la sua verifica.

Il caso della sezione a C qui presentato è una **verifica specifica**, con geometria prismatica, materiale isotropo e confronto statico lineare con elementi solidi OpenSees. I risultati di questo caso non costituiscono, da soli, una validazione di tutte le possibili variazioni geometriche e materiali contemplate dall'architettura.

In sintesi, **la generalità perseguita riguarda la struttura della formulazione e la separazione dei componenti; le capacità operative dichiarate riguardano soltanto quanto è oggi implementato e verificato**.
