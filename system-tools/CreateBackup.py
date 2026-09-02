# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import os
import datetime
import string
import shutil


def get_next_suffix(index):
    # bijective base-26 sequence, same pattern as spreadsheet column names:
    # 0->a, 1->b, ..., 25->z, 26->aa, 27->ab, ..., 51->az, 52->ba, ...
    letters = string.ascii_lowercase
    result = ""
    n = index
    while True:
        result = letters[n % 26] + result
        n = (n // 26) - 1
        if n < 0:
            break
    return result


def run_rhino_backup():
    doc_path = rs.DocumentPath()
    doc_name = rs.DocumentName()

    if not doc_path or not doc_name:
        rs.MessageBox(u"Save the file at least once before running a backup.", 0, "File Not Saved")
        return

    if not isinstance(doc_name, unicode):
        doc_name = unicode(doc_name, "utf-8", errors="ignore")
    if not isinstance(doc_path, unicode):
        doc_path = unicode(doc_path, "utf-8", errors="ignore")

    base_name = os.path.splitext(doc_name)[0]
    current_full_path = os.path.join(doc_path, doc_name)

    default_dir = ur"I:\RhinoBackups"
    target_dir = default_dir

    question_text = u"Backup will go to:\n\n'{0}'\n\nUse this folder?".format(default_dir)
    choice = rs.MessageBox(question_text, 4 + 32, "Rhino Backup")

    if choice == 7:
        custom_dir = rs.BrowseForFolder(default_dir, "Pick a folder for this backup", "Custom Backup")
        if custom_dir:
            target_dir = custom_dir if isinstance(custom_dir, unicode) else unicode(custom_dir, "utf-8", errors="ignore")
        else:
            print("Backup cancelled, no folder picked.")
            return

    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
            print("Created backup folder: {0}".format(target_dir))
        except Exception as e:
            print("Couldn't create the target folder: {0}".format(e))
            return

    timestamp = unicode(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    new_filename = u"{0}_{1}.3dm".format(base_name, timestamp)
    full_target_path = os.path.join(target_dir, new_filename)

    collision_index = 0
    while os.path.exists(full_target_path):
        suffix = unicode(get_next_suffix(collision_index))
        new_filename = u"{0}_{1}_{2}.3dm".format(base_name, timestamp, suffix)
        full_target_path = os.path.join(target_dir, new_filename)
        collision_index += 1

    try:
        shutil.copy2(current_full_path, full_target_path)
        print("Backup saved: {0}".format(new_filename))
        print("Location: {0}".format(target_dir))
        rs.StatusBarMessage("Backup saved: " + new_filename)
    except Exception as err:
        print("Copy failed: {0}".format(err))


if __name__ == "__main__":
    run_rhino_backup()
