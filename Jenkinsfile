elifePipeline {
    node('containers-jenkins-plugin') {
        def commit

        stage 'Checkout', {
            checkout scm
            commit = elifeGitRevision()
        }

        stage 'Build images', {
            checkout scm
            dockerComposeBuild(commit)
        }

        stage 'Project tests (PY2)', {
            dockerComposeRun(
                "sciencebeam-judge-dev",
                "./project_tests.sh",
                commit
            )
        }

        stage 'Project tests (PY3)', {
            dockerComposeRun(
                "sciencebeam-judge-dev-py3",
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

        stage 'Revert temporary git changes', {
            sh "git checkout ."
        }

        elifeMainlineOnly {
            stage 'Merge to master', {
                elifeGitMoveToBranch commit, 'master'
            }

            stage 'Push unstable image', {
                def image = DockerImage.elifesciences(this, 'sciencebeam-judge', commit)
                def unstable_image = image.addSuffixAndTag('_unstable', commit)
                unstable_image.tag('latest').push()
                unstable_image.push()
            }

            stage 'Push unstable jupyter image', {
                def image = DockerImage.elifesciences(this, 'sciencebeam-judge-jupyter', commit)
                def unstable_image = image.addSuffixAndTag('_unstable', commit)
                unstable_image.tag('latest').push()
                unstable_image.push()
            }
        }
    }
}
