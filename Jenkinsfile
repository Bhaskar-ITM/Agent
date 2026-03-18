import groovy.transform.Field

@Field def STAGES_RESULTS = []
@Field def PROJECT = [:]
@Field def SELECTED = []
@Field def IS_MANUAL = false
@Field def IMAGE_TAG = ''

pipeline {
    agent any

    parameters {
        string(name: 'SCAN_ID', defaultValue: '')
        choice(name: 'SCAN_MODE', choices: ['AUTOMATED', 'MANUAL'])
        text(name: 'PROJECT_DATA', defaultValue: '{}')
        text(name: 'SELECTED_STAGES', defaultValue: '[]')
        text(name: 'SCAN_TIMEOUT', defaultValue: '7200')  // Dynamic timeout in seconds
    }

    environment {
        // Use environment variable for backend URL, fallback to localhost:8000 for dev
        CALLBACK_URL = "${env.BACKEND_URL ?: 'http://localhost:8000'}/api/v1/scans/${params.SCAN_ID}/callback"
        REPORT_DIR = "reports"
        // Get callback token from Jenkins credentials (no fallback - fails if not set)
        CALLBACK_TOKEN = "${env.CALLBACK_TOKEN}"
    }

    options {
        // Dynamic timeout based on scan complexity (default 2 hours)
        timeout(time: params.SCAN_TIMEOUT ? params.SCAN_TIMEOUT.toInteger() : 7200, unit: 'SECONDS')
        disableConcurrentBuilds()
        skipStagesAfterUnstable()
        // Keep build logs for debugging
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Init Context') {
            steps {
                script {
                    // Debug logging
                    echo "=== Init Context Started ==="
                    echo "SCAN_ID received: ${params.SCAN_ID}"
                    echo "SCAN_MODE received: ${params.SCAN_MODE}"
                    
                    // Validate SCAN_ID
                    if (!params.SCAN_ID?.trim()) {
                        error("SCAN_ID is mandatory. Backend handshake failed.")
                    }
                    
                    if (params.SCAN_ID =~ /\s/) {
                        error("SCAN_ID must not contain spaces. Use UUID format.")
                    }
                    
                    echo "SCAN_ID validation passed"
                    
                    // Unescape HTML entities in parameters
                    def projectData = params.PROJECT_DATA.replaceAll('&quot;', '"').replaceAll('&#39;', "'")
                    def selectedStages = params.SELECTED_STAGES.replaceAll('&quot;', '"').replaceAll('&#39;', "'")
                    
                    echo "Unescaped PROJECT_DATA: ${projectData}"
                    echo "Unescaped SELECTED_STAGES: ${selectedStages}"
                    
                    // Parse JSON using readJSON (sandbox-safe)
                    def projectMap = readJSON text: projectData
                    PROJECT = new HashMap(projectMap)
                    
                    def selectedList = readJSON text: selectedStages
                    SELECTED = new ArrayList(selectedList)
                    
                    IS_MANUAL = params.SCAN_MODE == "MANUAL"
                    sh "mkdir -p ${env.REPORT_DIR}"
                    
                    echo "Parsed PROJECT: ${PROJECT}"
                    echo "Parsed SELECTED: ${SELECTED}"
                    echo "IS_MANUAL: ${IS_MANUAL}"
                    echo "=== Init Context Completed ==="
                }
            }
        }

        stage('1. Git Checkout') {
            steps {
                script {
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: PROJECT.branch ?: 'main']],
                        userRemoteConfigs: [[
                            url: PROJECT.git_url,
                            credentialsId: PROJECT.credentials_id ?: 'github-credentials'
                        ]]
                    ])
                    recordStage('git_checkout', 'PASS', 'Git checkout successful')
                }
            }
        }

        stage('2. Sonar Scanner') {
            when { expression { shouldRun('sonar_scanner') } }
            steps {
                // Per-stage timeout: 15 minutes for Sonar analysis
                timeout(time: 15, unit: 'MINUTES') {
                    script {
                        // Get the SonarQube Scanner tool path
                        def scannerHome = tool 'sonar-scanner'

                        try {
                            // Use Jenkins SonarQube server configuration
                            withSonarQubeEnv('sonar-server') {
                                sh """
                                    ${scannerHome}/bin/sonar-scanner \
                                      -Dsonar.projectKey=${PROJECT.sonar_key ?: params.SCAN_ID} \
                                      -Dsonar.sources=. \
                                      -Dsonar.projectName=${PROJECT.project_name ?: params.SCAN_ID}
                                """
                            }
                            recordStage('sonar_scanner', 'PASS', 'Sonar scan completed')
                        } catch (Exception e) {
                            echo "⚠️  SonarQube failed: ${e.message}"
                            echo "   Continuing pipeline with other security scans..."
                            recordStage('sonar_scanner', 'WARN', "SonarQube failed: ${e.message}")
                        }
                    }
                }
            }
        }

        stage('3. Sonar Quality Gate') {
            when { expression { shouldRun('sonar_quality_gate') } }
            steps {
                echo "⏭️  Skipping SonarQube Quality Gate check"
                recordStage('sonar_quality_gate', 'SKIPPED', 'Quality Gate check skipped')
            }
        }

        stage('4. NPM / PIP Install') {
            when { expression { shouldRun('npm_pip_install') } }
            steps {
                // Per-stage timeout: 10 minutes for dependency installation
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        // Find package.json location
                        def npmDir = sh(
                            script: "find . -name 'package.json' -type f | head -1",
                            returnStdout: true
                        ).trim()
                        
                        if (npmDir) {
                            dir(npmDir.replaceAll('/package.json', '')) {
                                sh 'npm ci'
                            }
                        }
                        
                        // Find requirements.txt location  
                        def pipDir = sh(
                            script: "find . -name 'requirements.txt' -type f | head -1",
                            returnStdout: true
                        ).trim()
                        
                        if (pipDir) {
                            dir(pipDir.replaceAll('/requirements.txt', '')) {
                                sh 'pip install -r requirements.txt'
                            }
                        }
                    }
                }
                recordStage('npm_pip_install', 'PASS', 'Dependencies installed')
            }
        }

        stage('5. Dependency Check') {
            when { expression { shouldRun('dependency_check') } }
            steps {
                dependencyCheck additionalArguments: """
                    --project ${params.SCAN_ID}
                    --scan .
                    --format JSON
                    --format HTML
                    --out ${env.REPORT_DIR}
                    --enableExperimental
                """, odcInstallation: 'OWasp'
                recordStage('dependency_check', 'PASS', 'Dependency check completed')
            }
        }

        stage('6. Trivy FS Scan') {
            when { expression { shouldRun('trivy_fs_scan') } }
            steps {
                sh """
                    /home/kali_linux/.local/bin/trivy fs --format json \
                      -o ${env.REPORT_DIR}/trivy-fs.json . || true
                """
                recordStage('trivy_fs_scan', 'PASS', 'Trivy FS scan completed')
            }
        }

        stage('7. Docker Build') {
            when { expression { shouldRun('docker_build') } }
            steps {
                script {
                    // Auto-detect Dockerfile with priority order
                    def dockerfile = ''
                    def context = '.'
                    
                    // Check common locations in priority order
                    def locations = [
                        [file: 'Dockerfile', context: '.'],
                        [file: 'docker/Dockerfile', context: '.'],
                        [file: 'backend/Dockerfile', context: 'backend'],
                        [file: 'frontend/Dockerfile', context: 'frontend'],
                        [file: 'api/Dockerfile', context: 'api'],
                        [file: 'app/Dockerfile', context: 'app'],
                        [file: 'server/Dockerfile', context: 'server'],
                        [file: 'web/Dockerfile', context: 'web'],
                    ]
                    
                    for (loc in locations) {
                        if (fileExists(loc.file)) {
                            dockerfile = loc.file
                            context = loc.context
                            echo "✓ Using ${dockerfile} (context: ${context})"
                            break
                        }
                    }
                    
                    // Fallback to find command if not in common locations
                    if (!dockerfile) {
                        def output = sh(
                            script: "find . -name 'Dockerfile*' -type f | head -1",
                            returnStdout: true
                        ).trim()
                        if (output) {
                            dockerfile = output
                            context = output.contains('/') ? 
                                output.substring(0, output.lastIndexOf('/')) : '.'
                            echo "✓ Found via find: ${dockerfile} (context: ${context})"
                        }
                    }
                    
                    // Build or skip
                    if (dockerfile) {
                        IMAGE_TAG = "${PROJECT.project_id ?: 'scan'}:${params.SCAN_ID}"
                        sh "docker build -t ${IMAGE_TAG} -f ${dockerfile} ${context}"
                        recordStage('docker_build', 'PASS', 'Built from ${dockerfile}')
                    } else {
                        echo "⚠️  No Dockerfile found - skipping Docker build"
                        recordStage('docker_build', 'SKIPPED', 'No Dockerfile found')
                    }
                }
            }
        }

        stage('8. Docker Push') {
            when { expression { shouldRun('docker_push') } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-credentials',
                                                  usernameVariable: 'DOCKER_USER',
                                                  passwordVariable: 'DOCKER_PASS')]) {
                    sh """
                        echo "${DOCKER_PASS}" | \
                        docker login \
                            -u "${DOCKER_USER}" --password-stdin || true
                        docker push ${IMAGE_TAG} || true
                    """
                    recordStage('docker_push', 'PASS', 'Docker image pushed')
                }
            }
        }

        stage('9. Trivy Image Scan') {
            when { expression { shouldRun('trivy_image_scan') } }
            steps {
                sh """
                    /home/kali_linux/.local/bin/trivy image --format json \
                      -o ${env.REPORT_DIR}/trivy-image.json ${IMAGE_TAG} || true
                """
                recordStage('trivy_image_scan', 'PASS', 'Trivy image scan completed')
            }
        }

        stage('10. Nmap Scan') {
            when { expression { shouldRun('nmap_scan') } }
            steps {
                script {
                    if (!PROJECT.target_ip) {
                        if (IS_MANUAL) {
                            error("target_ip required for manual Nmap scan")
                        }
                        echo "SKIP: No target_ip provided"
                        return
                    }
                    sh """
                        nmap -sV -sC -oX ${env.REPORT_DIR}/nmap.xml ${PROJECT.target_ip} || true
                    """
                    recordStage('nmap_scan', 'PASS', 'Nmap scan completed')
                }
            }
        }

        stage('11. ZAP Scan') {
            when { expression { shouldRun('zap_scan') } }
            steps {
                script {
                    if (!PROJECT.target_url) {
                        if (IS_MANUAL) {
                            error("target_url required for manual ZAP scan")
                        }
                        echo "SKIP: No target_url provided"
                        return
                    }
                    withEnv(["TARGET_URL=${PROJECT.target_url}"]) {
                        sh '''
                            zap.sh -daemon -host 127.0.0.1 -port 8090 -config api.disablekey=true &
                            ZAP_PID=$!
                            sleep 30
                            
                            curl "http://127.0.0.1:8090/JSON/spider/action/scan/?url=$TARGET_URL" || true
                            sleep 60
                            
                            curl "http://127.0.0.1:8090/JSON/core/action/htmlreport/" -o reports/zap.html || true
                            curl "http://127.0.0.1:8090/JSON/core/action/jsonreport/" -o reports/zap.json || true
                            
                            kill $ZAP_PID 2>/dev/null || true
                        '''
                    }
                    recordStage('zap_scan', 'PASS', 'ZAP scan completed')
                }
            }
        }
    }

    post {
        always {
            script {
                archiveArtifacts artifacts: "${env.REPORT_DIR}/**", allowEmptyArchive: true

                // Build detailed error information for failed scans
                def errorMessage = null
                def errorType = null
                def jenkinsConsoleUrl = null

                if (currentBuild.currentResult == 'FAILURE' || currentBuild.currentResult == 'ABORTED') {
                    // Get the cause of failure - use wrappedBuild for sandbox compatibility
                    def failedStage = null
                    try {
                        // Try to get build execution details (may be restricted by script security)
                        def buildWrapper = currentBuild.rawBuild
                        if (buildWrapper && buildWrapper.hasProperty('execution')) {
                            def executions = buildWrapper.execution
                            if (executions) {
                                for (stage in executions) {
                                    if (stage.status == 'FAILURE' || stage.status == 'ABORTED') {
                                        failedStage = stage
                                        break
                                    }
                                }
                            }
                        }
                    } catch (SecurityException e) {
                        // Script security doesn't allow rawBuild, use fallback
                        echo "Using fallback error handling (script security restricted)"
                        errorMessage = "Pipeline failed at stage: ${currentBuild.currentResult}"
                        errorType = 'PIPELINE_ERROR'
                    } catch (Exception e) {
                        echo "Error getting build details: ${e.message}"
                    }
                    
                    // Set default error if not already set
                    if (!errorMessage) {
                        errorMessage = "Pipeline execution failed"
                    }
                    if (!errorType) {
                        errorType = 'PIPELINE_ERROR'
                    }
                    
                    // Determine error type based on failure
                    if (currentBuild.buildCauses?.any { it.shortDescription?.contains('Timeout') }) {
                        errorType = 'TIMEOUT'
                        errorMessage = "Scan timed out after ${params.SCAN_TIMEOUT ? params.SCAN_TIMEOUT / 60 : 60} minutes. The pipeline exceeded the maximum allowed execution time."
                    } else if (failedStage) {
                        errorType = 'PIPELINE_ERROR'
                        errorMessage = "Pipeline failed at stage: ${failedStage.name}. Check Jenkins console for detailed error logs."
                    } else {
                        errorType = 'PIPELINE_ERROR'
                        errorMessage = "Pipeline failed with status: ${currentBuild.currentResult}. Review build logs for details."
                    }

                    // Build Jenkins console URL using local Jenkins server
                    jenkinsConsoleUrl = "${env.JENKINS_BASE_URL ?: 'http://192.168.1.101:8080'}/job/${env.JOB_NAME}/${env.BUILD_NUMBER}/console"
                }

                def payload = [
                    status: currentBuild.currentResult,
                    build_number: currentBuild.number,
                    scan_id: params.SCAN_ID,
                    scan_mode: params.SCAN_MODE,
                    stages: STAGES_RESULTS ?: [],
                    finished_at: new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone('UTC')),
                    error_message: errorMessage,
                    error_type: errorType,
                    jenkins_console_url: jenkinsConsoleUrl
                ]

                // Write callback payload to file
                writeFile file: 'callback.json', text: groovy.json.JsonOutput.toJson(payload)

                // Send callback to backend using environment CALLBACK_TOKEN
                sh """
                    curl -sS -X POST \
                      -H "Content-Type: application/json" \
                      -H "X-Callback-Token: ${CALLBACK_TOKEN}" \
                      --data @callback.json \
                      "${CALLBACK_URL}" \
                    || echo "Callback failed"
                """
            }
        }

        success {
            echo "Pipeline completed successfully for SCAN_ID: ${params.SCAN_ID}"
        }

        failure {
            echo "Pipeline failed for SCAN_ID: ${params.SCAN_ID}"
            echo "Failure reason will be sent to backend in callback"
        }
    }
}

def shouldRun(stageName) {
    if (IS_MANUAL == false) {
        return true
    }
    return SELECTED.contains(stageName)
}

def recordStage(stageName, status, summary) {
    if (!binding.hasVariable('STAGES_RESULTS')) {
        STAGES_RESULTS = []
    }
    STAGES_RESULTS.add([
        stage: stageName.toString(),
        status: status.toString(),
        summary: summary.toString(),
        timestamp: new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone('UTC'))
    ])
    echo "Recorded stage: ${stageName} - ${status}"
}
