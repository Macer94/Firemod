# Manuale utenti — Firemod 0.1.0

[README](../README.md) · [Compatibilità](COMPATIBILITY.md) · [Agenti](AGENT_GUIDE.md) · [Download ufficiali](https://github.com/Macer94/Firemod/releases/latest)

Questo manuale descrive i pulsanti e il comportamento effettivo della versione 0.1.0. La GUI è in italiano; alcuni messaggi tecnici del registro e del firmware sono in inglese.

## 1. Cosa serve e cosa aspettarsi

Servono un PC x86_64 Linux o Windows, una Fire TV Android con API almeno 22, un collegamento ADB autorizzato e un telecomando per accettare la richiesta sulla TV. Per i pacchetti compilati non serve Python. Le build ufficiali sono prodotte e provate su Ubuntu 22.04 e Windows Server 2022; non è una certificazione di ogni distribuzione o edizione Windows.

Firemod riconosce per le modifiche un produttore `Amazon` e un modello che inizia per `AFT`. Fire OS 5/API 22 è l’unica versione abilitata per il companion Home e l’acceleratore. Sui Fire OS successivi sono disponibili gestione app e impostazioni, secondo quanto consente il firmware. Vega OS non è supportato. Non sono supportate modifiche a telefoni, tablet e dispositivi di altri produttori.

L’esperienza originale riguarda AFTT/tank con Fire OS 5.2.9.5. I test desktop non provano da soli che un’opzione funzioni su un altro firmware. Consulta la [matrice](COMPATIBILITY.md) prima di scegliere gli interventi.

## 2. Scaricare, verificare e avviare

Apri le [Releases di Macer94/Firemod](https://github.com/Macer94/Firemod/releases/latest). Scarica l’archivio del tuo sistema e `SHA256SUMS` della **stessa release**. Gli asset `firemod-home.apk` e `firemod-bridge.jar` sono già inclusi negli archivi desktop: normalmente non devi installarli a mano. Gli archivi automatici **Source code** contengono i sorgenti, non gli eseguibili pronti.

Il download facoltativo `Firemod-0.1.0-documentation.zip` contiene le guide aggiornate e ha un file `.sha256` separato. Estrailo e apri `Firemod-documentation/README.md` con un visualizzatore Markdown, oppure consulta gli stessi documenti su GitHub. L’archivio non contiene un nuovo eseguibile e non cambia la versione del programma.

### Linux

Dalla directory dei download:

```bash
sha256sum Firemod-0.1.0-linux-x86_64.tar.gz
```

Confronta tutti i caratteri dell’hash con la riga dello stesso file in `SHA256SUMS`. Se hai scaricato **tutti** i file elencati, puoi usare `sha256sum -c SHA256SUMS`; i file non scaricati saranno segnalati come mancanti. Un hash diverso richiede un nuovo download, non l’estrazione del file incompleto.

```bash
tar -xzf Firemod-0.1.0-linux-x86_64.tar.gz
./Firemod/Firemod
```

Per avviare da un’altra directory usa il percorso completo dell’eseguibile. Se il gestore archivi ha perso il permesso di esecuzione, puoi ripristinarlo con `chmod +x Firemod/Firemod`.

### Windows

In PowerShell, dalla cartella dei download:

```powershell
Get-FileHash .\Firemod-0.1.0-windows-x86_64.zip -Algorithm SHA256
Get-Content .\SHA256SUMS
```

Confronta l’hash con la riga dello ZIP; maiuscole e minuscole dell’hash sono equivalenti. Usa **Estrai tutto** sullo ZIP e apri `Firemod\Firemod.exe` dalla cartella estratta. Non eseguirlo dentro l’anteprima dello ZIP e non spostare il solo `.exe`.

### File da conservare

Tieni insieme eseguibile e `_internal`. Non servono privilegi amministrativi sul PC per il normale uso del programma; installare un driver USB o una libreria di sistema può richiederli. Gli eseguibili non sono firmati digitalmente: un checksum permette di confrontare il download con quello pubblicato, non sostituisce una firma dell’autore. Verifica la provenienza del file anziché disabilitare globalmente le protezioni del sistema.

Per aggiornare, chiudi Firemod e usa una nuova cartella estratta. La cronologia di ripristino è nella cartella dati del tuo account, separata dall’eseguibile: non cancellarla durante l’aggiornamento.

## 3. Preparare la Fire TV e ADB

### Sulla TV

1. Apri **Impostazioni → La mia Fire TV / Dispositivo → Opzioni sviluppatore**. I nomi variano secondo il firmware.
2. Se le opzioni sviluppatore non compaiono, entra in **Informazioni**, seleziona il nome del dispositivo e premi sette volte il tasto di selezione del telecomando.
3. Abilita **Debug ADB**. Per installare il companion e Luncher, controlla anche le opzioni per app da origini sconosciute disponibili sul tuo firmware.
4. Mantieni la TV visibile per accettare la richiesta di autorizzazione del PC. Può chiamarsi **Consenti debug USB?** anche quando la connessione è via rete.

Firemod non abilita il debug a distanza e non può accettare la richiesta al tuo posto. Per il percorso specifico del modello consulta la [guida ADB Amazon](https://developer.amazon.com/docs/fire-tv/connecting-adb-to-device.html).

### Sul PC

Avvia Firemod. Se indica **ADB non trovato**, scegli una delle alternative:

- **Scegli ADB…**: seleziona `adb` su Linux o `adb.exe` su Windows da un’installazione esistente.
- **Installa ADB…**: mostra il riferimento ai termini SDK di Google e, dopo la tua conferma, scarica dal dominio ufficiale `dl.google.com` ed estrae i file necessari nella cartella dati di Firemod. Richiede Internet.
- Installa i [Platform-Tools ufficiali](https://developer.android.com/tools/releases/platform-tools) e rendili disponibili nel `PATH`, oppure imposta `FIREMOD_ADB` al percorso dell’eseguibile prima dell’avvio.

Non serve l’intero Android Studio. Su Windows conserva `AdbWinApi.dll` e `AdbWinUsbApi.dll` insieme ad `adb.exe`. La scelta effettuata nella GUI viene ricordata tramite le preferenze Qt dell’account del PC; per cambiarla usa di nuovo **Scegli ADB…**. Un percorso valido già salvato nella GUI ha precedenza sul rilevamento automatico.

## 4. Collegare e aprire il dispositivo

### Collegamento Wi-Fi

1. Collega PC e Fire TV alla stessa rete locale e annota l’IP della TV da **Informazioni → Rete**, se disponibile. Una rete ospiti con isolamento fra client può impedire la connessione.
2. Nel campo **Indirizzo IP della Fire TV**, inserisci per esempio `192.168.1.50` oppure `192.168.1.50:5555`, sostituendo l’indirizzo con quello reale. Se ometti la porta su IPv4 viene usata `5555`. Un IPv6 va scritto con parentesi e porta, per esempio `[fd00::50]:5555`.
3. Premi **Connetti Wi-Fi**, accetta la richiesta sulla TV e premi **Rileva** se necessario.
4. Seleziona il dispositivo in stato **device** e premi **Apri dispositivo**.

Il campo accetta IP numerici, non URL, nomi host o comandi. Firemod non esegue un abbinamento `adb pair` né configura da solo porte o debug di rete: il dispositivo deve già offrire una connessione ADB compatibile. Non occorre esporre la porta del dispositivo su Internet.

### Collegamento USB

Usa una porta del dispositivo che supporti il debug e un cavo **dati**: un collegamento usato soltanto per l’alimentazione non garantisce ADB. Su alcuni modelli il debug USB va attivato separatamente; su Windows può servire il driver indicato nella guida Amazon. La porta HDMI trasporta il video, non la connessione ADB del PC.

Premi **Rileva**, autorizza il PC sulla TV, seleziona il dispositivo in stato **device** e premi **Apri dispositivo**. Se il tuo modello non offre un collegamento USB dati utilizzabile, usa la rete.

### Controllare la schermata Dispositivo

Verifica modello e Fire OS prima di preparare modifiche. **RAM disponibile** è una lettura istantanea: usa `MemAvailable`, oppure `MemFree` quando il kernel non fornisce il primo valore. Non è un benchmark. **Spazio libero** riguarda `/data`; nascondere un’app non libera il suo APK. **Home veloce** indica lo stato dell’acceleratore Firemod, non quello di altri helper eventualmente installati in precedenza.

Il contatore delle app disattivate deriva da `pm list packages -d`: può non comprendere tutte le app nascoste. Per il singolo pacchetto consulta lo stato nella pagina **Applicazioni**.

## 5. Scegliere le modifiche

### Applicazioni

La casella **MODIFICA** prepara un’azione in base allo stato corrente:

| Stato della riga | Cosa succede se selezioni la casella |
| --- | --- |
| Attiva | Viene proposta la disattivazione |
| Inattiva · riattivabile | Viene proposta la riattivazione |
| Protetta | La casella non consente modifiche |

Lascia vuote le caselle delle app che non vuoi modificare. Non devi selezionare tutte le app da conservare. Cerca per nome o identificatore; **Mostra componenti protetti** rende visibili anche le righe bloccate. Cambiare filtro non cancella le selezioni nascoste.

La disattivazione conserva dati e accessi e tenta i comandi consentiti dal firmware. Su API 22 viene usato l’occultamento (`pm hide`); su versioni successive viene tentata prima la disattivazione (`pm disable-user`) e poi l’occultamento. Il tool verifica lo stato risultante. Un’app non modificabile rimane segnalata come invariata.

Amazon Home, impostazioni e componenti di sistema non riconosciuti come opzionali restano protetti. Appstore, profili, Prime Video, Luncher e helper Home sono esplicitamente conservati. La piccola lista opzionale comprende metriche, servizio pubblicitario, Photos, Music e Alexa: se il firmware consente di disattivare Alexa, anche le funzioni vocali possono smettere di funzionare. Le note della riga spiegano i casi noti.

### Ottimizzazioni

| Opzione | Effetto richiesto | Limite |
| --- | --- | --- |
| Riduci le animazioni | Scale a `0`, `0.5` oppure `1` | Non aumenta CPU o RAM fisica |
| Limita statistiche e tracciamento | Salva le chiavi privacy supportate dal progetto | Il valore salvato non prova che ogni servizio lo rispetti |
| Disattiva screensaver fotografico | Disabilita tre impostazioni screensaver | Non è una promessa su tutti i meccanismi di standby del firmware |
| Installa Luncher e abilita Firemod Home | Installa il companion e Luncher se assente | Solo API 22; Amazon Home resta installata |
| Attiva l’acceleratore | Avvia il processo shell che riporta Luncher davanti | Solo API 22; richiede il companion e dura fino al riavvio o all’arresto del processo |

**Prepara il profilo consigliato** seleziona animazioni a `0`, privacy e, su API 22, Home e acceleratore. Non applica nulla e non modifica le selezioni delle app o dello screensaver che hai già impostato. Controlla il piano anche quando usi il profilo consigliato.

Le pubblicità interne a YouTube, Prime Video o altre app non vengono bloccate. La home offline di Luncher non mostra le inserzioni della home Amazon; non elimina Amazon Home dal dispositivo.

### Conferma e risultato

1. Premi **Rivedi le modifiche**.
2. Controlla il modello e tutte le righe del piano, incluse le app selezionate prima di una ricerca.
3. Conferma **Apply / Applica**, oppure annulla. Nessuna modifica alla Fire TV parte prima della conferma.
4. Attendi senza scollegare il dispositivo. La barra è un indicatore di attività, non una percentuale del tempo rimanente.
5. Leggi il riepilogo e la pagina **Registro**.

`[OK]` indica un’operazione completata; `[INVARIATO]` un’operazione già soddisfatta, non supportata o rifiutata; `[ERRORE]` un problema da esaminare. Non contare solo il numero finale: leggi i motivi. Il piano può riuscire in parte e non esegue un rollback generale automatico.

Dopo l’operazione Firemod rilegge il dispositivo. Le selezioni delle app vengono ricostruite, mentre le opzioni possono rimanere spuntate. Prima di una nuova operazione controllale di nuovo.

## 6. Home veloce nella pratica

La prima volta, su API 22, seleziona **Installa Luncher e abilita Firemod Home** e **Attiva l’acceleratore della home per questa accensione**. Dopo il risultato, controlla **Home veloce: Attiva**. Prova il tasto Home del telecomando, l’apertura di un’app e il ritorno alle impostazioni: il tuo firmware può comportarsi diversamente dal dispositivo originale.

Puoi chiudere il tool e scollegare il PC. Il processo acceleratore rimane sulla Fire TV durante quella accensione; non viene installato un servizio PC che debba restare in esecuzione.

| Evento | Comportamento atteso |
| --- | --- |
| Chiusura di Firemod / scollegamento del PC | L’acceleratore già attivo continua a funzionare |
| Standby e risveglio | Non equivalgono a un reboot; il firmware può comunque terminare processi |
| Riavvio completo, perdita di corrente o processo terminato | L’acceleratore deve essere riattivato |
| Acceleratore assente o senza risposta | Il companion usa il normale avvio di Luncher, che può essere più lento |

Per riattivarlo: ricollega la TV, apri il dispositivo, **deseleziona le altre opzioni e le app**, seleziona solo l’acceleratore, rivedi e applica. Se il companion non è mai stato installato, va prima installato. Non serve reinstallare Luncher a ogni accensione.

Il tool accelera il passaggio alla Home; non azzera il tempo di avvio di Android e non promette 0,1 secondi. Le misure del prototipo sono documentate nel [README](../README.md#home-veloce-risultati-e-limiti).

## 7. Ripristino e conservazione dei dati

Prima delle modifiche viene creato un punto locale. Per usarlo:

1. Ricollega lo stesso dispositivo con lo stesso identificatore ADB e premi **Apri dispositivo**.
2. Apri **Ripristino**. Le date della lista sono in **UTC**, non necessariamente nell’ora locale del PC.
3. Seleziona il punto e premi **Ripristina il punto selezionato…**.
4. Leggi l’avviso sulle modifiche successive agli stessi valori, conferma e controlla il registro finale.

Un punto annulla le operazioni registrate in quel punto: non è una fotografia di tutto il dispositivo. Per annullare più interventi consecutivi, procedi dal punto più recente a quelli precedenti. Ripristinare direttamente un vecchio punto può sovrascrivere impostazioni cambiate nel frattempo senza annullare interventi diversi fatti successivamente.

Il ripristino recupera i valori originali e rimuove una chiave se prima non esisteva. Riporta le app al comportamento attivo/inattivo e alla visibilità salvati; su Android 5.1 uno stato predefinito può diventare esplicitamente abilitato. Non cancella in massa applicazioni o dati. Può rimuovere Luncher e Firemod Home solo se sono stati installati ex novo da quell’operazione. Un Luncher già presente viene conservato; per aggiornare un companion preesistente viene prima salvato il suo APK. Un APK suddiviso in split non viene sostituito.

Se una modifica o un ripristino viene interrotto, conserva il punto e gli eventuali backup APK. Le operazioni di ripristino già completate vengono segnate; quelle non riuscite possono essere ritentate dallo stesso punto dopo aver risolto la connessione. Un firmware può rifiutare anche il ripristino: il tool lo segnala, non garantisce un’immagine completa o il recupero di dati cambiati da altre app.

### Dove sono i dati

| Sistema | Cartella dati predefinita |
| --- | --- |
| Linux | `~/.local/share/Firemod`, oppure `$XDG_DATA_HOME/Firemod` se impostato |
| Windows | `%LOCALAPPDATA%\Firemod` |

**Apri cartella locale** apre questa cartella. I punti sono in `devices/<hash-del-seriale>/<data-UTC-e-id>/snapshot.json`, con eventuali APK accanto. Il file JSON contiene anche il seriale in chiaro: il nome della directory non rende anonima la cronologia. Copia l’intera cartella dati, a programma fermo, in una posizione privata se vuoi conservarla o trasferirla su un altro PC.

In 0.1.0 l’identità è il seriale restituito da ADB: per la rete è normalmente `IP:porta`, per USB può essere un altro valore. Un IP diverso o il cambio USB/Wi-Fi crea una cronologia distinta. Il programma non riconosce automaticamente che si tratta della stessa TV. Prima prova la connessione originale; non rinominare o modificare JSON per forzare il ripristino su un dispositivo diverso.

Il testo nella pagina **Registro** appartiene alla sessione aperta: non esiste un’esportazione automatica del registro completo. I punti conservano invece operazioni, stati e riepiloghi scritti dal motore. Il programma non carica la cronologia su Internet. Il download opzionale di ADB richiede una connessione a Google e ADB comunica con il dispositivo selezionato.

## 8. Uso assistito e diagnosi

Per affidare la diagnosi a un agente usa la [guida dedicata](AGENT_GUIDE.md). Firemod offre da sorgente una modalità dimostrativa, uno screenshot con dati dimostrativi e una diagnosi JSON in sola lettura. Non ha una CLI `apply`, un importatore di piani o una modalità automatica di rimozione app.

I report diagnostici includono identificatori del dispositivo. Tienili privati e depurali prima di condividerli. Una schermata dimostrativa non dimostra la compatibilità del tuo hardware.

## 9. Risoluzione dei problemi

| Sintomo | Controlli e azioni |
| --- | --- |
| ADB non trovato | Scegli il file corretto o usa il download ufficiale. Dopo aver modificato il `PATH`, riapri Firemod |
| Lista vuota su USB | Verifica supporto del modello, cavo dati, debug USB, driver Windows o permessi USB Linux. Prova la rete se disponibile |
| `unauthorized` | Guarda la TV e accetta la richiesta del PC, poi ripeti **Rileva** |
| `offline`, timeout o connessione rifiutata | Controlla IP, rete, debug e alimentazione; ripeti la connessione. Non eseguire un ripristino mentre la connessione è instabile |
| Il PC vede un dispositivo ma Firemod non lo apre | Seleziona una riga in stato `device`. Controlla modello Amazon/AFT e API: non tutti i dispositivi visibili sono supportati |
| Nome host rifiutato | Inserisci un IP numerico; per IPv6 usa `[indirizzo]:porta` |
| App o chiave rifiutata | Leggi il motivo nel registro. Non insistere con comandi non previsti per rimuovere un componente protetto |
| Home lenta dopo reboot | Ricollega il PC e riattiva soltanto l’acceleratore |
| Installazione APK rifiutata | Controlla i permessi previsti dal firmware e l’errore. Un conflitto di firma con un helper esistente non si risolve cancellandone alla cieca i dati |
| Cronologia vuota | Controlla account del PC, cartella dati, seriale ADB e connessione originale |
| Spazio libero quasi invariato | Nascondere/disabilitare conserva l’APK e i dati: è previsto |
| La GUI Linux non parte | Avvia l’eseguibile da terminale per leggere l’errore. Verifica desktop grafico, cartella `_internal`, architettura e librerie Qt richieste |

Su Ubuntu 22.04, per errori di librerie grafiche mancanti, le dipendenze usate dalla CI comprendono:

```bash
sudo apt-get install libegl1 libgl1 libopengl0 libxcb-cursor0 libxcb-shape0 libxkbcommon-x11-0 libgtk-3-0
```

Questo comando modifica il PC e richiede privilegi amministrativi; i nomi dei pacchetti dipendono dalla distribuzione. `QT_QPA_PLATFORM=offscreen` serve a test e screenshot automatici: non offre una GUI interattiva sullo schermo.

Per chiedere assistenza apri una [issue](https://github.com/Macer94/Firemod/issues) con versione del tool, sistema del PC, modello, Fire OS/API se nota, procedura per riprodurre il problema e messaggio depurato. Non allegare cronologie complete, dump dei pacchetti, backup APK, IP personali, seriali, credenziali o chiavi di debug/firma.
