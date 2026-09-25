pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    // Jenkins esegue normalmente un checkout automatico.
    // Lo disabilitiamo perché vogliamo mostrarlo esplicitamente come stage.
    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                bat '''
                    py -3.14 --version
                    py -3.14 -m venv .venv-jenkins
                    .venv-jenkins\\Scripts\\python.exe -m pip install --upgrade pip
                    .venv-jenkins\\Scripts\\python.exe -m pip install -r requirements.txt
                '''
            }
        }

        stage('Unit Test') {
            steps {
                bat '''
                    .venv-jenkins\\Scripts\\python.exe -m pytest test\\unit
                '''
            }
        }

        stage('Integration Test') {
            steps {
                bat '''
                    .venv-jenkins\\Scripts\\python.exe -m pytest test\\integration
                '''
            }
        }

       stage('Docker Compose Build') {
            steps {
                bat '''
                    docker compose build
                '''
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                    docker compose up -d --remove-orphans
                '''
            }
        }

        stage('Health Check') {
            steps {
                powershell '''
                    $maxAttempts = 10
                    $delaySeconds = 2

                    # -----------------------------
                    # FastAPI
                    # -----------------------------
                    $apiHealthy = $false

                    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
                        try {
                            Write-Host "FastAPI health check - tentativo $attempt/$maxAttempts"

                            $response = Invoke-RestMethod `
                                -Uri "http://localhost:8000/health" `
                                -TimeoutSec 5

                            if ($response.status -eq "ok") {
                                Write-Host "FastAPI pronta"
                                $apiHealthy = $true
                                break
                            }
                        }
                        catch {
                            Write-Host "FastAPI non ancora disponibile: $($_.Exception.Message)"
                        }

                        if ($attempt -lt $maxAttempts) {
                            Start-Sleep -Seconds $delaySeconds
                        }
                    }

                    if (-not $apiHealthy) {
                        throw "Health check FastAPI fallito"
                    }


                    # -----------------------------
                    # Prometheus
                    # -----------------------------
                    $prometheusHealthy = $false

                    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
                        try {
                            Write-Host "Prometheus health check - tentativo $attempt/$maxAttempts"

                            $response = Invoke-WebRequest `
                                -Uri "http://localhost:9090/-/ready" `
                                -UseBasicParsing `
                                -TimeoutSec 5

                            if ($response.StatusCode -eq 200) {
                                Write-Host "Prometheus pronto"
                                $prometheusHealthy = $true
                                break
                            }
                        }
                        catch {
                            Write-Host "Prometheus non ancora disponibile: $($_.Exception.Message)"
                        }

                        if ($attempt -lt $maxAttempts) {
                            Start-Sleep -Seconds $delaySeconds
                        }
                    }

                    if (-not $prometheusHealthy) {
                        throw "Health check Prometheus fallito"
                    }


                    # -----------------------------
                    # Grafana
                    # -----------------------------
                    $grafanaHealthy = $false

                    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
                        try {
                            Write-Host "Grafana health check - tentativo $attempt/$maxAttempts"

                            $response = Invoke-RestMethod `
                                -Uri "http://localhost:3000/api/health" `
                                -TimeoutSec 5

                            if ($response.database -eq "ok") {
                                Write-Host "Grafana pronta"
                                $grafanaHealthy = $true
                                break
                            }
                        }
                        catch {
                            Write-Host "Grafana non ancora disponibile: $($_.Exception.Message)"
                        }

                        if ($attempt -lt $maxAttempts) {
                            Start-Sleep -Seconds $delaySeconds
                        }
                    }

                    if (-not $grafanaHealthy) {
                        throw "Health check Grafana fallito"
                    }

                    Write-Host "Health check completato: intero stack operativo"
                '''
            }
        }
    }

    post {
        success {
            emailext(
                subject: "SUCCESS - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    La pipeline Jenkins è terminata con successo.

                    Job: ${env.JOB_NAME}
                    Build: #${env.BUILD_NUMBER}
                    Stato: SUCCESS

                    URL build:
                    ${env.BUILD_URL}
                """,
                to: 'luca.tiriolo@gmail.com'
            )
        }

        failure {
            emailext(
                subject: "FAILURE - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    La pipeline Jenkins è fallita.

                    Job: ${env.JOB_NAME}
                    Build: #${env.BUILD_NUMBER}
                    Stato: FAILURE

                    Controllare i log:
                    ${env.BUILD_URL}
                """,
                to: 'luca.tiriolo@gmail.com'
            )
        }
    }
}