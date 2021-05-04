import sciencebeam_alignment.align


class TestScienceBeamAlignment:
    def test_should_use_native_implementation(self):
        assert sciencebeam_alignment.align.native_enabled is True
