import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc


def batch_duplicate_blocks_as_unique():
    preselected_ids = rs.SelectedObjects()
    block_ids = []

    if preselected_ids:
        block_ids = [obj_id for obj_id in preselected_ids if rs.IsBlockInstance(obj_id)]
        if not block_ids:
            rs.UnselectAllObjects()
            block_ids = rs.GetObjects("Select block instances of the SAME type to make unique", rs.filter.instance)
    else:
        block_ids = rs.GetObjects("Select block instances of the SAME type to make unique", rs.filter.instance)

    if not block_ids:
        print("No block instances selected.")
        return

    # every instance in the batch has to belong to the same block definition
    first_block_name = rs.BlockInstanceName(block_ids[0])

    for b_id in block_ids:
        current_name = rs.BlockInstanceName(b_id)
        if current_name != first_block_name:
            rs.MessageBox(
                "All selected blocks must be instances of the SAME definition.\n"
                "You selected instances of '{}' and '{}'.".format(first_block_name, current_name),
                0,
                "Batch Operation Failed"
            )
            return

    default_new_name = "{}_1".format(first_block_name)
    new_block_name = rs.StringBox(
        message="Enter name for the new unique block definition:",
        default_value=default_new_name,
        title="Batch Duplicate As Unique"
    )

    if not new_block_name or new_block_name.strip() == "":
        print("Cancelled - a new block name is required.")
        return

    if rs.IsBlock(new_block_name):
        rs.MessageBox("A block named '{}' already exists. Pick a different name.".format(new_block_name), 0, "Duplicate Block Error")
        return

    items = ("DeleteSelectedInstances", "No", "Yes"),
    defaults = (True,)
    boolean_options = rs.GetBoolean("Batch Options", items, defaults)
    if boolean_options is None:
        return
    should_delete = boolean_options[0]

    sub_object_ids = rs.BlockObjects(first_block_name)
    if not sub_object_ids:
        print("Couldn't read the source definition's geometry.")
        return

    geometry_list = []
    attributes_list = []

    for sub_id in sub_object_ids:
        obj = sc.doc.Objects.Find(sub_id)
        if obj:
            # duplicate both geometry and attributes to fully break the link
            # to the old definition - otherwise the new one would share
            # attribute references with the original objects
            geometry_list.append(obj.Geometry.Duplicate())
            attributes_list.append(obj.Attributes.Duplicate())

    w0 = Rhino.Geometry.Point3d(0, 0, 0)
    new_block_index = sc.doc.InstanceDefinitions.Add(new_block_name, "", w0, geometry_list, attributes_list)
    if new_block_index < 0:
        print("Failed to create the new block definition.")
        return

    rs.EnableRedraw(False)

    instance_count = 0
    skipped_count = 0
    for b_id in block_ids:
        xform = rs.BlockInstanceXform(b_id)

        if xform is None:
            skipped_count += 1
            continue

        new_instance_id = sc.doc.Objects.AddInstanceObject(new_block_index, xform)

        if new_instance_id:
            instance_count += 1
            if should_delete:
                rs.DeleteObject(b_id)

    rs.EnableRedraw(True)

    print("New block definition: '{}'".format(new_block_name))
    print("Instances replaced: {}".format(instance_count))
    print("Original instances deleted: {}".format(should_delete))
    if skipped_count:
        print("Skipped {} instance(s) - couldn't read their transform.".format(skipped_count))


if __name__ == "__main__":
    batch_duplicate_blocks_as_unique()
