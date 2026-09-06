import rhinoscriptsyntax as rs


def create_bolt_slot():
    surface_id = rs.GetObject("Select surface or face for the slot hole", filter=8, preselect=False, subobjects=True)
    if not surface_id:
        print("No surface or face selected.")
        return

    bolt_options = [
        "Custom", "M4", "M5", "M6", "M8", "M10", "M12", "M14", "M16",
        "M18", "M20", "M22", "M24", "M27", "M30"
    ]
    selected_bolt = rs.ListBox(bolt_options, "Select bolt size (adds 1mm tolerance):", "Bolt Size Selection")
    if not selected_bolt:
        print("Bolt size selection cancelled.")
        return

    if selected_bolt == "Custom":
        custom_val = rs.GetReal("Enter custom bolt diameter (mm):", minimum=0.1)
        if not custom_val:
            print("Invalid custom diameter.")
            return
        slot_width = custom_val + 1.0
    else:
        nominal_size = int(selected_bolt[1:])
        slot_width = nominal_size + 1.0

    length_options = ["Custom"] + [str(i) for i in range(10, 55, 5)]
    selected_length = rs.ListBox(length_options, "Select slot length (center-to-center, mm):", "Slot Length Selection")
    if not selected_length:
        print("Slot length selection cancelled.")
        return

    if selected_length == "Custom":
        center_length = rs.GetReal("Enter custom slot length (mm):", minimum=0.1)
        if not center_length:
            print("Invalid custom length.")
            return
    else:
        center_length = float(selected_length)

    # first point picked = outer edge of the slot, second point = direction
    start_pt = rs.GetPointOnSurface(surface_id, "Pick slot start point (outer edge)")
    if not start_pt:
        print("Start point not selected.")
        return

    end_pt = rs.GetPointOnSurface(surface_id, "Pick second point to define slot direction")
    if not end_pt:
        print("Direction point not selected.")
        return

    if rs.Distance(start_pt, end_pt) < 0.001:
        print("Start point and direction point can't be the same.")
        return

    uv = rs.SurfaceClosestPoint(surface_id, start_pt)
    normal = rs.SurfaceNormal(surface_id, uv)

    dir_x = rs.VectorUnitize(rs.VectorCreate(end_pt, start_pt))
    dir_y = rs.VectorUnitize(rs.VectorCrossProduct(normal, dir_x))

    r = slot_width / 2.0

    # shift the plane origin inward by the radius so the picked start_pt
    # ends up being the actual outer edge, not the arc center
    shift_vector = rs.VectorScale(dir_x, r)
    plane_origin = rs.PointAdd(start_pt, shift_vector)
    plane = rs.PlaneFromFrame(plane_origin, dir_x, dir_y)

    # build the slot in the plane's local U/V coordinates
    pt_a = rs.EvaluatePlane(plane, [0, -r])
    pt_b = rs.EvaluatePlane(plane, [-r, 0])
    pt_c = rs.EvaluatePlane(plane, [0, r])
    arc1 = rs.AddArc3Pt(pt_a, pt_c, pt_b)

    pt_d = rs.EvaluatePlane(plane, [center_length, r])
    line1 = rs.AddLine(pt_c, pt_d)

    pt_e = rs.EvaluatePlane(plane, [center_length + r, 0])
    pt_f = rs.EvaluatePlane(plane, [center_length, -r])
    arc2 = rs.AddArc3Pt(pt_d, pt_f, pt_e)

    line2 = rs.AddLine(pt_f, pt_a)

    # any of these can come back None on degenerate geometry - filter before joining
    raw_curves = [arc1, line1, arc2, line2]
    curves = [c for c in raw_curves if c is not None]

    if len(curves) < len(raw_curves):
        missing = len(raw_curves) - len(curves)
        print("{0} of 4 slot segments failed to build, aborting.".format(missing))
        for c in curves:
            rs.DeleteObject(c)
        return

    slot_curve = rs.JoinCurves(curves, delete_input=True)

    if slot_curve:
        print("Slot created - {0} (width {1}mm), length {2}mm.".format(selected_bolt, slot_width, center_length))
    else:
        print("Failed to join the slot segments into one curve.")


if __name__ == "__main__":
    create_bolt_slot()
