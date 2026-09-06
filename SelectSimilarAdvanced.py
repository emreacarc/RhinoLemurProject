import rhinoscriptsyntax as rs
import scriptcontext as sc


def get_display_color(obj_id):
    # DrawColor() resolves ByLayer/ByObject correctly - rs.ObjectColor() alone
    # can be misleading for objects using a layer's color (see SelectObjectsSameColor.py)
    obj = sc.doc.Objects.Find(obj_id)
    if not obj:
        return None
    return obj.Attributes.DrawColor(sc.doc).ToArgb()


def select_similar_multi():
    ref_objects = rs.GetObjects(
        message="Select reference object(s) to match similar objects",
        preselect=True,
        select=False
    )

    if not ref_objects:
        print("No reference objects selected.")
        return

    if "select_similar_settings" not in sc.sticky:
        sc.sticky["select_similar_settings"] = {
            "match_type": True,
            "match_layer": True,
            "match_block_name": True,
            "match_color": False,
            "match_name": False,
            "match_dim": False,
            "match_vol": False
        }

    saved = sc.sticky["select_similar_settings"]

    items = [
        ("Object Type", saved.get("match_type", True)),
        ("Layer", saved.get("match_layer", True)),
        ("Block Name (For Block Instances)", saved.get("match_block_name", True)),
        ("Color", saved.get("match_color", False)),
        ("Name (Object Name)", saved.get("match_name", False)),
        ("Dimension / Size (Bounding Box)", saved.get("match_dim", False)),
        ("Volume (Closed Solids)", saved.get("match_vol", False))
    ]

    selected_options = rs.CheckListBox(
        items=items,
        message="Check criteria to match similar objects:",
        title="SelectSimilar Criteria"
    )

    if not selected_options:
        print("Cancelled.")
        return

    match_type = selected_options[0][1]
    match_layer = selected_options[1][1]
    match_block_name = selected_options[2][1]
    match_color = selected_options[3][1]
    match_name = selected_options[4][1]
    match_dim = selected_options[5][1]
    match_vol = selected_options[6][1]

    sc.sticky["select_similar_settings"] = {
        "match_type": match_type,
        "match_layer": match_layer,
        "match_block_name": match_block_name,
        "match_color": match_color,
        "match_name": match_name,
        "match_dim": match_dim,
        "match_vol": match_vol
    }

    if not any([match_type, match_layer, match_block_name, match_color, match_name, match_dim, match_vol]):
        print("No criteria checked, nothing to match on.")
        return

    def get_safe_volume(obj_id):
        try:
            if rs.IsPolysurface(obj_id) or rs.IsSurface(obj_id):
                if rs.IsPolysurfaceClosed(obj_id):
                    vol_data = rs.SurfaceVolume(obj_id)
                    return round(vol_data[0], 3) if vol_data else None
            elif rs.IsMesh(obj_id):
                if rs.IsMeshClosed(obj_id):
                    vol_data = rs.MeshVolume(obj_id)
                    return round(vol_data[0], 3) if vol_data else None
        except Exception:
            pass
        return None

    # gather the matching properties from every reference object, not just the first
    ref_types = set()
    ref_layers = set()
    ref_colors = set()
    ref_names = set()
    ref_block_names = set()
    ref_bbox_sizes = set()
    ref_volumes = set()

    missing_names_count = 0
    non_block_count = 0
    missing_bbox_count = 0
    non_solid_count = 0

    for obj in ref_objects:
        if match_type:
            ref_types.add(rs.ObjectType(obj))

        if match_layer:
            ref_layers.add(rs.ObjectLayer(obj))

        if match_color:
            ref_colors.add(get_display_color(obj))

        if match_name:
            name = rs.ObjectName(obj)
            if name:
                ref_names.add(name)
            else:
                missing_names_count += 1

        if match_block_name:
            if rs.IsBlockInstance(obj):
                ref_block_names.add(rs.BlockInstanceName(obj))
            else:
                non_block_count += 1

        if match_dim:
            bbox = rs.BoundingBox(obj)
            if bbox:
                dx = round(rs.Distance(bbox[0], bbox[1]), 3)
                dy = round(rs.Distance(bbox[0], bbox[3]), 3)
                dz = round(rs.Distance(bbox[0], bbox[4]), 3)
                ref_bbox_sizes.add((dx, dy, dz))
            else:
                missing_bbox_count += 1

        if match_vol:
            vol = get_safe_volume(obj)
            if vol is not None:
                ref_volumes.add(vol)
            else:
                non_solid_count += 1

    # if a criterion turned out to be unusable across the whole reference set, drop it instead of matching nothing
    if match_name and missing_names_count > 0:
        print("Warning: {} reference object(s) have no Object Name.".format(missing_names_count))
        if not ref_names:
            match_name = False

    if match_block_name and non_block_count > 0:
        print("Warning: {} reference object(s) are not block instances.".format(non_block_count))
        if not ref_block_names:
            match_block_name = False

    if match_dim and missing_bbox_count > 0:
        print("Warning: couldn't get a bounding box for {} reference object(s).".format(missing_bbox_count))
        if not ref_bbox_sizes:
            match_dim = False

    if match_vol and non_solid_count > 0:
        print("Warning: {} reference object(s) aren't closed solids/meshes.".format(non_solid_count))
        if not ref_volumes:
            match_vol = False

    all_objects = rs.NormalObjects(include_lights=False, include_grips=False)
    similar_objects = []

    for obj in all_objects:
        if obj in ref_objects:
            similar_objects.append(obj)
            continue

        if match_type and rs.ObjectType(obj) not in ref_types:
            continue

        if match_layer and rs.ObjectLayer(obj) not in ref_layers:
            continue

        if match_block_name and ref_block_names:
            if not rs.IsBlockInstance(obj) or rs.BlockInstanceName(obj) not in ref_block_names:
                continue

        if match_color and get_display_color(obj) not in ref_colors:
            continue

        if match_name and ref_names:
            if rs.ObjectName(obj) not in ref_names:
                continue

        if match_dim and ref_bbox_sizes:
            obj_bbox = rs.BoundingBox(obj)
            if not obj_bbox:
                continue
            dx = round(rs.Distance(obj_bbox[0], obj_bbox[1]), 3)
            dy = round(rs.Distance(obj_bbox[0], obj_bbox[3]), 3)
            dz = round(rs.Distance(obj_bbox[0], obj_bbox[4]), 3)
            if (dx, dy, dz) not in ref_bbox_sizes:
                continue

        if match_vol and ref_volumes:
            vol = get_safe_volume(obj)
            if vol is None or vol not in ref_volumes:
                continue

        similar_objects.append(obj)

    if similar_objects:
        rs.SelectObjects(similar_objects)
        print("Selected {0} matching object(s) against {1} reference object(s).".format(
            len(similar_objects), len(ref_objects)
        ))
    else:
        print("No matching objects found.")


if __name__ == "__main__":
    select_similar_multi()
