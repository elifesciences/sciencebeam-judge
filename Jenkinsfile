elifeLibrary {
    def commit

    stage 'Checkout', {
        checkout scm
        commit = elifeGitRevision()
    }

    node('containers-jenkins-plugin') {
        stage 'Build images', {
            checkout scm
            dockerComposeBuild(commit)
        }

        stage 'Project tests', {
            dockerComposeRun(
                "sciencebeam-judge-dev",
                "./project_tests.sh",
                commit
            )
        }

        stage 'Test update evaluation results', {
            sh "bash ./update-example-data-results.sh"
        }

        stage 'Test update notebooks', {
            sh "bash ./update-example-data-notebooks.sh"
        }
    }

    elifeMainlineOnly {
        stage 'Merge to master', {
            elifeGitMoveToBranch commit, 'master'
        }
    }
}
