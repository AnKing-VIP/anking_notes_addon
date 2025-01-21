from src.anking_notetypes.notetype_setting import order_names


class TestOrderNames:
    def test_basic(self):
        assert order_names(
            new_names=[
                "Lecture Notes",
                "Boards and Beyond",
                "Boards and Beyond Links",
                "First Aid",
                "First Aid Links",
                "Extra",
                "Missed Questions",
            ],
            current_names=[
                "Extra",
                "First Aid",
                "Missed Questions",
                "Boards and Beyond",
            ],
        ) == [
            # We are keeping the order of the current names and adding the new names which are missing
            # after related current names (matching by their first word) if any matches exist,
            # otherwise at the end.
            "Extra",
            "First Aid",
            "First Aid Links",
            "Missed Questions",
            "Boards and Beyond",
            "Boards and Beyond Links",
            "Lecture Notes",
        ]

    def test_with_multiple_first_word_matches(self):
        assert order_names(
            new_names=["Sketchy", "Sketchy 1", "Sketchy 2", "Extra"],
            current_names=["Sketchy", "Sketchy 1", "Extra"],
        ) == ["Sketchy", "Sketchy 1", "Sketchy 2", "Extra"]

    def test_no_matches(self):
        assert order_names(
            new_names=["Apple", "Banana"], current_names=["Cherry", "Date"]
        ) == ["Apple", "Banana"]
