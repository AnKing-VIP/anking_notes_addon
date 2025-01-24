from src.anking_notetypes.notetype_setting import order_names


class TestOrderNames:
    def test_basic(self):
        assert order_names(
            new_names=[
                "Lecture Notes",
                "First Aid",
                "Extra",
                "First Aid Links",
            ],
            current_names=[
                "Extra",
                "First Aid",
            ],
        ) == [
            "Extra",
            "First Aid",
            "Lecture Notes",
            "First Aid Links",
        ]

    def test_no_matches(self):
        assert order_names(
            new_names=["Apple", "Banana"], current_names=["Cherry", "Date"]
        ) == ["Apple", "Banana"]
