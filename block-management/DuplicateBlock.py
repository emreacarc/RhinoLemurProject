import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc


def duplicate_block_as_unique():
    block_id = rs.GetObject("Select a block instance to duplicate as unique", rs.filter.instance, preselect=True)
    if not block_id:
        print("No block instance selected.")
        return

    source_block_name = rs.BlockInstanceName(block_id)
    if not source_block_name:
        print("Couldn't read the source block's name.")
        return

    default_new_name = "{}_1".format(source_block_name)
    new_block_name = rs.StringBox(
        message="Enter name for the new unique block:",
        default_value=default_new_name,
        title="Duplicate Block As Unique"
    )

    if not new_block_name or new_block_name.strip() == "":
        print("Cancelled - a new block name is required.")
        return

    if rs.IsBlock(new_block_name):
        rs.MessageBox("A block named '{}' already exists. Pick a different name.".format(new_block_name), 0, "Duplicate Block Error")
        return

    items = ("DeleteSelectedInstance", "No", "Yes"),
    defaults = (True,)
    boolean_options = rs.GetBoolean("Instance Options", items, defaults)
    if boolean_options is None:
        return
    should_delete = boolean_options[0]

    xform = rs.BlockInstanceXform(block_id)
    if xform is None:
        print("Couldn't read the instance's transform.")
        return

    sub_object_ids = rs.BlockObjects(source_block_name)
    if not sub_object_ids:
        print("Couldn't read the source block's geometry.")
        return

    geometry_list = []
    attributes_list = []

    for sub_id in sub_object_ids:
        obj = sc.doc.Objects.Find(sub_id)
        if obj:
            # duplicate both geometry and attributes so the new definition
            # doesn't end up sharing references with the original objects
            geometry_list.append(obj.Geometry.Duplicate())
            attributes_list.append(obj.Attributes.Duplicate())

    w0 = Rhino.Geometry.Point3d(0, 0, 0)
    new_block_index = sc.doc.InstanceDefinitions.Add(new_block_name, "", w0, geometry_list, attributes_list)
    if new_block_index < 0:
        print("Failed to create the new block definition.")
        return

    rs.EnableRedraw(False)
    new_instance_id = sc.doc.Objects.AddInstanceObject(new_block_index, xform)

    if should_delete and new_instance_id:
        rs.DeleteObject(block_id)

    rs.EnableRedraw(True)
    print("Created unique block '{}'.".format(new_block_name))


if __name__ == "__main__":
    duplicate_block_as_unique()
