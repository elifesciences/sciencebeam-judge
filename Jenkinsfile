elifePipeline {
    node('containers-jenkins-plugin') {
        def commit
        def version

        stage 'Checkout', {
            checkout scm
            commit = elifeGitRevision()
            if (env.TAG_NAME) {
                version = env.TAG_NAME - 'v'
            } else {
                version = 'develop'
            }
        }

        stage 'Build images', {
            checkout scm
            dockerComposeBuild(commit)
        }

        stage 'Project tests', {
            try {
                parallel([
                    'Project tests (PY3)': {
                        withCommitStatus({
                            sh "make IMAGE_TAG=${commit} NO_BUILD=y ci-test"
                        }, 'project-tests/py3', commit)
                    },
                    'Test run evaluation (PY3)': {
                        withCommitStatus({
                            sh "make IMAGE_TAG=${commit} NO_BUILD=y ci-test-run-evaluation"
                        }, 'project-tests/evaluate', commit)
                    },
                    'Test evaluate and update notebooks': {
                        // this will current cause evaluation results to be updated in the working dir
                        withCommitStatus({
                            sh "make IMAGE_TAG=${commit} NO_BUILD=y ci-test-evaluate-and-update-notebooks"
                        }, 'project-tests/evaluate-and-update-notebooks', commit)
                    }
                ])
            } finally {
                sh 'make ci-clean'
            }
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

        elifeTagOnly { repoTag ->
            stage 'Push stable sciencebeam-judge image', {
                def image = DockerImage.elifesciences(this, 'sciencebeam-judge', commit)
                image.tag('latest').push()
                image.tag(version).push()
            }

            stage 'Push stable sciencebeam-judge-jupyter image', {
                def image = DockerImage.elifesciences(this, 'sciencebeam-judge-jupyter', commit)
                image.tag('latest').push()
                image.tag(version).push()
            }
        }
    }
}
