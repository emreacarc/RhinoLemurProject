# -*- coding: utf-8 -*-
import Rhino
import scriptcontext as sc
import System


def add_centered_xline(center_pt, direction):
    """Draws a very long line, perfectly centered on the given point."""
    if direction.Length == 0:
        return
    direction.Unitize()

    # long enough that Rhino won't clip it asymmetrically on screen
    dist = 1000000.0
    p1 = center_pt - (direction * dist)
    p2 = center_pt + (direction * dist)
    sc.doc.Objects.AddLine(p1, p2)


def draw_axis_xlines(is_horizontal):
    """Horizontal/vertical mode, tracking whichever viewport's CPlane the mouse is over."""
    while True:
        gp = Rhino.Input.Custom.GetPoint()
        if is_horizontal:
            gp.SetCommandPrompt("Pick center point for horizontal xline (Enter to finish)")
        else:
            gp.SetCommandPrompt("Pick center point for vertical xline (Enter to finish)")

        def dynamic_axis_draw(sender, e):
            # read the axes of whichever viewport the cursor is over right now
            cplane = e.Viewport.ConstructionPlane()
            direction = cplane.XAxis if is_horizontal else cplane.YAxis

            pt = e.CurrentPoint
            p1 = pt - (direction * 1000000.0)
            p2 = pt + (direction * 1000000.0)

            e.Display.DrawLine(p1, p2, System.Drawing.Color.DarkGray)
            e.Display.DrawPoint(pt, System.Drawing.Color.Red)

        gp.DynamicDraw += dynamic_axis_draw
        res = gp.Get()

        if res == Rhino.Input.GetResult.Cancel or res == Rhino.Input.GetResult.Nothing:
            break

        if res == Rhino.Input.GetResult.Point:
            pt = gp.Point()

            # use the axes of the view that was actually clicked in for the final line
            view = gp.View()
            if view:
                cplane = view.ActiveViewport.ConstructionPlane()
            else:
                cplane = sc.doc.Views.ActiveView.ActiveViewport.ConstructionPlane()

            direction = cplane.XAxis if is_horizontal else cplane.YAxis
            add_centered_xline(pt, direction)
            sc.doc.Views.Redraw()


def main():
    gp = Rhino.Input.Custom.GetPoint()
    gp.SetCommandPrompt("Pick a start point, or choose an option")

    op_horiz = gp.AddOption("Horizontal")
    op_vert = gp.AddOption("Vertical")

    res = gp.Get()

    if res == Rhino.Input.GetResult.Cancel or res == Rhino.Input.GetResult.Nothing:
        return

    if res == Rhino.Input.GetResult.Option:
        opt = gp.Option().Index
        if opt == op_horiz:
            draw_axis_xlines(True)
        elif opt == op_vert:
            draw_axis_xlines(False)
        return

    # user clicked a point instead - standard centered 2-point mode
    if res == Rhino.Input.GetResult.Point:
        pt1 = gp.Point()

        while True:
            gp2 = Rhino.Input.Custom.GetPoint()
            gp2.SetCommandPrompt("Pick the second point to pass through (Enter to finish)")

            def dynamic_2pt_draw(sender, e):
                pt2 = e.CurrentPoint
                if pt1.DistanceTo(pt2) > 0.001:
                    mid_x = (pt1.X + pt2.X) / 2.0
                    mid_y = (pt1.Y + pt2.Y) / 2.0
                    mid_z = (pt1.Z + pt2.Z) / 2.0
                    mid = Rhino.Geometry.Point3d(mid_x, mid_y, mid_z)

                    direction = pt2 - pt1
                    direction.Unitize()

                    p1 = mid - (direction * 1000000.0)
                    p2 = mid + (direction * 1000000.0)
                    e.Display.DrawLine(p1, p2, System.Drawing.Color.DarkGray)
                    e.Display.DrawPoint(mid, System.Drawing.Color.Red)

            gp2.DynamicDraw += dynamic_2pt_draw
            res2 = gp2.Get()

            if res2 == Rhino.Input.GetResult.Cancel or res2 == Rhino.Input.GetResult.Nothing:
                break

            if res2 == Rhino.Input.GetResult.Point:
                pt2 = gp2.Point()
                if pt1.DistanceTo(pt2) > 0.001:
                    mid_x = (pt1.X + pt2.X) / 2.0
                    mid_y = (pt1.Y + pt2.Y) / 2.0
                    mid_z = (pt1.Z + pt2.Z) / 2.0
                    mid = Rhino.Geometry.Point3d(mid_x, mid_y, mid_z)

                    direction = pt2 - pt1
                    add_centered_xline(mid, direction)
                    sc.doc.Views.Redraw()


if __name__ == "__main__":
    main()
