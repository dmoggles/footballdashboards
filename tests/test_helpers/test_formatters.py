class TestFormatters:
    def test_player_name_first_initial_surname_formatter(self):
        from footballdashboards.helpers.formatters import (
            player_name_first_initial_surname_formatter,
        )

        assert player_name_first_initial_surname_formatter("John Smith") == "J Smith"
        assert player_name_first_initial_surname_formatter("jonn smith") == "J Smith"
        assert player_name_first_initial_surname_formatter("john") == "John"
        assert player_name_first_initial_surname_formatter("John") == "John"
        assert player_name_first_initial_surname_formatter(None) is None
        assert player_name_first_initial_surname_formatter("John Smith Jones") == "J Jones"
