# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import scriptcontext as sc
import math


def draw_slot(center, direction_vec, cap, slot_length):
    radius = cap / 2.0
    straight = max(0.0, slot_length - cap)

    if straight < 0.001:
        # slot length is at or below the cap diameter, so it's really just a circle
        rs.AddCircle(center, radius)
        return

    unit = rs.VectorUnitize(direction_vec)
    half = straight / 2.0

    perp = rs.VectorCrossProduct(unit, [0, 0, 1])
    if rs.VectorLength(perp) < 0.001:
        perp = rs.VectorCrossProduct(unit, [0, 1, 0])
    perp = rs.VectorUnitize(perp)

    # centers of the two end caps
    c1 = rs.PointAdd(center, rs.VectorScale(unit, half))
    c2 = rs.PointAdd(center, rs.VectorScale(unit, -half))

    # the four corner points of the straight sides
    p1 = rs.PointAdd(c1, rs.VectorScale(perp, radius))
    p2 = rs.PointAdd(c2, rs.VectorScale(perp, radius))
    p3 = rs.PointAdd(c2, rs.VectorScale(perp, -radius))
    p4 = rs.PointAdd(c1, rs.VectorScale(perp, -radius))

    arc_mid_c2 = rs.PointAdd(c2, rs.VectorScale(unit, -radius))
    arc_mid_c1 = rs.PointAdd(c1, rs.VectorScale(unit, radius))

    line1 = rs.AddLine(p1, p2)
    arc1 = rs.AddArc3Pt(p2, p3, arc_mid_c2)
    line2 = rs.AddLine(p3, p4)
    arc2 = rs.AddArc3Pt(p4, p1, arc_mid_c1)

    curves = [c for c in [line1, arc1, line2, arc2] if c is not None]
    if curves:
        rs.JoinCurves(curves, delete_input=True)


def place_edge_slots():
    DIA_KEY = "EdgeSlot_diameter"
    OFFSET_KEY = "EdgeSlot_endOffset"
    SPACING_KEY = "EdgeSlot_spacing"
    LENGTH_KEY = "EdgeSlot_length"

    dia_default = sc.sticky.get(DIA_KEY, 20.0)
    offset_default = sc.sticky.get(OFFSET_KEY, 50.0)
    spacing_default = sc.sticky.get(SPACING_KEY, 100.0)
    length_default = sc.sticky.get(LENGTH_KEY, 40.0)

    p1 = rs.GetPoint("Pick the start point")
    if p1 is None:
        return
    p2 = rs.GetPoint("Pick the end point")
    if p2 is None:
        return

    diameter = rs.GetReal("Hole diameter (mm)", dia_default, 0.01)
    if diameter is None:
        return

    slot_length = rs.GetReal("Slot length (mm)", length_default, diameter)
    if slot_length is None:
        return

    end_offset = rs.GetReal("End offset distance (mm)", offset_default, 0.0)
    if end_offset is None:
        return

    spacing = rs.GetReal("Hole spacing, max (mm)", spacing_default, 0.01)
    if spacing is None:
        return

    sc.sticky[DIA_KEY] = diameter
    sc.sticky[OFFSET_KEY] = end_offset
    sc.sticky[SPACING_KEY] = spacing
    sc.sticky[LENGTH_KEY] = slot_length

    vec = rs.VectorCreate(p2, p1)
    length = rs.VectorLength(vec)
    if length <= 0:
        rs.MessageBox("Start and end points are the same.")
        return

    usable = length - 2.0 * end_offset
    if usable <= 0:
        rs.MessageBox("End offset is larger than the available length - no room for holes.")
        return

    points = []
    start_pt = rs.PointAdd(p1, rs.VectorScale(vec, end_offset / length))
    points.append(start_pt)
    end_pt = rs.PointAdd(p1, rs.VectorScale(vec, (length - end_offset) / length))

    if usable <= spacing:
        points.append(end_pt)
    else:
        segments = int(math.ceil(usable / spacing))
        step = usable / segments
        for i in range(1, segments):
            offset = end_offset + i * step
            points.append(rs.PointAdd(p1, rs.VectorScale(vec, offset / length)))
        points.append(end_pt)

    for pt in points:
        draw_slot(pt, vec, diameter, slot_length)

    rs.MessageBox("{} slot(s) placed.".format(len(points)))


if __name__ == "__main__":
    place_edge_slots()
