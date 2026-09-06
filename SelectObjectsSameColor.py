import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc


def select_objects_by_same_color():
    source_id = rs.GetObject("Select an object to match its color", preselect=True)
    if not source_id:
        print("Nothing selected.")
        return

    source_obj = sc.doc.Objects.Find(source_id)
    if not source_obj:
        return

    # DrawColor() gives the actual visible color, sidestepping ByLayer/ByObject mismatches
    target_color = source_obj.Attributes.DrawColor(sc.doc)

    settings = Rhino.DocObjects.ObjectEnumeratorSettings()
    settings.NormalObjects = True
    settings.LockedObjects = False
    settings.HiddenObjects = False

    active_objects = sc.doc.Objects.GetObjectList(settings)
    if not active_objects:
        print("No active objects in this context.")
        return

    objects_to_select = []

    for obj in active_objects:
        if not obj.IsSelectable():
            continue

        current_obj_color = obj.Attributes.DrawColor(sc.doc)
        if current_obj_color.ToArgb() == target_color.ToArgb():
            objects_to_select.append(obj.Id)

    if objects_to_select:
        rs.EnableRedraw(False)
        rs.SelectObjects(objects_to_select)
        rs.EnableRedraw(True)
        print("Selected {} object(s) with a matching color.".format(len(objects_to_select)))
    else:
        print("No other objects share that color here.")


if __name__ == "__main__":
    select_objects_by_same_color()
