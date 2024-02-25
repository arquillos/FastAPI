def test_add_three():
    assert 2 + 3 + 1 == 6


def test_dict_contains():
    my_dict = {"a": 1, "b": 2}

    expected = {"a": 1}

    assert expected.items() <= my_dict.items()
