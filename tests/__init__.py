def _merge_dicts(a, b, path=None):
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                _merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass
            else:
                if a[key] is None:
                    a[key] = b[key]
                if b[key] is None:
                    b[key] = a[key]
        else:
            a[key] = b[key]
    return a


def _convert_outline_item(outline_item):
    """Convert an outline item.

    The following input:
    ```
    ["1", "a", "i."]
    ```

    Is converted into the following output:
    ```
    {
        "1": {
            "a": {
                "i.": None
            }
        }
    }
    ```
    """
    if len(outline_item) == 1:
        return {outline_item[0]: None}
    else:
        node, remainder = outline_item[0], outline_item[1:]
        return {node: _convert_outline_item(remainder)}


def _convert_outline(outline_as_tuples):
    """Convert an outline as tuples into a tree format.

    Given the following input:

    ```
    [
        ["1", "a", "i."],
        ["1", "a", "ii."],
        ["1", "b", "i."],
        ["2"],
        ["3", "a"]
    ]
    ```

    Generate the following output (all leaves are encoded as None):

    ```
    {"1": {"a": {"i.": None, "ii.": None}, "b": {"i.": None}}, "2": None, "3": None}
    ```
    """
    tree = dict()
    for item in outline_as_tuples:
        tree = _merge_dicts(tree, _convert_outline_item(item))
    return tree
