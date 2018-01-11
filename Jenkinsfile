elifeLibrary {
    stage 'Checkout', {
        checkout scm
    }

    stage 'Build image', {
        sh 'docker build -t elife/sciencebeam-judge .'
    }

    stage 'Run tests', {
        elifeLocalTests './project_tests.sh'
    }
}
