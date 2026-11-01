# Guida operativa per agenti — Firemod 0.1.0

[README](../README.md) · [Manuale utenti](USER_GUIDE.it.md) · [Istruzioni del repository](../AGENTS.md) · [Build](BUILDING.md)

Questa guida serve a un agente che assiste un utente, analizza un problema o automatizza un intervento già autorizzato. Per modificare il progetto leggi anche `AGENTS.md`. Descrive la versione 0.1.0: verifica il checkout prima di applicarla a versioni successive.

## 1. Identificare obiettivo e contesto

Usa l’autorizzazione e le preferenze già fornite dall’utente. Non chiedere di nuovo il permesso per passi reversibili già compresi nell’incarico. Se manca una decisione che cambia le app da disattivare, il dispositivo bersaglio o un’azione esterna, chiedi solo quel dato e prosegui le verifiche indipendenti.

Prima di modificare un dispositivo, determina:

- versione del tool o commit e sistema/architettura del PC;
- eseguibile ADB e identificatore completo restituito da `adb devices -l`;
- produttore, modello, Fire OS e API Android;
- azioni richieste e app che l’utente vuole conservare;
- presenza di Luncher, Firemod Home o un helper precedente;
- cartella dati e disponibilità della cronologia per lo stesso identificatore ADB.

Non scegliere il primo dispositivo dell’elenco. ADB può vedere telefoni, emulatori o più Fire TV. Non usare un indirizzo ricordato da un’altra sessione senza ricontrollare modello e bersaglio. La presenza in ADB non equivale a compatibilità Firemod.

## 2. Preparare un ambiente riproducibile

Usa Python 3.12 x86_64, come in CI, e i comandi separati per Linux/Windows nel [README](../README.md#dal-sorgente). Le dipendenze di build sono bloccate con hash in `requirements-build.txt`. Per riprodurre una release usa il suo tag; per una correzione lavora su un branch basato sulla versione pertinente. Non spostare tag pubblicati.

Nelle sezioni seguenti `python` indica **Python del virtualenv preparato**, non necessariamente il comando globale. Su Linux puoi sostituirlo con `.venv/bin/python`; su Windows con `.\.venv\Scripts\python.exe`. L’uso del percorso diretto evita di dipendere dall’attivazione della shell.

In esecuzione normale la GUI usa un percorso ADB già salvato, se ancora valido; altrimenti chiama `find_adb()`. Il rilevamento automatico tenta nell’ordine:

1. variabile `FIREMOD_ADB`;
2. eseguibile nel `PATH`;
3. `platform-tools` delle risorse e della cartella dati Firemod;
4. `platform-tools` sotto `ANDROID_HOME` e `ANDROID_SDK_ROOT`.

La CLI di diagnosi usa direttamente `find_adb()`, senza leggere il percorso salvato nelle preferenze GUI. Imposta `FIREMOD_ADB` quando serve garantire lo stesso eseguibile. Esempi, da adattare:

```bash
export FIREMOD_ADB='/percorso/android-sdk/platform-tools/adb'
```

```powershell
$env:FIREMOD_ADB = 'C:\percorso\platform-tools\adb.exe'
```

Non scaricare eseguibili ADB da mirror casuali. Il download integrato è un’azione esplicita con termini Google e origine HTTPS `dl.google.com`; non viene effettuato dal solo avvio della diagnosi o della demo.

## 3. Interfacce reali disponibili

```text
python -m firemod.app
python -m firemod.app --demo
python -m firemod.app --screenshot build/preview.png
python -m firemod.app --diagnose "SERIALE_ADB"
python -m firemod.app --help
```

| Comando | Effetto e output |
| --- | --- |
| Nessuna opzione | Avvia la GUI; può rilevare i dispositivi via ADB, ma le modifiche richiedono il piano |
| `--demo` | Mostra dati dimostrativi e disabilita l’applicazione delle modifiche; non apre una sessione ADB verso una Fire TV |
| `--screenshot PERCORSO` | Mostra la demo, salva un PNG e chiude la GUI; crea le directory di destinazione |
| `--diagnose SERIALE_ADB` | Legge informazioni del dispositivo e stampa un oggetto JSON su stdout; richiede ADB già disponibile e una connessione autorizzata |
| `--help` | Mostra le opzioni effettive del parser |

Non esistono `--apply`, `--restore`, `--install-adb`, importazione JSON di un piano, server HTTP o API remota. Non inventare questi comandi. La GUI compilata Windows usa il sottosistema senza console: per catturare stdout diagnostico in modo affidabile usa il comando Python da sorgente.

Per screenshot su un host senza display grafico:

```bash
QT_QPA_PLATFORM=offscreen python -m firemod.app --screenshot build/preview.png
```

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
python -m firemod.app --screenshot build/preview.png
Remove-Item Env:QT_QPA_PLATFORM
```

L’offscreen non è una modalità interattiva visibile. Demo e screenshot possono creare preferenze/cartelle locali del PC, ma non modificano la Fire TV. Una demo non è un test hardware.

## 4. Diagnosi in sola lettura

Con ADB nel `PATH`:

```bash
adb devices -l
adb -s "SERIALE_ADB" get-state
python -m firemod.app --diagnose "SERIALE_ADB"
```

Sostituisci `SERIALE_ADB` con il valore completo della riga scelta, anche `IP:porta` per una connessione di rete. Usa sempre `-s` per i comandi destinati al dispositivo. Se ADB non è nel `PATH`, usa il suo percorso completo; in PowerShell un percorso quotato si esegue con `& 'C:\percorso\adb.exe' ...`.

La diagnosi stampa i campi di `DeviceInfo`: `serial`, `model`, `manufacturer`, `fire_os`, `android`, `sdk`, `available_mb`, `total_mb`, `free_storage`, `disabled_count`, `boot_id`. È un report privato: contiene seriale e identificatore del boot. La proprietà `is_fire_tv` non è un campo JSON serializzato. `--diagnose` chiama `inspect()`, non `require_fire_tv()`: può leggere anche un dispositivo non supportato e non ne certifica la compatibilità.

Per verificare il vincolo Fire TV e leggere l’elenco app da codice, senza modifiche:

```python
from firemod.adb import Adb, find_adb
from firemod.engine import Engine

adb_path = find_adb()
if not adb_path:
    raise RuntimeError("ADB non trovato: impostare FIREMOD_ADB")
engine = Engine(Adb(adb_path, "SERIALE_ADB"))  # sostituire il valore
info = engine.require_fire_tv()
packages = engine.packages()
accelerator_active = engine.bridge_status()
```

`require_fire_tv()` richiede produttore Amazon, modello `AFT…` e API >= 22. `packages()` distingue pacchetti sistema, disabilitati, nascosti e protetti e filtra quelli non installati per l’utente 0. Il motore lavora sull’**utente Android 0**, non offre selezione multiutente Android. `bridge_status()` controlla marker del boot e processo Firemod: non riconosce come attivo un acceleratore di un’altra namespace.

Se la connessione è `unauthorized`, l’utente deve accettarla sulla TV. Se è `offline`, ripristina la connessione prima di qualsiasi scrittura. Non presentare `adb kill-server` come prima azione innocua: interrompe anche altre sessioni ADB del PC. Un reboot della Fire TV termina l’acceleratore corrente.

## 5. Preparare un piano senza applicarlo

Il modello Python è `firemod.models.Plan`:

| Campo | Valore / significato |
| --- | --- |
| `animations` | `None` per non intervenire, oppure stringa `"0"`, `"0.5"`, `"1"` |
| `privacy` | Booleano: applica le chiavi privacy previste dal motore |
| `screensaver` | Booleano: disabilita le impostazioni screensaver previste |
| `launcher` | Booleano: installa Luncher se assente e Firemod Home; API 22 |
| `accelerator` | Booleano: avvia il bridge della Home; API 22, companion necessario |
| `packages` | Lista di identificatori espliciti delle app da disattivare |
| `enable_packages` | Lista esplicita delle app da riattivare |

Esempio di sola preparazione, senza comandi sul dispositivo:

```python
from dataclasses import asdict
import json
from firemod.models import Plan

plan = Plan(animations="0.5")  # nessuna selezione automatica di app
print(json.dumps(asdict(plan), indent=2))
```

Non usare la lista delle app installate come lista da rimuovere. Confronta le richieste dell’utente con `Package.protected`, `catalog.ALWAYS_KEEP` e `catalog.OPTIONAL_SYSTEM`; considera le dipendenze funzionali, ad esempio Alexa e comandi vocali. Le liste di disattivazione e riattivazione non possono contenere lo stesso pacchetto. Un piano vuoto o con una scala animazioni diversa da quelle previste è rifiutato.

Presenta il bersaglio, le azioni e i limiti nel risultato da rivedere. Nella GUI usa **Rivedi le modifiche**: il dialogo elenca l’intero piano. Le righe nascoste da un filtro possono restare selezionate. Il profilo consigliato mantiene le selezioni già fatte per app e screensaver; non equivale a un piano pulito.

## 6. Eseguire soltanto l’intervento autorizzato

La GUI è il percorso ordinario. Per un’automazione già autorizzata, l’API interna della versione 0.1.0 espone le seguenti chiamate; **queste modificano il dispositivo**, a differenza degli esempi di preparazione:

```python
outcome = engine.apply(plan)
```

Il frammento presuppone l’`engine` verificato e il `plan` esplicito delle sezioni precedenti. L’API Python è interna e non è un contratto di compatibilità fra versioni. Non chiamare i metodi privati `_disable`, `_install` o `_setting` per saltare validazione e cronologia. Non eseguire due motori contemporaneamente sullo stesso dispositivo: non esiste un lock globale fra processi. Non cambiare bersaglio nel mezzo del piano.

`apply()` verifica il dispositivo, valida le app e crea il journal prima delle operazioni. Restituisce `Outcome` con `done`, `skipped`, `errors`, `snapshot`. Un’eccezione o `errors` non significa che nulla sia cambiato. Le operazioni sono sequenziali, con scrittura dell’undo prima delle mutazioni registrate; non esiste una transazione unica con rollback automatico.

Il motore non dispone di un dry-run ADB generico. Preparare un `Plan` non chiama `apply()`. Ripetere `apply()` non è un test innocuo: alcune impostazioni sono idempotenti, ma il companion può essere reinstallato e vengono creati nuovi punti.

### Verificare il risultato

- Leggi tutte le liste dell’`Outcome` e gli eventuali errori, non soltanto il codice di uscita del processo.
- Controlla il valore restituito da `settings` e gli stati pacchetto tramite il motore. Un valore privacy presente nel database prova la scrittura, non l’effetto di ogni servizio.
- Per Home controlla `bridge_status()`, poi verifica sull’hardware il tasto Home, l’apertura di un’app e l’accesso alle impostazioni. Un marker non è una misura della latenza percepita.
- Distingui misure reali, dati demo, test simulati e prove CI desktop. Il benchmark originale di un AFTT non si estende automaticamente ad altri firmware.
- Riporta gli interventi riusciti, rifiutati e falliti e dove si trova privatamente il punto di ripristino. Non pubblicare quel percorso se contiene informazioni personali.

## 7. Journal e ripristino

Cartella dati: `data_dir()` in `paths.py`; directory dispositivo: primi 20 caratteri esadecimali di SHA-256 del **seriale ADB**. Struttura:

```text
Firemod/
  devices/
    <hash-seriale>/
      <timestamp-UTC>-<id>/
        snapshot.json
        <pacchetto>.apk   # solo se è stato necessario un backup
```

Schema journal `1`: `firemod`, `created`, `device` (seriale, modello, Fire OS), `operations`, `finished`; al termine di un apply compare `summary`. Le operazioni possono essere `setting`, `package`, `install`, `permission`, `legacy_helper`, `bridge`, con stati `pending`, `applied`, `failed`, `refused`, `restored` secondo l’esito. `finished: true` significa che il piano ha terminato i tentativi, non che ogni operazione è riuscita. La sostituzione del JSON è atomica; non descriverla come backup dell’intero disco o garanzia contro ogni perdita di alimentazione del PC.

La GUI di ripristino elenca i punti dello stesso identificatore. Per automazione autorizzata, dal medesimo `Engine`:

```python
from pathlib import Path
restored = engine.restore(Path(outcome.snapshot))
```

Questo annulla il punto dell’esempio, non tutti gli interventi mai fatti. Per un punto precedente usa un percorso verificato ottenuto da `engine.snapshots()`, non un JSON ricevuto da una fonte non fidata. Il motore controlla directory, schema e seriale; non correggere a mano il seriale per superare quel vincolo.

Il ripristino percorre le operazioni in ordine inverso, salta quelle già ripristinate o rifiutate e conserva gli errori. Le chiavi originariamente assenti vengono eliminate. Per i pacchetti verifica visibilità e comportamento abilitato/disabilitato; API 22 può ripristinare uno stato predefinito tramite `enable`, non il valore numerico originale `0`. Ripristinare una vecchia impostazione può sovrascrivere cambiamenti successivi allo stesso valore. Per annullare più piani, usa l’ordine dal più recente al più vecchio.

Un cambio fra USB e Wi-Fi, IP o porta cambia l’identificatore e quindi la cronologia. Non è implementata una migrazione automatica verso l’identità fisica della TV. Conserva l’intera cartella dati, inclusi gli APK originali, e non forzare una corrispondenza fra dispositivi.

## 8. Confini dell’integrazione Home

| Elemento | Valore nella versione 0.1.0 |
| --- | --- |
| Luncher | `com.luncher.launcher` |
| Companion | `org.firemod.home` |
| Helper precedente riconosciuto | `it.massi.firehome` |
| JAR e PID del bridge | `/data/local/tmp/firemod/bridge.jar`, `bridge.pid` nella stessa directory |
| Log del bridge | `/data/local/tmp/firemod/bridge.log` |
| Directory delle richieste | `/sdcard/Android/data/org.firemod.home/files` |
| File del protocollo | `home-bridge-ready`, `home-request`, `home-response` |

Il companion usa `READ_LOGS` per osservare gli avvii Home; non ha permesso Internet. Il processo shell avviato da ADB usa FileObserver, accetta solo un identificatore numerico e invoca una destinazione Luncher fissa. Non è una shell remota, non apre porte di rete e non è un servizio root. Il marker contiene il boot ID; una risposta mancante entro circa 1,2 secondi provoca il fallback del companion. Il processo può terminare per reboot, perdita di alimentazione o intervento del sistema; riattivalo dal tool senza reinstallare indiscriminatamente gli APK.

Amazon Home rimane il target nativo e non viene disabilitata o rinominata. La priorità del sistema non viene invertita. Non promettere persistenza dei privilegi shell dopo il reboot o avvio completo in 0,1 secondi. Il codice che tratta le attività profilo automatiche è limitato ai primi 120 secondi dal boot; non va esteso a ogni cambio profilo senza prove.

## 9. Dati e consegna del lavoro

Non mettere in Git o nelle issue seriali, IP personali, boot ID, dump completi, snapshot, APK di backup, chiavi ADB, keystore, password o token GitHub. I dati dimostrativi e gli identificatori fittizi sono adatti agli esempi. L’hash della cartella dispositivo non anonimizza il seriale dentro `snapshot.json`.

Per una consegna utile indica: versione/commit, dispositivo descritto senza identificatori personali, piano autorizzato, esiti reali, test eseguiti, limiti rimasti e istruzioni per riattivazione/ripristino. Per una modifica al codice usa il percorso di [contribuzione](../CONTRIBUTING.md), preserva le licenze e non pubblicare o taggare senza che rientri nell’incarico dell’utente.

## 10. Riferimento delle impostazioni

Questa tabella descrive le scritture di `Engine.apply()` in 0.1.0; è un riferimento per verificare il piano, non una richiesta di eseguire comandi manuali che saltano il journal. Tutti i valori sono passati come stringhe.

| Opzione | Namespace `settings` | Chiave | Valore richiesto |
| --- | --- | --- | --- |
| Animazioni | `global` | `window_animation_scale` | `0`, `0.5` o `1` |
| Animazioni | `global` | `transition_animation_scale` | come sopra |
| Animazioni | `global` | `animator_duration_scale` | come sopra |
| Privacy | `secure` | `USAGE_METRICS_UPLOAD_ENABLED` | `0` |
| Privacy | `secure` | `usage_metrics_marketing_enabled` | `0` |
| Privacy | `secure` | `limit_ad_tracking` | `1` |
| Privacy | `secure` | `settingsApp:deviceUsageData:value` | `0` |
| Privacy | `secure` | `settingsApp:appUsageData:value` | `0` |
| Screensaver | `secure` | `screensaver_enabled` | `0` |
| Screensaver | `secure` | `screensaver_activate_on_sleep` | `0` |
| Screensaver | `secure` | `screensaver_activate_on_dock` | `0` |

Il motore legge prima il valore e non lo riscrive se è già quello richiesto. Una chiave assente è rappresentata con `None` e ripristinata con `settings delete`. La presenza di una chiave non prova che un altro firmware implementi quella funzione; non aggiungere chiavi ipotetiche alla lista per far apparire un’opzione supportata.

Ordine di un piano: validazione, creazione journal, animazioni, privacy, screensaver, disattivazioni, riattivazioni, installazione Home, acceleratore, riepilogo finale. La validazione delle app avviene prima delle prime modifiche; errori operativi possono comunque lasciare un piano parzialmente applicato. Il catalogo e il motore, non questa tabella, restano la fonte da controllare quando cambia la versione.
