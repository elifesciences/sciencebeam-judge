from sciencebeam_judge.utils.misc import normalize_person_name


class TestNormalizePersonName:
    def test_should_remove_space_between_initials(self):
        assert normalize_person_name('A M Smith') == 'AM Smith'

    def test_should_not_remove_space_between_full_name(self):
        assert normalize_person_name('A Middle Smith') == 'A Middle Smith'

    def test_should_remove_dot_after_single_initial(self):
        assert normalize_person_name('A. Smith') == 'A Smith'

    def test_should_replace_dot_with_space_after_single_initial_without_space(self):
        assert normalize_person_name('A.Smith') == 'A Smith'

    def test_should_remove_dot_after_initials(self):
        assert normalize_person_name('A. M. Smith') == 'AM Smith'

    def test_should_remove_dot_after_multiple_initials(self):
        assert normalize_person_name('A. M. X. Smith') == 'AMX Smith'

    def test_should_remove_dot_after_initials_only(self):
        assert normalize_person_name('A. M.') == 'AM'
