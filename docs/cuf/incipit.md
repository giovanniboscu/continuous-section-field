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

## Conclusione

**L'idea iniziale era semplice: fare arrivare la sezione continua `S(x)` fino ai nuclei CUF.** Questo ha reso possibile una valutazione numerica dei contributi sezionali a partire dalla geometria e dai materiali effettivi, evitando di costruire integrazioni simboliche specifiche per ogni caso.

Da lì è nata l'organizzazione di CSF–CUF: geometria e materiali nel CSF, approssimazioni e calcolo nei componenti Python, e file YAML per comporre un'analisi riproducibile.

Questa pagina racconta il percorso concettuale e implementativo. La verifica della formulazione, i dettagli degli operatori e i risultati numerici richiedono documenti tecnici distinti, a partire dalla [derivazione formale per sezioni variabili](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md).
