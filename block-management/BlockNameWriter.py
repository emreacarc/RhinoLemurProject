# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import Eto.Forms as forms
import Eto.Drawing as drawing

LABEL_TAG_KEY = "BlockNameWriter_Label"

# remembers the last values used, same idea as Rhino's own <default> prompts
HEIGHT_KEY = "BlockNameWriter_Height"
FONT_KEY = "BlockNameWriter_Font"
LOCATION_KEY = "BlockNameWriter_Location"

DEFAULT_HEIGHT = 5.0
DEFAULT_FONT = "Arial Narrow"
DEFAULT_LOCATION = "Outside_Block"


def get_top_surface_center_and_plane(block_id):
    # world-space bbox of the instance, centered on its topmost face
    bbox = rs.BoundingBox(block_id)
    if not bbox:
        return None, None

    z_max = bbox[4].Z
    x_center = (bbox[4].X + bbox[6].X) / 2.0
    y_center = (bbox[4].Y + bbox[6].Y) / 2.0
    top_center = Rhino.Geometry.Point3d(x_center, y_center, z_max)

    plane = Rhino.Geometry.Plane.WorldXY
    plane.Origin = top_center
    return top_center, plane


def get_local_top_center_and_plane(block_name):
    # Same idea as above, but computed straight from the block DEFINITION's
    # own geometry instead of a specific instance's world-space bbox. That
    # way the label lands in the same spot no matter which instance (scaled,
    # rotated, mirrored...) happens to trigger the update.
    block_objects = rs.BlockObjects(block_name)
    if not block_objects:
        return None, None

    bbox = rs.BoundingBox(block_objects)
    if not bbox:
        return None, None

    z_max = bbox[4].Z
    x_center = (bbox[4].X + bbox[6].X) / 2.0
    y_center = (bbox[4].Y + bbox[6].Y) / 2.0
    top_center = Rhino.Geometry.Point3d(x_center, y_center, z_max)

    plane = Rhino.Geometry.Plane.WorldXY
    plane.Origin = top_center
    return top_center, plane


def safe_get_font(font_name):
    try:
        font = Rhino.DocObjects.Font(font_name)
        if font is None:
            raise ValueError("got None back for font")
        return font
    except Exception:
        print("Font '{0}' not found, using Arial instead.".format(font_name))
        return Rhino.DocObjects.Font("Arial")


def create_text_object(text_string, plane, height, font_name, current_layer, tag_as_label=False):
    if not isinstance(text_string, unicode):
        text_string = unicode(text_string, "utf-8", errors="ignore")

    te = Rhino.Geometry.TextEntity()
    te.Plane = plane
    te.Text = text_string
    te.TextHeight = height
    te.Justification = Rhino.Geometry.TextJustification.Center
    te.Font = safe_get_font(font_name)

    obj_id = sc.doc.Objects.AddText(te)
    if obj_id:
        rs.ObjectLayer(obj_id, current_layer)
        if tag_as_label:
            # so we can find + replace it next time instead of stacking duplicates
            rs.SetUserText(obj_id, LABEL_TAG_KEY, "1")
    return obj_id


def remove_previous_labels_from_definition(block_name):
    block_objects = rs.BlockObjects(block_name)
    if not block_objects:
        return []

    remaining = []
    for obj_id in block_objects:
        if rs.GetUserText(obj_id, LABEL_TAG_KEY):
            continue  # this is an old label from a previous run, drop it
        remaining.append(obj_id)
    return remaining


def show_options_dialog(height_default, font_default, location_default):
    # one dialog, all three settings at once - no step-by-step prompting
    dialog = forms.Dialog[bool]()
    dialog.Title = "Block Name Writer - Settings"
    dialog.Padding = drawing.Padding(12)
    dialog.Resizable = False

    height_box = forms.NumericStepper()
    height_box.DecimalPlaces = 2
    height_box.MinValue = 0.01
    height_box.MaxValue = 1000000
    height_box.Value = height_default
    height_box.Width = 150

    font_box = forms.TextBox()
    font_box.Text = font_default
    font_box.Width = 150

    location_box = forms.DropDown()
    location_box.Items.Add("Outside_Block")
    location_box.Items.Add("Inside_Block")
    location_box.SelectedIndex = 0 if location_default == "Outside_Block" else 1

    form_layout = forms.DynamicLayout()
    form_layout.Spacing = drawing.Size(8, 10)
    form_layout.AddRow(forms.Label(Text="Text Height:"), height_box)
    form_layout.AddRow(forms.Label(Text="Font Name:"), font_box)
    form_layout.AddRow(forms.Label(Text="Location:"), location_box)

    ok_button = forms.Button(Text="OK")
    cancel_button = forms.Button(Text="Cancel")

    def on_ok(sender, e):
        dialog.Close(True)

    def on_cancel(sender, e):
        dialog.Close(False)

    ok_button.Click += on_ok
    cancel_button.Click += on_cancel

    button_row = forms.DynamicLayout()
    button_row.AddRow(None, ok_button, cancel_button)

    main_layout = forms.DynamicLayout()
    main_layout.Spacing = drawing.Size(8, 14)
    main_layout.AddSeparateRow(form_layout)
    main_layout.AddSeparateRow(button_row)

    dialog.Content = main_layout
    dialog.DefaultButton = ok_button
    dialog.AbortButton = cancel_button

    confirmed = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    if not confirmed:
        return None

    return height_box.Value, font_box.Text, location_box.SelectedValue.ToString()


def main():
    selected = rs.SelectedObjects()
    if not selected:
        selected = rs.GetObjects("Select blocks to label", filter=4096, preselect=True)

    blocks = [obj for obj in selected if rs.IsBlockInstance(obj)] if selected else []
    if not blocks:
        rs.MessageBox("No valid block instances selected!", 0, "Error")
        return

    height_default = sc.sticky.get(HEIGHT_KEY, DEFAULT_HEIGHT)
    font_default = sc.sticky.get(FONT_KEY, DEFAULT_FONT)
    location_default = sc.sticky.get(LOCATION_KEY, DEFAULT_LOCATION)

    dialog_result = show_options_dialog(height_default, font_default, location_default)
    if dialog_result is None:
        return

    text_height, font_name, location_choice = dialog_result

    if text_height is None or text_height <= 0:
        rs.MessageBox("Text height must be greater than 0.", 0, "Error")
        return
    if not font_name or not font_name.strip():
        rs.MessageBox("Font name cannot be empty.", 0, "Error")
        return

    sc.sticky[HEIGHT_KEY] = text_height
    sc.sticky[FONT_KEY] = font_name
    sc.sticky[LOCATION_KEY] = location_choice

    current_layer = rs.CurrentLayer()
    inside_processed_defs = set()

    rs.EnableRedraw(False)

    for block in blocks:
        block_name = rs.BlockInstanceName(block)
        if not isinstance(block_name, unicode):
            block_name = unicode(block_name, "utf-8", errors="ignore")

        if location_choice == "Outside_Block":
            center_pt, target_plane = get_top_surface_center_and_plane(block)
            if target_plane:
                create_text_object(block_name, target_plane, text_height, font_name, current_layer)

        elif location_choice == "Inside_Block":
            if block_name in inside_processed_defs:
                continue

            center_pt, target_plane = get_local_top_center_and_plane(block_name)
            if not target_plane:
                continue

            existing_objects = remove_previous_labels_from_definition(block_name)
            temp_text = create_text_object(
                block_name, target_plane, text_height, font_name, current_layer, tag_as_label=True
            )

            if temp_text:
                new_obj_ids = list(existing_objects) + [temp_text]
                base_point = Rhino.Geometry.Point3d(0, 0, 0)
                rs.ModifyBlockDefinition(block_name, base_point, new_obj_ids, replace_geometry=True)
                inside_processed_defs.add(block_name)

    rs.EnableRedraw(True)
    rs.Redraw()
    print("Done - labeled {0} block(s).".format(len(blocks)))


if __name__ == "__main__":
    main()
