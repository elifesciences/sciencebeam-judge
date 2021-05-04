from sciencebeam_judge.utils.fuzzy import (
    StringView,
    translate_string_view_matching_blocks
)


class TestTranslateStringViewMatchingBlocks:
    def test_should_translate_index_with_masked_characters_outside_matched_text(self):
        a = 'x x abc x'
        b = 'y abc y y'
        a_string_view = StringView(a, [not c.isspace() for c in a])
        b_string_view = StringView(b, [not c.isspace() for c in b])
        assert str(a_string_view) == 'xxabcx'
        assert str(b_string_view) == 'yabcyy'
        result = translate_string_view_matching_blocks(
            [(2, 1, 3)], a_string_view=a_string_view, b_string_view=b_string_view
        )
        assert list(result) == [(4, 2, 3)]

    def test_should_translate_index_with_masked_characters_in_second_value(self):
        a = 'x x abc x'
        b = 'y a b c y y'
        a_string_view = StringView(a, [not c.isspace() for c in a])
        b_string_view = StringView(b, [not c.isspace() for c in b])
        assert str(a_string_view) == 'xxabcx'
        assert str(b_string_view) == 'yabcyy'
        result = translate_string_view_matching_blocks(
            [(2, 1, 3)], a_string_view=a_string_view, b_string_view=b_string_view
        )
        assert list(result) == [(4, 2, 1), (5, 4, 1), (6, 6, 1)]
