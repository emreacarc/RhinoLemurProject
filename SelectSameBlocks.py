import rhinoscriptsyntax as rs


def select_same_blocks():
    selected_objects = rs.SelectedObjects()
    if not selected_objects:
        print("Select at least one block instance first.")
        return

    target_block_names = set()
    for obj in selected_objects:
        if rs.IsBlockInstance(obj):
            target_block_names.add(rs.BlockInstanceName(obj))

    if not target_block_names:
        print("None of the selected objects are block instances.")
        return

    all_objects = rs.AllObjects()
    matching_blocks = []
    block_counts = {name: 0 for name in target_block_names}

    for obj in all_objects:
        if rs.IsBlockInstance(obj):
            current_name = rs.BlockInstanceName(obj)
            if current_name in target_block_names:
                matching_blocks.append(obj)
                block_counts[current_name] += 1

    if matching_blocks:
        rs.EnableRedraw(False)
        rs.UnselectAllObjects()
        rs.SelectObjects(matching_blocks)
        rs.EnableRedraw(True)

        print("Selection summary:")
        for name in sorted(target_block_names):
            print("  {0}: {1}".format(name, block_counts[name]))
        print("Total selected: {0}".format(len(matching_blocks)))
    else:
        print("No matching blocks found.")


if __name__ == "__main__":
    select_same_blocks()
