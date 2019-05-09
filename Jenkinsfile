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

        stage 'Project tests', {
            try {
                parallel([
                    'Project tests (PY2)': {
                        withCommitStatus({
                            sh "make IMAGE_TAG=${commit} NO_BUILD=y ci-test-py2"
                        }, 'project-tests/py2', commit)
                    },
                    'Project tests (PY3)': {
                        withCommitStatus({
                            sh "make IMAGE_TAG=${commit} NO_BUILD=y ci-test-py3"
                        }, 'project-tests/py3', commit)
                    },
                    'Test run evaluation (PY2)': {
                        withCommitStatus({
                            sh "make IMAGE_TAG=${commit} NO_BUILD=y ci-run-evaluation-py2"
                        }, 'run-evaluation/py2', commit)
                    },
                    'Test run evaluation (PY3)': {
                        withCommitStatus({
                            sh "make IMAGE_TAG=${commit} NO_BUILD=y ci-run-evaluation-py3"
                        }, 'run-evaluation/py3', commit)
                    }
                ])
            } finally {
                sh 'make ci-clean'
            }
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
