def group_by_key_value(input_list, key_to_group_by):
    """
    Groups a list of dictionaries by the values of a certain key (`key_to_group_by`)

    Examples:
        >>> my_list [
            {"a": "a1", "b": "b1"}, {"a": "a1", "b": "b2"}, {"a": "a2", "b": "b3"}
        ]
        >>> group_by_key_value(my_list, "a")
        {
            "a1": [{"a": "a1", "b": "b1"}, {"a": "a1", "b": "b2"}],
            "a2": [{"a": "a2", "b": "b3"}]
        }
    """

    grouped_dict = {}

    for d in input_list:
        value_to_group_by = d[key_to_group_by]
        if value_to_group_by not in grouped_dict:
            grouped_dict[value_to_group_by] = []
        grouped_dict[value_to_group_by].append(d)

    return grouped_dict
