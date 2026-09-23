# Sentiment Analysis DevOps


L'obiettivo del progetto è realizzare il deploy e il monitoraggio di un modello di Sentiment Analysis per recensioni, utilizzando una pipeline CI/CD e strumenti DevOps.

## Stato attuale

Il progetto è nella fase iniziale di configurazione.

È disponibile una semplice API REST realizzata con FastAPI che espone un endpoint di prova:

```http
GET /

## CI/CD

La pipeline Jenkins esegue automaticamente test, build Docker, deploy e health check.

## Monitoraggio con Prometheus e Grafana

L'applicazione espone metriche compatibili con Prometheus tramite l'endpoint:

```http
GET /metrics
```

Le metriche vengono poi raccolte da Prometheus e visualizzate tramite dashboard Grafana.

### Metriche esposte dall'applicazione

Sono state definite le seguenti metriche personalizzate:

```text
http_request_duration_seconds
prediction_errors_total
predictions_total
```

`http_request_duration_seconds` misura il tempo di risposta delle richieste HTTP.

`prediction_errors_total` conta gli errori verificatisi durante l'esecuzione delle predizioni.

`predictions_total` conta il numero di predizioni suddivise per sentimento:

```text
positive
neutral
negative
```

Il client Prometheus espone inoltre metriche relative al processo Python, tra cui CPU e memoria quando disponibili nell'ambiente di esecuzione.

---

### Avvio locale dell'API

Installare le dipendenze:

```powershell
pip install -r requirements.txt
```

Avviare FastAPI:

```powershell
uvicorn main:app --reload
```

L'API sarà disponibile all'indirizzo:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Metriche Prometheus:

```text
http://127.0.0.1:8000/metrics
```

Eseguire alcune chiamate a:

```http
POST /predict
```

per generare dati nelle metriche.

Esempio:

```json
{
  "review": "This is terrible. I hate it."
}
```

---

### Configurazione Prometheus

Il file di configurazione si trova in:

```text
monitoring/prometheus/prometheus.yml
```

Contenuto:

```yaml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: "sentiment-analysis-api"

    metrics_path: /metrics

    static_configs:
      - targets:
          - "host.docker.internal:8000"
```

`host.docker.internal` permette al container Prometheus di raggiungere l'API FastAPI in esecuzione sull'host Windows.

Avviare Prometheus:

```powershell
docker run -d `
  --name prometheus `
  -p 9090:9090 `
  -v "${PWD}\monitoring\prometheus\prometheus.yml:/etc/prometheus/prometheus.yml" `
  prom/prometheus
```

Interfaccia Prometheus:

```text
http://localhost:9090
```

Per verificare che Prometheus riesca a raggiungere l'API:

```text
Status → Target health
```

Il target:

```text
sentiment-analysis-api
```

deve risultare:

```text
UP
```

---

### Query Prometheus utili

Numero totale di predizioni:

```promql
predictions_total
```

Numero totale di errori:

```promql
prediction_errors_total
```

Tempo medio cumulativo delle richieste `/predict`:

```promql
sum(http_request_duration_seconds_sum{endpoint="/predict"})
/
sum(http_request_duration_seconds_count{endpoint="/predict"})
```

Tempo medio recente:

```promql
sum(rate(http_request_duration_seconds_sum{endpoint="/predict"}[5m]))
/
sum(rate(http_request_duration_seconds_count{endpoint="/predict"}[5m]))
```

La query basata su `rate()` può restituire `NaN` se nella finestra temporale selezionata non sono presenti abbastanza richieste recenti.

---

### Avvio Grafana

Avviare Grafana tramite Docker:

```powershell
docker run -d `
  --name grafana `
  -p 3000:3000 `
  grafana/grafana
```

Grafana sarà disponibile all'indirizzo:

```text
http://localhost:3000
```

Al primo accesso utilizzare le credenziali iniziali:

```text
Username: admin
Password: admin
```

Grafana richiederà successivamente di impostare una nuova password.

---

### Collegamento Grafana → Prometheus

In Grafana aprire:

```text
Connections
→ Data sources
→ Add data source
→ Prometheus
```

Configurare l'URL:

```text
http://host.docker.internal:9090
```

Non utilizzare:

```text
http://localhost:9090
```

perché Grafana gira all'interno di un container e `localhost` indicherebbe il container Grafana stesso.

Premere:

```text
Save & test
```

La configurazione è corretta quando Grafana mostra:

```text
Successfully queried the Prometheus API.
```

---

### Problemi comuni

Se la porta `8000` risulta già occupata, verificare la presenza di un precedente container:

```powershell
docker ps
```

Se è ancora attivo il container dell'API:

```powershell
docker stop sentiment-analysis-api
```

Questo problema può verificarsi quando si tenta di avviare contemporaneamente FastAPI localmente e il container Docker sulla stessa porta.

Se `/metrics` restituisce:

```json
{
  "detail": "Not Found"
}
```

verificare quale processo sta realmente rispondendo sulla porta `8000`. È possibile che sia ancora attivo un vecchio container Docker che contiene una versione precedente dell'applicazione.

### Dashboard Grafana

È stata realizzata la dashboard:

```text
Sentiment Analysis Monitoring
```

La dashboard contiene i seguenti pannelli.

#### Predizioni per sentiment

Visualizza il numero di predizioni suddivise per classe:

```promql
sum by (sentiment) (predictions_total)
```

Visualizzazione utilizzata: `Pie chart`.

#### Errori di predizione

Visualizza il numero totale di errori verificatisi durante l'inferenza del modello:

```promql
sum(prediction_errors_total)
```

Visualizzazione utilizzata: `Stat`.

#### Tempo medio di risposta di `/predict`

Visualizza il tempo medio necessario per elaborare una richiesta di predizione:

```promql
1000 *
sum(http_request_duration_seconds_sum{endpoint="/predict"})
/
sum(http_request_duration_seconds_count{endpoint="/predict"})
```

Il risultato è espresso in millisecondi.

Visualizzazione utilizzata: `Stat`.

#### Utilizzo CPU dell'API

```promql
100 * rate(process_cpu_seconds_total[1m])
```

Il valore rappresenta l'utilizzo recente della CPU da parte del processo Python.

#### Memoria utilizzata dall'API

```promql
process_resident_memory_bytes / 1024 / 1024
```

Il risultato è espresso in MiB.

### Persistenza della dashboard

La configurazione esportata della dashboard Grafana è versionata nel repository:

```text
monitoring/grafana/dashboards/sentiment-analysis-monitoring.json
```