pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    // Jenkins esegue normalmente un checkout automatico.
    // Lo disabilitiamo perché vogliamo mostrarlo esplicitamente come stage.
    options {
        skipDefaultCheckout(true)
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
                    python --version
                    python -m venv .venv-jenkins
                    .venv-jenkins\\Scripts\\python.exe -m pip install --upgrade pip
                    .venv-jenkins\\Scripts\\python.exe -m pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                bat '''
                    .venv-jenkins\\Scripts\\python.exe -m pytest
                '''
            }
        }

        stage('Docker Build') {
            steps {
                bat '''
                    docker build -t sentiment-analysis-devops:%BUILD_NUMBER% .
                '''
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                    docker rm -f sentiment-analysis-api >nul 2>&1 || echo Container precedente non presente
                    docker run -d --name sentiment-analysis-api -p 8000:8000 sentiment-analysis-devops:%BUILD_NUMBER%
                '''
            }
        }

        stage('Health Check') {
            steps {
                powershell '''
                    Start-Sleep -Seconds 3

                    $response = Invoke-RestMethod -Uri "http://localhost:8000/health"

                    if ($response.status -ne "ok") {
                        throw "Health check fallito"
                    }

                    Write-Host "Health check completato: applicazione attiva"
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