# Firemod

**Una Fire TV più leggera, con la possibilità di tornare indietro.**

Un tool grafico open source per **Linux e Windows**: collega una Fire TV, scegli quali app tenere attive e applica ottimizzazioni alla reattività, alla home e alla privacy. Prima delle modifiche, Firemod salva un punto di ripristino sul PC.

[Download](https://github.com/Macer94/Firemod/releases) · [English](README.en.md) · [Compatibilità](docs/COMPATIBILITY.md) · [Compilazione](docs/BUILDING.md)

![Interfaccia di Firemod con dati dimostrativi](docs/firemod-preview.png)

## Funzioni

- **Applicazioni:** disattiva o riattiva le app opzionali selezionate, conservando dati e accessi.
- **Animazioni:** riduci la durata o elimina le animazioni dell’interfaccia.
- **Privacy:** limita le statistiche d’uso e il tracciamento pubblicitario tramite le impostazioni supportate.
- **Screensaver:** disattiva lo screensaver fotografico, se non ti serve.
- **Home essenziale:** su **Fire OS 5 / API 22**, installa [Luncher](https://github.com/CVasilakis/luncher), offline e senza inserzioni nella home, con il companion Firemod Home.
- **Acceleratore Home:** riduce l’attesa del passaggio a Luncher, per l’accensione corrente del dispositivo.
- **Ripristino:** recupera impostazioni e stati delle app dai punti salvati per quel dispositivo.

Firemod conserva i componenti essenziali e la home Amazon, utile per impostazioni e ripristino. Se il firmware rifiuta un’operazione, il tool la segnala come **non applicata**. Non esegue root, modifiche hardware, aggiornamenti del firmware o reset di fabbrica.

La gestione app usa disattivazione e occultamento: **non cancella le app in massa e non libera lo spazio occupato dai loro APK**. Le pubblicità interne a YouTube, Prime Video e altre app rimangono gestite dalle rispettive app.

## Versioni compilate

I pacchetti della sezione **Releases** sono:

- Linux x86_64: `Firemod-0.1.0-linux-x86_64.tar.gz`
- Windows x86_64: `Firemod-0.1.0-windows-x86_64.zip`

Non serve installare Python. Estrai l’intera cartella: l’eseguibile e la directory `_internal` devono restare insieme.

Su Linux:

```bash
tar -xzf Firemod-0.1.0-linux-x86_64.tar.gz
./Firemod/Firemod
```

Su Windows, estrai lo ZIP e apri `Firemod/Firemod.exe`. Gli eseguibili non sono firmati digitalmente. Le build CI Linux usano Ubuntu 22.04; una build locale può richiedere librerie della distribuzione su cui è stata compilata. L’interfaccia è attualmente in italiano.

## Prima connessione

1. Sulla Fire TV abilita **Debug ADB** nelle **Opzioni sviluppatore**. Se il menu non compare, apri **Informazioni** e premi sette volte sul nome del dispositivo.
2. Usa un **cavo USB dati**, se il modello lo supporta, oppure collega PC e Fire TV alla stessa rete e annota l’IP della chiavetta. La connessione Wi-Fi ADB usa normalmente la porta `5555`.
3. Accetta sulla TV la richiesta di autorizzazione del PC. Il tool non può aggirarla o abilitare il debug quando è disattivato.
4. Avvia Firemod. Se ADB è nel PATH o nell’Android SDK viene rilevato automaticamente. In alternativa, usa **Scegli ADB…** oppure **Installa ADB…**: quest’ultimo scarica i Platform-Tools ufficiali di Google dopo averne mostrato i termini.
5. Premi **Rileva**, seleziona il dispositivo giusto e scegli **Apri dispositivo**. Per il Wi-Fi, inserisci prima l’IP e premi **Connetti Wi-Fi**.

Riferimenti: [guida ADB Amazon](https://developer.amazon.com/docs/fire-tv/connecting-adb-to-device.html), [Platform-Tools Android](https://developer.android.com/tools/releases/platform-tools).

## Applica le migliorie

1. In **Applicazioni**, seleziona le app da disattivare oppure da riattivare. Le altre restano come sono.
2. In **Ottimizzazioni**, scegli gli interventi. **Prepara il profilo consigliato** seleziona alcune opzioni, senza applicarle automaticamente e senza scegliere app da rimuovere.
3. Premi **Rivedi le modifiche** e controlla il piano prima di applicarlo.
4. Leggi il riepilogo: distingue operazioni completate, rifiuti del firmware ed errori. Il registro contiene i dettagli.

Ogni valore precedente viene salvato **prima** della modifica. Il tool verifica poi lo stato restituito dal dispositivo: un messaggio apparentemente positivo non basta a dichiarare riuscita l’operazione.

## Home veloce: risultati e limiti

Nel prototipo originale, su una Fire TV Stick AFTT con Fire OS 5.2.9.5, il ritorno alla home è passato da circa **6–7 secondi a 1,3–1,6 secondi**. Sono misure da PC su un singolo dispositivo, comprensive del tempo del comando ADB; non sono una garanzia per altri modelli. [Dati del confronto](docs/benchmark.json).

L’acceleratore viene avviato con i permessi della shell ADB. Il companion gli invia una richiesta attraverso la propria cartella esterna; l’acceleratore chiede al servizio delle attività di riportare Luncher in primo piano. Esegue soltanto questa azione fissa: **non accetta comandi shell arbitrari e non apre porte di rete**. Il companion non richiede Internet.

**Puoi chiudere Firemod e scollegare il PC: l’acceleratore continua a funzionare finché la Fire TV rimane accesa. Dopo un riavvio completo o una perdita di alimentazione va riattivato dal PC.** Ricollega il dispositivo e seleziona soltanto l’opzione dell’acceleratore. Nel frattempo resta disponibile il metodo standard, che parte automaticamente.

Lo standby non equivale al riavvio; le schermate di risveglio dipendono anche dal firmware e dal telecomando. L’intervento accelera il passaggio alla home; **non porta l’avvio completo di Android a 0,1 secondi**.

## Ripristino e dati locali

Apri **Ripristino**, seleziona un punto del dispositivo connesso e conferma il ripristino. Firemod recupera i valori precedenti; se una chiave non esisteva, la elimina. Riporta le app allo stato registrato e rimuove soltanto i companion installati da quell’operazione.

Un Luncher già presente viene conservato. Prima di aggiornare un companion esistente viene salvato il suo APK; pacchetti con APK suddivisi in più file non vengono sostituiti. Il ripristino non è un’immagine completa del dispositivo e non recupera dati modificati al di fuori di queste operazioni.

I punti di ripristino restano in:

- Linux: `${XDG_DATA_HOME:-~/.local/share}/Firemod`
- Windows: `%LOCALAPPDATA%/Firemod`

Conserva questa cartella per ripristinare in futuro. Contiene identificatori del dispositivo e impostazioni originali: non pubblicarla nei bug report. È separata dal repository e Firemod non la invia a nessun servizio.

## Compatibilità

Il lavoro originale è stato verificato su **Fire TV Stick 2ª generazione, AFTT/tank, Fire OS 5.2.9.5**. La prima versione limita integrazione Home e acceleratore a **API 22**. Su versioni successive espone gestione app e impostazioni; disponibilità ed effetti dipendono dal firmware e non sono ancora verificati su quegli hardware.

I dispositivi **Vega OS**, che non eseguono app Android, non sono supportati. Vedi la [matrice di compatibilità](docs/COMPATIBILITY.md).

## Dal sorgente

Serve Python 3.12 o successivo:

```bash
python -m venv .venv
# Linux: source .venv/bin/activate
# Windows PowerShell: .venv/Scripts/Activate.ps1
python -m pip install -r requirements-build.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m firemod.app
```

Anteprima senza aprire ADB: `python -m firemod.app --demo`.

Verifiche: `python -m pytest -q` e `ruff check src tests scripts`.

Per compilare desktop e componenti Android, consulta [BUILDING.md](docs/BUILDING.md).

## Licenza e riconoscimenti

Il codice originale di Firemod è **AGPL-3.0-or-later**: [LICENSE](LICENSE). I componenti di terze parti mantengono le rispettive licenze: Luncher, il companion derivato da Firehome, Qt/PySide6, Python e PyInstaller sono elencati in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Firemod è indipendente e non è affiliato ad Amazon o Google.
