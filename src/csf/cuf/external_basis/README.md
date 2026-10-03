# CSF-CUF: base trasversale esterna - v1

Versione: 2026-09-29.

Questa estensione riguarda soltanto la chiave **`cuf.basis`** del caso YAML.
Aggiunge un'alternativa ai nomi interni: il percorso di un file Python esterno.
Non modifica le basi interne, il solver, il longitudinale, i materiali,
l'equilibration, bond o blender. La gestione di `cuf.segments` resta invariata.

## Configurazione

La configurazione interna resta identica:

```yaml
cuf:
  basis: scaled_maclaurin
  order: 8
```

Per una base esterna:

```yaml
cuf:
  basis: ./my_expansions/custom_basis.py
  order: 8
```

`order` e l'eventuale `basis_options` passano attraverso lo stesso
`CUFBasisPlugin.build()` usato dalle basi interne. Non vengono reinterpretati
o sostituiti dal caricatore.

Il file `custom_scaled_maclaurin.py` in questa cartella costituisce un esempio
pronto: usa la stessa base numerica e gli stessi requisiti di quadratura della
versione interna. Non introduce una nuova approssimazione matematica.
Copiandolo accanto a un caso YAML esistente, basta cambiare quella sola chiave:

```yaml
cuf:
  basis: ./custom_scaled_maclaurin.py
  order: 8
```

Il resto del caso YAML non cambia. Non viene fornito un nuovo problema
strutturale: carichi, geometria e vincoli rimangono quelli del caso scelto.

## Regole dei percorsi

I percorsi relativi in `cuf.basis` sono riferiti alla cartella del **file YAML
del caso**, non alla directory dalla quale viene eseguito `csf-cuf`.

Sono accettati percorsi assoluti, `./...`, `../...` e percorsi con `~`.
Un nome come `custom_basis.py` viene riconosciuto come file anche senza `./`.
La forma `./custom_basis` funziona anche senza suffisso: il contenuto deve
comunque essere codice sorgente Python. Un nome senza suffisso e senza
separatore, come `scaled_maclaurin`, rimane invece un nome del registro.
Maiuscole e minuscole del percorso vengono conservate; valgono le regole
del filesystem del sistema operativo utilizzato.

Il parser YAML risolve il percorso, ma **non esegue** il modulo. Il caricamento
avviene quando viene richiesto il plugin. Un file assente genera un errore:
non viene scelta una base interna al suo posto.

Per chiamate Python dirette, `get_cuf_basis_plugin()` accetta anche `Path`.
Un percorso relativo passato direttamente a questa funzione, senza passare
da `load_case()`, viene interpretato rispetto alla directory corrente.

## Contratto del modulo esterno

Si usa la stessa registrazione dei moduli in `csf.cuf.expansions`:

```python
from csf.cuf.core.basis_plugins import CUFBasisPlugin, register_cuf_basis_plugin

register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="my_basis",
        builder=my_builder,
        section_gauss_minimum=my_section_gauss_minimum,
        longitudinal_transverse_degree=my_transverse_x_degree,
    )
)
```

Il modulo deve registrare **un solo plugin** durante l'importazione. Questa
regola rende univoca la selezione tramite il solo percorso: zero o piu' plugin
producono un errore che mostra i nomi trovati, senza sceglierne uno arbitrariamente.
Non viene introdotto un nuovo nome obbligatorio per una factory o una classe.

La firma del builder rimane:

```python
def my_builder(*, order, section_provider, continuous_section_field, options):
    ...
```

L'oggetto restituito deve rispettare il contratto trasversale gia' richiesto
dal solver: dimensione della base, valori e derivate. Gli eventuali metodi
opzionali, compresa la dipendenza esplicita da `x`, non vengono modificati.
Il caricatore non assume che la base sia Maclaurin, Legendre o Lagrange.

I due callback di quadratura restano quelli dichiarati dal plugin; il loro
significato e i controlli gia' presenti in `CUFBasisPlugin` sono invariati.
Questa estensione non dimostra la correttezza matematica di un plugin esterno
e non inventa i suoi requisiti di integrazione.

## Isolamento e importazione

La registrazione di un file esterno viene raccolta separatamente dal registro
interno. Il plugin esterno puo' quindi chiamarsi `scaled_maclaurin` senza
sostituire quello interno, anche se usa `replace=True`. Due file con lo stesso
nome in cartelle diverse restano distinti. I plugin esterni si selezionano
tramite il loro percorso; non diventano nuovi alias globali del registro.

Ogni percorso risolto viene caricato una sola volta per processo. Il plugin
rimane in cache, mentre il builder puo' essere richiamato con ordini e contesti
diversi. Dopo una modifica a un modulo gia' caricato, riavviare il processo
Python; non e' implementato un meccanismo di hot reload.

Il modulo viene inserito in `sys.modules` prima dell'esecuzione, quindi puo'
usare normalmente `dataclass` e introspezione del modulo. Un'importazione
fallita rimuove la propria voce incompleta e ripristina il contesto di
registrazione. Gli errori di importazione conservano la causa originale.

Il caricatore non modifica `sys.path` e non trasforma un file in un pacchetto:
per dipendenze ausiliarie usare moduli o pacchetti normalmente importabili
nell'ambiente. I file esterni vengono eseguiti come codice Python ordinario:
**usare soltanto codice attendibile**. L'isolamento del registro non e' una
sandbox di sicurezza.

## File dell'intervento

File esistenti modificati:

- `src/csf/cuf/case.py`: risoluzione del solo `cuf.basis` top-level.
- `src/csf/cuf/core/basis_plugins.py`: selezione nome/percorso e destinazione
  della registrazione durante un'importazione esterna.

File aggiunti:

- `src/csf/cuf/core/external_basis.py`: caricatore e risoluzione dei percorsi.
- `tests/test_cuf_external_basis.py`: test mirati.
- `cuf/examples/external_basis/custom_scaled_maclaurin.py`: esempio esterno.
- Questo documento.

`CUFBasisPlugin.build()`, i suoi due metodi di quadratura, la discovery interna
e le classi di configurazione restano identici. Non cambiano `engine.py`,
`numerics.py`, `basis.py` o i moduli delle espansioni longitudinali.

## Verifiche

Dalla radice del repository, nell'ambiente Python del progetto con `pytest`:

```bash
python -m pytest -q tests/test_cuf_external_basis.py
```

Nell'ambiente di preparazione sono passati **48 test mirati**, eseguiti su
una copia isolata dei moduli coinvolti. Coprono parser YAML, caricamento,
passaggio del contesto e delle opzioni, callback, omonimie, cache, importazioni
annidate e concorrenti, errori e compatibilita' del percorso interno.
La discovery delle basi concrete viene isolata con una fixture: questi test
**non costituiscono una riesecuzione dell'intera suite del repository o dei
benchmark strutturali CSF-CUF**.

Anche la sintassi Python e l'applicazione della patch su una copia dei file
base sono state verificate. Il confronto AST conferma che, fra le definizioni
esistenti, cambiano solo `load_case`, `register_cuf_basis_plugin` e
`get_cuf_basis_plugin`.

L'esportazione `.cuf.npz` non viene estesa: restano i requisiti del compilatore
esistente. Il caricamento di una base esterna non garantisce, da solo, che
una nuova famiglia sia esportabile nel formato di checkpoint.

## Riferimenti dei file base

Intervento preparato sui sorgenti `main` consultati il 29 settembre 2026:

- `case.py`: header `normalized longitudinal partition v25 - 2026-09-21`.
- `basis_plugins.py`: header `ContinuousSectionField context v25.1 - 2026-08-30`.

Sorgenti consultati:

- https://github.com/giovanniboscu/continuous-section-field
- https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/src/csf/cuf/case.py
- https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/src/csf/cuf/core/basis_plugins.py
- https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/src/csf/cuf/expansions/scaled_maclaurin.py
- https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/src/csf/cuf/solver/compiled_field.py
