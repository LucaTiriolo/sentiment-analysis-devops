pipeline {
    agent any

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
    }

    post {
        success {
            echo 'Pipeline completata con successo.'
        }

        failure {
            echo 'Pipeline fallita.'
        }
    }
}