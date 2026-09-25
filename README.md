# Sentiment Analysis DevOps

Questo progetto realizza il deploy, il monitoraggio e l'automazione CI/CD di un modello di **Sentiment Analysis** per recensioni di prodotti. L'obiettivo è costruire una soluzione completa che non si limiti all'esposizione del modello tramite API, ma includa anche testing automatico, containerizzazione, deploy riproducibile e monitoraggio operativo.

L'applicazione è sviluppata con **FastAPI**, viene eseguita in container tramite **Docker**, è orchestrata con **Docker Compose**, utilizza **Jenkins** per la pipeline CI/CD e integra **Prometheus** e **Grafana** per la raccolta e la visualizzazione delle metriche.

Il modello lavora su recensioni in lingua inglese e restituisce una delle tre classi previste dal progetto:

```text
positive
neutral
negative
```

---

# Obiettivo del progetto

Il progetto nasce dallo scenario di una piattaforma e-commerce che riceve ogni giorno un numero elevato di recensioni e vuole automatizzare l'analisi del sentiment. Il sistema deve quindi permettere di inviare una recensione tramite API REST, ottenere il sentimento previsto, monitorare il comportamento dell'applicazione e distribuire automaticamente nuove versioni attraverso una pipeline CI/CD.

La soluzione realizzata copre l'intero ciclo applicativo: il codice viene versionato su GitHub, Jenkins rileva le modifiche, esegue i test, costruisce le immagini Docker, effettua il deploy dello stack e verifica che FastAPI, Prometheus e Grafana siano realmente operativi. Al termine della pipeline viene inviata una notifica email di successo o fallimento.

---

# Architettura

L'architettura complessiva è la seguente:

```text
                         GitHub
                            |
                            | commit / push
                            v
                         Jenkins
                            |
              +-------------+-------------+
              |                           |
              v                           v
          pytest                   Docker Compose
                                         |
                         +---------------+---------------+
                         |               |               |
                         v               v               v
                      FastAPI        Prometheus       Grafana
                      :8000            :9090           :3000
                         |
                         v
                 Modello Sentiment
```

FastAPI espone il modello di Sentiment Analysis e le metriche applicative. Prometheus interroga periodicamente l'endpoint `/metrics`, mentre Grafana utilizza Prometheus come datasource per costruire la dashboard di monitoraggio.

Poiché i tre servizi vengono eseguiti nello stesso stack Docker Compose, la comunicazione interna avviene tramite i nomi dei servizi. Prometheus raggiunge quindi l'API tramite:

```text
http://api:8000/metrics
```

mentre Grafana raggiunge Prometheus tramite:

```text
http://prometheus:9090
```

Le porte pubblicate sull'host sono `8000` per FastAPI, `9090` per Prometheus e `3000` per Grafana.

---

# Modello di Sentiment Analysis

Il modello è fornito nel file:

```text
model/sentiment_analysis_model.pkl
```

Il file utilizza il formato pickle, un meccanismo di serializzazione di Python che permette di salvare su disco oggetti complessi, come modelli di Machine Learning o pipeline scikit-learn, e di ricostruirli successivamente in memoria.

Nel nostro caso il file .pkl contiene la pipeline di Sentiment Analysis già addestrata. L'applicazione non deve quindi addestrare nuovamente il modello, ma può semplicemente caricarlo tramite pickle.load() e utilizzarlo per effettuare le predizioni.

La pipeline scikit-learn contiene un `CountVectorizer` seguito da un classificatore `MultinomialNB`. `CountVectorizer` trasforma la recensione in numeri, n conteggi delle parole, e poi `MultinomialNB` (Naive Bayes multinomiale) usa quei conteggi per stimare quale classe sia più probabile tra

- `negative`, 
- `neutral` e 
- `positive`.

Il caricamento del modello è gestito da `model_service.py`. Il percorso del pickle viene calcolato rispetto alla posizione reale del file Python, evitando dipendenze dalla directory dalla quale viene avviato il processo.

Il modello viene inoltre caricato in modalità lazy e mantenuto in cache tramite `lru_cache`. Questo significa che il file pickle non viene deserializzato a ogni richiesta, ma soltanto al primo utilizzo.

La confidence restituita dall'API indica quanto il modello è sicuro della previsione effettuata. 
Dopo aver ottenuto il sentimento con `predict()`, il servizio cerca la probabilità associata proprio a quella classe tra i valori restituiti da `predict_proba()` e usa quel valore come confidence.

---

# Compatibilità con scikit-learn

Il file pickle fornito dal progetto è stato originariamente serializzato con:

```text
scikit-learn 1.6.0
```

L'ambiente applicativo utilizza invece:

```text
Python 3.14
scikit-learn 1.9.1
```

Per questo motivo, durante il caricamento del modello, scikit-learn può mostrare `InconsistentVersionWarning` relativi a `CountVectorizer`, `MultinomialNB` e `Pipeline`.

La differenza di versione è stata mantenuta intenzionalmente per utilizzare Python 3.14. Prima di adottare definitivamente questa configurazione è stato eseguito un confronto utilizzando anche un ambiente compatibile con scikit-learn 1.6.0. Le stesse recensioni sono state elaborate con entrambe le versioni e sono stati confrontati il sentimento previsto, le probabilità restituite da `predict_proba()` e la confidence associata alla classe prevista. Nei casi verificati, i risultati ottenuti sono risultati identici.

---

# API REST

L'applicazione espone un'API FastAPI con versione 1.0.0. Gli endpoint principali sono:

```text
GET  /
GET  /health
POST /predict
GET  /metrics
```

La documentazione Swagger è disponibile all'indirizzo:

```text
http://localhost:8000/docs
```

## GET `/`

L'endpoint principale restituisce le informazioni essenziali del servizio:

```json
{
  "service": "Sentiment Analysis API",
  "version": "1.0.0",
  "status": "running"
}
```

## GET `/health`

L'health check non verifica soltanto che FastAPI sia avviata. Il servizio prova anche a caricare il modello, in modo da assicurarsi che il file sia raggiungibile e deserializzabile.

In condizioni normali la risposta è:

```json
{
  "status": "ok",
  "model": "loaded"
}
```

con codice HTTP `200`.

Se invece il modello non può essere caricato, l'API risponde con:

```json
{
  "detail": "Modello non disponibile"
}
```

e codice HTTP `503 Service Unavailable`.

Questo endpoint viene utilizzato sia da Docker Compose sia dalla pipeline Jenkins durante i controlli post-deploy.

## POST `/predict`

L'endpoint riceve una recensione in formato JSON:

```json
{
  "review": "This product is amazing! I love it."
}
```

e restituisce il sentimento previsto insieme alla confidence:

```json
{
  "sentiment": "positive",
  "confidence": 0.5683
}
```

Il campo `sentiment` può assumere esclusivamente i valori `negative`, `neutral` o `positive`, mentre `confidence` è vincolato all'intervallo compreso tra `0.0` e `1.0`.

Se il modello non è disponibile viene restituito `503 Service Unavailable`. Se invece il caricamento è riuscito ma si verifica un errore durante l'inferenza, l'API restituisce `500 Internal Server Error`.

## GET `/metrics`

L'endpoint espone le metriche nel formato atteso da Prometheus:

```text
http://localhost:8000/metrics
```

---

# Validazione delle richieste

Il campo `review` è obbligatorio e deve contenere da 1 a 5000 caratteri.

Prima della validazione finale viene applicato `strip()`, quindi una stringa contenente esclusivamente spazi viene considerata non valida. Una recensione vuota o superiore a 5000 caratteri produce una risposta HTTP `422 Unprocessable Entity`.

Esempio non valido:

```json
{
  "review": "   "
}
```

---

# Gestione degli errori e logging

Il progetto distingue esplicitamente gli errori di caricamento del modello dagli errori di inferenza.

`ModelLoadError` rappresenta un problema durante l'apertura o la deserializzazione del pickle. Questo errore può produrre un `503` sia su `/health` sia su `/predict`.

`PredictionError` rappresenta invece un errore avvenuto dopo che il modello è stato caricato correttamente, durante l'esecuzione della predizione. In questo caso `/predict` restituisce `500`.

Gli errori vengono registrati tramite il modulo `logging` di Python e `logger.exception()`, così da includere nei log anche lo stack trace utile per la diagnosi.

Quando una richiesta di predizione non può essere completata viene inoltre incrementata la metrica:

```text
prediction_errors_total
```

---

# Test automatici

Il progetto utilizza `pytest` e separa i test unitari dai test di integrazione:

```text
test/unit
test/integration
```

L'ultima verifica completa della suite ha prodotto:

```text
13 passed
```

I test unitari verificano il comportamento di `model_service.py` senza dipendere necessariamente dal pickle reale. Il servizio supporta infatti l'iniezione di un modello, quindi i test possono utilizzare oggetti fittizi per verificare la classe restituita, il calcolo della confidence e la conversione degli errori del modello in `PredictionError`.

I test di integrazione utilizzano il `TestClient` di FastAPI e verificano il comportamento dell'applicazione completa. Sono coperti l'endpoint informativo, l'health check, il caso di modello non disponibile, le tre classi di sentiment, la validità della confidence, gli input non validi, l'endpoint `/metrics`, gli errori tecnici di predizione e l'incremento della relativa metrica.

Tra i casi di test viene utilizzata anche la frase riportata nelle specifiche del progetto:

```text
This product is amazing! I love it.
```

Per eseguire l'intera suite:

```powershell
.venv\Scripts\python.exe -m pytest
```

Per eseguire separatamente unit test e integration test:

```powershell
.venv\Scripts\python.exe -m pytest test\unit
.venv\Scripts\python.exe -m pytest test\integration
```

Durante i test possono comparire warning relativi alla compatibilità scikit-learn già descritta.

---

# Avvio locale

Per lavorare sul progetto sono necessari Git, Python 3.14, Docker Desktop e Docker Compose. Jenkins e Java sono necessari soltanto sulla macchina utilizzata come host della pipeline CI/CD.

Il repository può essere clonato con:

```powershell
git clone https://github.com/LucaTiriolo/sentiment-analysis-devops.git
cd sentiment-analysis-devops
```

Su Windows l'ambiente virtuale viene creato con:

```powershell
py -3.14 -m venv .venv
```

Le dipendenze vengono quindi installate con:

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Per avviare FastAPI direttamente, senza Docker:

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Una volta avviata, l'applicazione è disponibile sui seguenti indirizzi:

```text
API:       http://localhost:8000
Swagger:   http://localhost:8000/docs
Health:    http://localhost:8000/health
Metrics:   http://localhost:8000/metrics
```

Non bisogna eseguire contemporaneamente Uvicorn locale e il container API sulla stessa porta `8000`.

---

# Docker

Il servizio FastAPI viene containerizzato tramite il `Dockerfile`, basato sull'immagine:

```text
python:3.14.7-slim
```

Il Dockerfile installa le dipendenze, copia il codice e il modello, espone la porta `8000` e avvia Uvicorn.

Per motivi di sicurezza il processo non viene eseguito come `root`. Durante la build viene creato l'utente:

```text
appuser
```

e il container utilizza questo account per eseguire l'applicazione.

La configurazione può essere verificata con:

```powershell
docker compose exec api whoami
```

Il risultato atteso è, appunto, **appuser**

---

# Docker Compose

L'intero stack viene gestito dal file:

```text
compose.yaml
```

I servizi definiti sono `api`, `prometheus` e `grafana`.

Per avviare l'ambiente completo:

```powershell
docker compose up -d --build
```

Lo stato può essere controllato con:

```powershell
docker compose ps
```

Dopo il completamento degli health check, i tre servizi devono risultare `healthy`.

Per arrestare lo stack:

```powershell
docker compose down
```

Per eliminare anche i volumi persistenti:

```powershell
docker compose down -v
```

Quest'ultimo comando rimuove i dati mantenuti nei volumi Docker, quindi deve essere utilizzato consapevolmente.

---

# Health check

La soluzione utilizza controlli di salute sia a livello Docker sia nella pipeline Jenkins.

FastAPI viene verificata tramite:

```text
http://localhost:8000/health
```

Prometheus viene verificato tramite:

```text
http://localhost:9090/-/ready
```

Grafana viene verificato tramite:

```text
http://localhost:3000/api/health
```

Docker Compose utilizza anche la condizione:

```yaml
condition: service_healthy
```

per coordinare l'avvio dei servizi. Prometheus attende quindi che l'API risulti healthy e Grafana attende che Prometheus sia pronto.

---

# Prometheus

La configurazione di Prometheus si trova nel file:

```text
monitoring/prometheus/prometheus.yml
```

Prometheus effettua la lettura delle metriche ogni 5 secondi e raggiunge FastAPI tramite il nome del servizio Docker `api`.

L'interfaccia è disponibile su:

```text
http://localhost:9090
```

mentre la pagina dei target è:

```text
http://localhost:9090/targets
```

Il target `sentiment-analysis-api` deve risultare `UP`.

---

# Metriche Prometheus

Le metriche personalizzate esposte dall'applicazione sono:

```text
http_request_duration_seconds
prediction_errors_total
predictions_total
```

`http_request_duration_seconds`  misura il tempo di risposta delle richieste HTTP e utilizza le label `method`, `endpoint` e `status_code`. Viene egistrata anche la durata della richiesta anche quando si verifica un'eccezione, grazie all'utilizzo di un blocco `finally`.

`prediction_errors_total`  misura gli errori tecnici che impediscono al servizio di completare una predizione. Rientrano in questa categoria, per esempio, l'indisponibilità del modello e gli errori durante l'inferenza.
Questa metrica non rappresenta gli errori di classificazione del modello rispetto al sentimento reale della recensione. 

`predictions_total` misura le predizioni completate correttamente. La label `sentiment` permette di separare le serie relative a `positive`, `neutral` e `negative`.

Il client Prometheus espone inoltre metriche relative al processo Python. Il progetto utilizza in particolare:

```text
process_cpu_seconds_total
process_resident_memory_bytes
```

Queste metriche descrivono le risorse utilizzate dal processo FastAPI e non l'utilizzo complessivo della macchina host.

---

# Query Prometheus principali

La distribuzione delle predizioni per sentimento viene calcolata con:

```promql
sum by (sentiment) (predictions_total)
```

Il numero complessivo di errori tecnici viene ottenuto con:

```promql
sum(prediction_errors_total)
```

Il tempo medio cumulativo di risposta dell'endpoint `/predict`, espresso in secondi, è:

```promql
sum(http_request_duration_seconds_sum{endpoint="/predict"})
/
sum(http_request_duration_seconds_count{endpoint="/predict"})
```

Per ottenere il valore in millisecondi viene utilizzata:

```promql
1000 *
sum(http_request_duration_seconds_sum{endpoint="/predict"})
/
sum(http_request_duration_seconds_count{endpoint="/predict"})
```

Un tempo medio recente può essere calcolato con:

```promql
sum(rate(http_request_duration_seconds_sum{endpoint="/predict"}[5m]))
/
sum(rate(http_request_duration_seconds_count{endpoint="/predict"}[5m]))
```

In assenza di richieste sufficienti nella finestra temporale, le query basate su `rate()` possono restituire `NaN`.

L'utilizzo CPU del processo viene rappresentato tramite:

```promql
100 * rate(process_cpu_seconds_total[1m])
```

Il valore rappresenta la percentuale equivalente rispetto a un singolo core logico e non la percentuale complessiva della CPU dell'host.

La memoria residente del processo viene invece calcolata con:

```promql
process_resident_memory_bytes / 1024 / 1024
```

ottenendo il valore RSS in MiB.

---

# Grafana

Grafana viene avviato automaticamente da Docker Compose ed è disponibile all'indirizzo:

```text
http://localhost:3000
```

La configurazione non dipende da passaggi manuali eseguiti nella GUI. Il datasource Prometheus e la dashboard vengono infatti provisionati automaticamente tramite file versionati nel repository.

Il datasource è definito in:

```text
monitoring/grafana/provisioning/datasources/prometheus.yml
```

e utilizza:

```text
http://prometheus:9090
```

come URL interno.

La dashboard viene caricata tramite:

```text
monitoring/grafana/provisioning/dashboards/dashboards.yml
```

e il relativo JSON si trova in:

```text
monitoring/grafana/dashboards/sentiment-analysis-monitoring.json
```

Le modifiche definitive alla dashboard devono quindi essere riportate nei file versionati, evitando di affidarsi esclusivamente a modifiche effettuate tramite interfaccia Grafana.

---

# Dashboard di monitoraggio

La dashboard principale si chiama:

```text
Sentiment Analysis Monitoring
```

L'auto-refresh è configurato ogni 5 secondi per fornire una visualizzazione quasi in tempo reale.

La dashboard contiene cinque pannelli. Il primo mostra la distribuzione delle predizioni tra sentiment positivo, neutro e negativo tramite un Pie Chart e utilizza:

```promql
sum by (sentiment) (predictions_total)
```

Il secondo pannello mostra gli errori tecnici di predizione tramite uno Stat:

```promql
sum(prediction_errors_total)
```

In questo caso `0` errori viene visualizzato in verde, mentre da `1` errore in poi il valore viene evidenziato in rosso.

Il terzo pannello visualizza il tempo medio di risposta di `/predict` in millisecondi:

```promql
1000 *
sum(http_request_duration_seconds_sum{endpoint="/predict"})
/
sum(http_request_duration_seconds_count{endpoint="/predict"})
```

Il quarto pannello visualizza l'utilizzo CPU del processo API:

```promql
100 * rate(process_cpu_seconds_total[1m])
```

e il quinto mostra la memoria residente del processo:

```promql
process_resident_memory_bytes / 1024 / 1024
```

Anche per CPU e memoria non vengono applicate soglie non giustificate dai requisiti.

---

# Jenkins CI/CD

La pipeline CI/CD è definita nel file:

```text
Jenkinsfile
```

Il flusso è:

```text
Git commit / push
       |
       v
Jenkins rileva la modifica
       |
       v
Checkout
       |
       v
Setup Python 3.14
       |
       v
Unit Test
       |
       v
Integration Test
       |
       v
Docker Compose Build
       |
       v
Deploy
       |
       v
Health Check
       |
       v
Email SUCCESS / FAILURE
```

La pipeline crea un ambiente virtuale dedicato:

```text
.venv-jenkins
```

e installa le dipendenze definite in `requirements.txt`.

I test vengono eseguiti separatamente:

```powershell
.venv-jenkins\Scripts\python.exe -m pytest test\unit
.venv-jenkins\Scripts\python.exe -m pytest test\integration
```

La build Docker viene eseguita con:

```powershell
docker compose build
```

e il deploy con:

```powershell
docker compose up -d --remove-orphans
```

Dopo il deploy Jenkins controlla FastAPI, Prometheus e Grafana. Ogni servizio viene verificato con più tentativi e una breve attesa tra un tentativo e il successivo, evitando di considerare fallita la pipeline soltanto perché un container ha impiegato qualche secondo in più per diventare operativo.

---

# Trigger automatico della pipeline

Il trigger è configurato tramite:

```groovy
pollSCM('H/2 * * * *')
```

Jenkins interroga periodicamente il repository e, quando rileva un nuovo commit sul branch monitorato, avvia automaticamente la pipeline.

La scelta del polling è legata all'ambiente di esecuzione: Jenkins viene eseguito localmente e non è pubblicamente raggiungibile da GitHub. Di conseguenza non è possibile utilizzare direttamente un webhook verso l'istanza locale.

Il comportamento resta comunque automatico: dopo un commit e il relativo push, Jenkins rileva la modifica al successivo controllo SCM e avvia la pipeline senza intervento manuale.

---

# Configurazione Jenkins

Sulla macchina Jenkins devono essere installati Java, Python 3.14, Git, Docker Desktop e Docker Compose. L'utente con cui viene eseguito il servizio Jenkins deve poter accedere correttamente a Docker.

Il job deve essere creato come **Pipeline** utilizzando **Pipeline script from SCM**, con Git come SCM.

Il repository configurato è:

```text
https://github.com/LucaTiriolo/sentiment-analysis-devops.git
```

Il branch monitorato è:

```text
*/main
```

e lo script path è:

```text
Jenkinsfile
```

Il repository è pubblico, quindi il checkout non richiede credenziali GitHub.

Per le notifiche email viene utilizzato **Email Extension Plugin**.

---

# Notifiche email

La pipeline invia una email sia in caso di successo sia in caso di fallimento.

La configurazione SMTP utilizzata nello sviluppo è:

```text
SMTP server: smtp.gmail.com
Port: 587
TLS: enabled
SSL: disabled
```

Le credenziali non vengono salvate nel repository. Le notifiche includono il nome del job, il numero della build, lo stato finale e l'URL della build.

---

# Sicurezza

Il progetto applica alcune precauzioni di base.

Il container FastAPI viene eseguito tramite l'utente non privilegiato `appuser` e non come `root`.

Le credenziali SMTP non vengono versionate nel repository. Il file `.env` è inoltre escluso da Git e dal contesto Docker.

Infine, l'input della recensione ha una dimensione massima di 5000 caratteri, evitando richieste applicative eccessivamente grandi.

---

# Scalabilità e limiti

L'architettura attuale utilizza una singola istanza FastAPI gestita tramite Docker Compose. La soluzione soddisfa gli obiettivi del progetto relativi a containerizzazione, deploy automatico, riproducibilità, monitoraggio e CI/CD, ma non rappresenta un sistema ad alta disponibilità o autoscalabile.

La topologia corrente è:

```text
FastAPI
   |
   `-- 1 container
```

Non sono presenti load balancing, replica automatica dell'API, orchestrazione Kubernetes, autoscaling o failover tra più istanze.

Docker Compose è stato scelto perché adeguato alla complessità richiesta dalla traccia. 

---

# Avvio rapido

Con Python e Docker già installati, il progetto può essere avviato con:

```powershell
git clone https://github.com/LucaTiriolo/sentiment-analysis-devops.git
cd sentiment-analysis-devops

py -3.14 -m venv .venv

.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

.venv\Scripts\python.exe -m pytest

docker compose up -d --build
```

Lo stato dei servizi può essere controllato con:

```powershell
docker compose ps
```

Gli indirizzi principali sono:

```text
FastAPI:            http://localhost:8000
Swagger:            http://localhost:8000/docs
Health:             http://localhost:8000/health
Metrics:            http://localhost:8000/metrics
Prometheus:         http://localhost:9090
Prometheus Targets: http://localhost:9090/targets
Grafana:            http://localhost:3000
```


