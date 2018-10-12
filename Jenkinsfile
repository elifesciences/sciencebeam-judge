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
                "sciencebeam-judge",
                "./project_tests.sh",
                commit
            )
        }
    }
}
