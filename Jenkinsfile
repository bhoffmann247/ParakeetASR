import groovy.json.JsonSlurper

String SERVICE_DOCKER_IMAGE_NAME = 'parakeetasr'
String NEXUS_DOCKER_HOST = 'nexus-docker.shared.intouchcx.cloud'
String CLEAN_VERSION_NUMBER = ''
String VERSION_NUMBER = ''
def webServerImage
String kustomizationPath = ''
boolean deployOnly = false
boolean processForDeploy = false
boolean slackNotificationThreadExists = false
boolean performDeploy = false
boolean confirmPerformDeploy = false
String deploymentCluster = ''
String serviceDeploymentToMonitor = 'deployment/parakeetasr'
String deploymentNamespace = ''
String deploymentRegion = ''
def slackResponse
String BRANCH_RELEASENOTES = ''
String BRANCH_AUTHOR = ''
String CLEAN_BRANCH = ''

pipeline {
  agent {
    kubernetes {
      cloud 'k8s-nonprod-ca'
      inheritFrom 'jenkins-worker-default'
      yamlFile 'buildAgent.yaml'
    }
  }

  options {
    parallelsAlwaysFailFast()
    skipStagesAfterUnstable()
  }

  stages {
    stage('Build Branch')
    {
        when {
            not {
                branch 'master'
            }
        }
        steps {
            script {
                CLEAN_BRANCH = "${BRANCH_NAME}"
                CLEAN_BRANCH = CLEAN_BRANCH.replaceAll("feature", "")
                CLEAN_BRANCH = CLEAN_BRANCH.replaceAll("release", "")
                CLEAN_BRANCH = CLEAN_BRANCH.replaceAll("hotfix", "")
                CLEAN_BRANCH = CLEAN_BRANCH.replaceAll("[^a-zA-Z0-9]", "")

                echo "${CLEAN_BRANCH}"
            }
        }
    }
    stage('Rerun Check') {
      when {
        allOf {
            not {
                branch 'master'
            }
            triggeredBy 'UserIdCause'
        }
      }
      steps {
        script {
          try {
            deployOnly = true
            def url = "https://${NEXUS_DOCKER_HOST}/v2/${SERVICE_DOCKER_IMAGE_NAME}/tags/list"
            def payload = httpRequest url: "${url}", wrapAsMultipart: false
            def json = new groovy.json.JsonSlurperClassic().parseText(payload.content)
            def tags = json.tags            

            def filteredTags = tags.findAll {
              it.contains("${CLEAN_BRANCH}")
            }
            filteredTags = filteredTags.reverse()
            timeout(time: 2, unit: 'MINUTES') {
              def userInput = input id: 'ImageSelect', message: 'Use existing image and skip rebuilding(build/test/tag stages)?', ok: 'Select', parameters: [choice(choices: filteredTags, description: 'List of versions already built in Nexus', name: 'Versions')]
              echo "${userInput}"
              VERSION_NUMBER = userInput
              currentBuild.displayName = "${VERSION_NUMBER} [Manual Run]"
            }
          } catch (err) {
            echo "${err}"
            deployOnly = false
          }
        }
      }
    }
    stage('Pre Build') {
      when {
        not {
          expression {
            return deployOnly
          }
        }
      }
      stages {
        stage('Gather Branch Information') {
          steps {
            script {
              def changeLogSets = currentBuild.changeSets
              def authors = []

              for (int i = 0; i < changeLogSets.size(); i++) {
                def entries = changeLogSets[i].items
                for (int j = 0; j < entries.length; j++) {
                  def entry = entries[j]

                  authors.add(entry.author)
                  BRANCH_RELEASENOTES += "\r ${entry.commitId} by ${entry.author} on ${new Date(entry.timestamp)}: ${entry.msg}"
                }
              }

              def authorsUnique = authors.unique(false)
              if (authorsUnique.size() <= 0) {
                authors.add("System")
              }

              if (BRANCH_RELEASENOTES == "") {
                BRANCH_RELEASENOTES = "System Operation"
              }

              for (int z = 0; z < authorsUnique.size(); z++) {
                BRANCH_AUTHOR += "${authorsUnique[z]}"

                if (z != authorsUnique.size() && authorsUnique.size() > 1) {
                  BRANCH_AUTHOR += ", "
                }
              }
            }
          }
        }
        // Assign version number based on deployment environment
        stage('Version') {
          steps {
            script {
              def versionatorResponse = httpRequest "http://versionator/version/parakeetasr?incrementMajor=false&incrementMinor=false&incrementPatch=true"
              def versionResponse = new JsonSlurper().parseText(versionatorResponse.content)

              CLEAN_VERSION_NUMBER = "${versionResponse.major}.${versionResponse.minor}.${versionResponse.patch}"
              VERSION_NUMBER = CLEAN_VERSION_NUMBER

              echo "Version Number: ${VERSION_NUMBER}"

              currentBuild.displayName = "${VERSION_NUMBER}"
            }
          }
        }

        //  Suffix based on environment
        stage('Version: Env. Suffix') {
          when {
            not {
              branch 'master'
            }
          }
          steps {
            script {
              VERSION_NUMBER = "${VERSION_NUMBER}-${CLEAN_BRANCH}"
              echo "Version Number: ${VERSION_NUMBER}"

              currentBuild.displayName = "${VERSION_NUMBER}"
            }
          }
        }

        stage('Send Slack Notifications') {
          when {
            anyOf {
              branch 'master';
              branch 'develop'
            }
          }
          steps {
            script {
              slackResponse = slackSend botUser: true, channel: '#crossbow-monitoring', color: 'good', message: "Build Started :: ${SERVICE_DOCKER_IMAGE_NAME} :: Version Number: ${VERSION_NUMBER} :: Author(s): ${BRANCH_AUTHOR}", notifyCommitters: true, teamDomain: '24-7intouch', tokenCredentialId: 'Slack_247intouch_superpunch_bot'
              slackNotificationThreadExists = true
            }
          }
        }
      }
    }
    stage('Build') {
      when {
        not {
          expression {
            return deployOnly
          }
        }
      }
      stages {
        stage('Web Service') {
          steps {
            container('docker') {
              echo "Building webservice.."
              script {
                docker.withRegistry("https://${NEXUS_DOCKER_HOST}", "nexus") {
                  webServerImage = docker.build("${SERVICE_DOCKER_IMAGE_NAME}", "-f Dockerfile .")
                  webServerImage.push()
                }
              }
            }
          }
        }
      }
    }

    stage('Tag image') {
      when {
        not {
          expression {
            return deployOnly
          }
        }
      }
      parallel {
        stage('Latest') {
          steps {
            container('docker') {
              echo "Pushing latest tag.."
              script {
                docker.withRegistry("https://${NEXUS_DOCKER_HOST}", "nexus") {
                  webServerImage.push 'latest'
                }
              }
            }
          }
        }
        stage('Version Number') {
          steps {
            container('docker') {
              echo "Pushing latest tag.."
              script {
                docker.withRegistry("https://${NEXUS_DOCKER_HOST}", "nexus") {
                  webServerImage.push "${VERSION_NUMBER}"
                }
              }
            }
          }
        }
        stage('Develop/Master') {
          when {
            anyOf {
              branch 'master'
              branch 'develop'
            }
          }
          steps {
            container('docker') {
              echo "Pushing branch tag.."
              script {
                docker.withRegistry("https://${NEXUS_DOCKER_HOST}", "nexus") {
                  webServerImage.push "${BRANCH_NAME}"
                }
              }
            }
          }
        }
      }
    }

    stage('Prepare Feature Branch for Deploy Check') {
      when {
        not {
          anyOf {
            branch 'master'
            branch 'develop'
          }
        }
      }
      steps {
        script {
          try {
            timeout(time: 5, unit: 'MINUTES') {
              def approver = input message: "**WARNING: ONLY APPROVE THIS FOR QA DEPLOYMENTS**\nConfirm Deployment preperation of ${VERSION_NUMBER} to Development Environment", ok: 'Confirm Prepare', submitterParameter: 'deployPrepareApprover'
              processForDeploy = true

              echo "Deployment Prepare for ${VERSION_NUMBER} - approved by ${approver}"
            }
          } catch (err) {
            processForDeploy = false
          }
        }
      }
    }

    stage('Pre-Deploy') {
      parallel {
        stage('Development') {
          when {
            anyOf {
              branch 'develop'
              expression {
                return processForDeploy
              }
            }
          }
          steps {
            echo 'Preparing sensitive value replacements'
            script {
              performDeploy = true
              kustomizationPath = "deployment/overlays/development"
              deploymentCluster = "k8s-nonprod-ca"
              deploymentNamespace = "development"
              deploymentRegion = 'ca-central-1'
            }
          }
        }

        stage('Master') {
          when {
            branch 'master'
          }
          steps {
            echo 'Preparing sensitive value replacements'
            script {
              performDeploy = true
              kustomizationPath = "deployment/overlays/production"
              deploymentCluster = "k8s-shared-services-ca"
              deploymentNamespace = "service"
              deploymentRegion = 'ca-central-1'

            }
          }
        }
      }
    }

    stage('Deploy Security Check') {
      when {
        expression {
          return performDeploy
        }
      }
      steps {
        script {
          try {
            if (slackNotificationThreadExists) {
              slackSend botUser: true, channel: slackResponse.threadId, color: 'warning', message: "<!here> Build Deployment Approval Required :: ${SERVICE_DOCKER_IMAGE_NAME} :: ${deploymentCluster} - ${deploymentNamespace} - ${kustomizationPath} - Version Number: ${VERSION_NUMBER} \r ${RUN_DISPLAY_URL}", teamDomain: '24-7intouch', tokenCredentialId: 'Slack_247intouch_superpunch_bot'
            }

            timeout(time: 5, unit: 'MINUTES') {
              def approver = input message: "Confirm Deployment to ${deploymentCluster} - ${deploymentNamespace} - ${kustomizationPath}", ok: 'Deploy', submitterParameter: 'deployApprover'
              confirmPerformDeploy = true

              echo "Deployment ${deploymentCluster} - ${deploymentNamespace} - ${kustomizationPath} approved by ${approver}"
              if (slackNotificationThreadExists) {
                slackSend botUser: true, channel: slackResponse.threadId, color: 'good', message: "Build Deployment Approved :: ${SERVICE_DOCKER_IMAGE_NAME} :: ${deploymentCluster} - ${deploymentNamespace} - ${kustomizationPath} - Version Number: ${VERSION_NUMBER} :: approved by ${approver}", teamDomain: '24-7intouch', tokenCredentialId: 'Slack_247intouch_superpunch_bot'
              } else {
                slackResponse = slackSend botUser: true, channel: '#crossbow-monitoring', color: 'good', message: "Feature Branch Build Deployment Approved :: ${SERVICE_DOCKER_IMAGE_NAME} :: ${deploymentCluster} - ${deploymentNamespace} - ${kustomizationPath} - Version Number: ${VERSION_NUMBER} :: approved by ${approver}", teamDomain: '24-7intouch', tokenCredentialId: 'Slack_247intouch_superpunch_bot'
              }
            }
          } catch (err) {
            confirmPerformDeploy = false

            if (slackNotificationThreadExists) {
              slackSend botUser: true, channel: slackResponse.threadId, color: 'warning', message: "Build Deploymeny Declined (Deployment skipped) :: ${SERVICE_DOCKER_IMAGE_NAME} :: ${deploymentCluster} - ${deploymentNamespace} - ${kustomizationPath} - Version Number: ${VERSION_NUMBER}", teamDomain: '24-7intouch', tokenCredentialId: 'Slack_247intouch_superpunch_bot'
            }

            echo "Deploymeny Declined (Deployment skipped): ${deploymentCluster} - ${deploymentNamespace} - ${kustomizationPath}"
          }
        }
      }
    }
    stage('Deploy') {
      when {
        expression {
          return confirmPerformDeploy
        }
      }
      steps {
        container('kubectl') {
          sh script: "aws eks update-kubeconfig --name ${deploymentCluster} --region ${deploymentRegion}", label: "Switch to ${deploymentCluster}"

          echo "Update image to match current build tag ${VERSION_NUMBER}"
          sh "sed -i 's/{IMAGE-TAG}/${VERSION_NUMBER}/g' deployment/base/kustomization.yaml"

          echo "Applying kustomize from ${kustomizationPath}"

          sh script: "kubectl apply -k ${kustomizationPath}", label: 'kubectl apply'
          sh script: "kubectl rollout status ${serviceDeploymentToMonitor} -n ${deploymentNamespace} --timeout 15m", label: 'monitor service release'
        }
      }
      post {
        success {
          script {
            currentBuild.displayName = "[D] " + currentBuild.displayName
            if (slackNotificationThreadExists || processForDeploy) {
              slackSend botUser: true, channel: slackResponse.threadId, color: 'good', message: "${serviceDeploymentToMonitor} DEPLOY SUCCESS :: ${SERVICE_DOCKER_IMAGE_NAME} :: ${deploymentCluster} - ${deploymentNamespace} - ${VERSION_NUMBER}", teamDomain: '24-7intouch', tokenCredentialId: 'Slack_247intouch_superpunch_bot'
            }
          }
        }
        failure {
          container('kubectl') {
            script {
              if (slackNotificationThreadExists || processForDeploy) {
                slackSend botUser: true, channel: slackResponse.threadId, color: 'danger', message: "<!here> ${serviceDeploymentToMonitor} DEPLOY FAILED :: ${SERVICE_DOCKER_IMAGE_NAME} :: ${deploymentCluster} - ${deploymentNamespace} - ${VERSION_NUMBER} \r Rolling back to last stable deployment.", teamDomain: '24-7intouch', tokenCredentialId: 'Slack_247intouch_superpunch_bot'
              }
            }

            sh script: "kubectl rollout undo ${serviceDeploymentToMonitor} -n ${deploymentNamespace}", label: 'rollback service release'
          }
        }
      }
    }
  }
  post {
    success {
      script {
        if (env.BRANCH_NAME == 'master' || env.BRANCH_NAME == 'develop') {
          committerEmail = sh(
            script: 'git --no-pager show -s --format=\'%ae\'',
            returnStdout: true
          ).trim()

          name = committerEmail.substring(0, committerEmail.lastIndexOf("@"));

          if (slackNotificationThreadExists) {
            slackSend botUser: true, channel: slackResponse.threadId, color: 'good', message: "Build Success :: ${SERVICE_DOCKER_IMAGE_NAME} :: Version Number: ${VERSION_NUMBER} \r Changes: ${BRANCH_RELEASENOTES} \r ${RUN_CHANGES_DISPLAY_URL}", teamDomain: '24-7intouch', tokenCredentialId: 'Slack_247intouch_superpunch_bot'
          }
        }
      }
    }
    failure {
      script {
        if (env.BRANCH_NAME == 'master' || env.BRANCH_NAME == 'develop') {
          committerEmail = sh(
            script: 'git --no-pager show -s --format=\'%ae\'',
            returnStdout: true
          ).trim()

          name = committerEmail.substring(0, committerEmail.lastIndexOf("@"));

          if (slackNotificationThreadExists) {
            slackSend botUser: true, replyBroadcast: true, channel: slackResponse.threadId, color: 'danger', message: "Build Failure :: ${SERVICE_DOCKER_IMAGE_NAME} :: Version Number: ${VERSION_NUMBER}", teamDomain: '24-7intouch', tokenCredentialId: 'Slack_247intouch_superpunch_bot'
            slackResponse.addReaction("face_with_cowboy_hat")
          }
        }
      }
    }
  }
}