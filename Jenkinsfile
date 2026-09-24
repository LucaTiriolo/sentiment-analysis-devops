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