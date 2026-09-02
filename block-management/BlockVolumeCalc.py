# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import os
import datetime


def get_volume_scale_factor(xform):
    # volume scale introduced by an instance's transform - handles
    # non-uniform scale, rotation and mirroring. computed manually from the
    # 3x3 linear part instead of relying on Transform.Determinant, which
    # isn't available on every RhinoCommon version.
    if not xform:
        return 1.0
    try:
        a, b, c = xform[0, 0], xform[0, 1], xform[0, 2]
        d, e, f = xform[1, 0], xform[1, 1], xform[1, 2]
        g, h, i = xform[2, 0], xform[2, 1], xform[2, 2]
        det = (a * (e * i - f * h)
               - b * (d * i - f * g)
               + c * (d * h - e * g))
        return abs(det)
    except Exception:
        return 1.0


def export_block_volumes_and_weights():
    selected_objects = rs.SelectedObjects()
    if not selected_objects:
        print("Select at least one block instance first.")
        return

    blocks = [obj for obj in selected_objects if rs.IsBlockInstance(obj)]
    if not blocks:
        print("Nothing in the selection is a block instance.")
        return

    calculate_weight = False
    material_name = "N/A"
    density_kg_m3 = 0.0

    weight_choice = rs.MessageBox(u"Calculate material weight (kg) for these blocks too?", 4 + 32, "Weight Calculation")

    if weight_choice == 6:  # Yes
        calculate_weight = True
        material_options = [
            "S235 Structural Steel (7850 kg/m3)",
            "S275 Structural Steel (7850 kg/m3)",
            "S355 Structural Steel (7850 kg/m3)",
            "Stainless Steel 304/316 (8000 kg/m3)",
            "Aluminum (2700 kg/m3)"
        ]
        selected_mat = rs.ListBox(material_options, u"Select material type:", "Material Selection", default=material_options[0])

        if not selected_mat:
            print("No material chosen, exporting volume only.")
            calculate_weight = False
        else:
            material_name = selected_mat.split(" (")[0]
            if "Steel" in selected_mat and "Stainless" not in selected_mat:
                density_kg_m3 = 7850.0
            elif "Stainless" in selected_mat:
                density_kg_m3 = 8000.0
            elif "Aluminum" in selected_mat:
                density_kg_m3 = 2700.0

    # geometry volume of each unique block DEFINITION, at scale 1.0, cached once
    base_volume_cache = {}

    def get_base_volume(b_name):
        if b_name in base_volume_cache:
            return base_volume_cache[b_name]

        block_objects = rs.BlockObjects(b_name)
        single_unit_volume_mm3 = 0.0
        solid_count = 0

        if block_objects:
            for obj_id in block_objects:
                vol = None
                if (rs.IsPolysurface(obj_id) and rs.IsPolysurfaceClosed(obj_id)) or \
                   (rs.IsSurface(obj_id) and rs.IsSurfaceClosed(obj_id)):
                    vol_properties = rs.SurfaceVolume(obj_id)
                    if vol_properties:
                        vol = vol_properties[0]
                elif rs.IsMesh(obj_id) and rs.IsMeshClosed(obj_id):
                    vol_properties = rs.MeshVolume(obj_id)
                    if vol_properties:
                        vol = vol_properties[0]

                if vol is not None:
                    single_unit_volume_mm3 += vol
                    solid_count += 1

        base_volume_cache[b_name] = (single_unit_volume_mm3, solid_count)
        return base_volume_cache[b_name]

    # walk every instance individually (not just one per name) and apply its
    # own scale factor, so mixed scales under the same block name still add up right
    block_counts = {}
    block_total_volume_mm3 = {}
    block_scale_variants = {}

    for block in blocks:
        b_name = rs.BlockInstanceName(block)
        single_unit_volume_mm3, _ = get_base_volume(b_name)

        xform = rs.BlockInstanceXform(block)
        scale_factor = get_volume_scale_factor(xform)
        instance_volume_mm3 = single_unit_volume_mm3 * scale_factor

        block_counts[b_name] = block_counts.get(b_name, 0) + 1
        block_total_volume_mm3[b_name] = block_total_volume_mm3.get(b_name, 0.0) + instance_volume_mm3
        block_scale_variants.setdefault(b_name, set()).add(round(scale_factor, 6))

    report_data = []
    total_grand_volume_m3 = 0.0
    total_grand_weight_kg = 0.0
    total_grand_qty = 0

    print("Block breakdown:")

    for b_name in sorted(block_counts.keys()):
        qty = block_counts[b_name]
        total_grand_qty += qty

        _, solid_count = base_volume_cache[b_name]

        total_block_volume_m3 = block_total_volume_mm3[b_name] / 1000000000.0
        total_block_weight_kg = total_block_volume_m3 * density_kg_m3 if calculate_weight else 0.0

        # unit values become an average once scales differ within the same name
        unit_volume_m3 = total_block_volume_m3 / qty if qty else 0.0
        unit_weight_kg = total_block_weight_kg / qty if qty else 0.0

        total_grand_volume_m3 += total_block_volume_m3
        total_grand_weight_kg += total_block_weight_kg

        mixed_scale = len(block_scale_variants[b_name]) > 1
        scale_note = "Mixed scales (avg shown)" if mixed_scale else ""
        note_suffix = "  [mixed scales - totals correct, unit values averaged]" if mixed_scale else ""

        report_data.append([b_name, qty, solid_count, unit_volume_m3, total_block_volume_m3, unit_weight_kg, total_block_weight_kg, scale_note])

        if calculate_weight:
            print("  {0}  x{1}  ->  {2:,.2f} kg total{3}".format(b_name, qty, total_block_weight_kg, note_suffix))
        else:
            print("  {0}  x{1}  ->  {2:,.4f} m3 total{3}".format(b_name, qty, total_block_volume_m3, note_suffix))

    export_choice = rs.MessageBox("Export these results to a CSV file?", 4 + 32, "Export to Excel")

    if export_choice == 6:
        doc_folder = rs.DocumentPath()
        doc_name = rs.DocumentName()

        if not doc_folder or not doc_name:
            doc_folder = os.path.join(os.path.expanduser("~"), "Desktop")
            base_file_name = "Rhino_Block_Report"
            print("File isn't saved yet, exporting to Desktop instead.")
        else:
            base_file_name = os.path.splitext(doc_name)[0]

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file_name = "{0}_BOM_{1}.csv".format(base_file_name, timestamp)
        file_path = os.path.join(doc_folder, csv_file_name)

        try:
            with open(file_path, 'w') as f:
                if calculate_weight:
                    f.write("Block Name;Quantity (Pcs);Solids In Block;Unit Volume (m3);Total Volume (m3);Unit Weight (kg);Total Weight (kg);Note\n")
                else:
                    f.write("Block Name;Quantity (Pcs);Solids In Block;Unit Volume (m3);Total Volume (m3);Note\n")

                for row in report_data:
                    if calculate_weight:
                        f.write("{0};{1};{2};{3:.6f};{4:.6f};{5:.2f};{6:.2f};{7}\n".format(
                            row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]
                        ))
                    else:
                        f.write("{0};{1};{2};{3:.6f};{4:.6f};{5}\n".format(
                            row[0], row[1], row[2], row[3], row[4], row[7]
                        ))

                if calculate_weight:
                    f.write("\nTOTAL;{0};;;{1:.6f};;{2:.2f}\n".format(total_grand_qty, total_grand_volume_m3, total_grand_weight_kg))
                    f.write("\nMaterial Config:;{0};;Density Value:;{1} kg/m3\n".format(material_name, density_kg_m3))
                else:
                    f.write("\nTOTAL;{0};;;{1:.6f}\n".format(total_grand_qty, total_grand_volume_m3))

            print("Saved report to: {0}".format(file_path))
            rs.MessageBox("BOM report saved.", 0, "Export Success")
        except Exception as e:
            print("Couldn't write the CSV file: {0}".format(e))


if __name__ == "__main__":
    export_block_volumes_and_weights()
