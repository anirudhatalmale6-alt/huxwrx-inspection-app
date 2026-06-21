#!/usr/bin/env python3
"""v215: Fix Ac/Re formula (d=-1→Ac=1), fix majSS Level I, move popup label up.

Source: June 21 export #2 (has v210 auto-hold + AQL fixes baked in).
Includes all v211-v213 changes plus:
- Ac formula: d=-1 now gives Ac=1 (was 0) per Z1.4 Table II-A
- majSS Level I: use base code letter table (same as critSS)
- Popup label Y moved up for better spacing
"""
import zipfile, io, os, json, copy

PROJECT_DIR = '/var/lib/freelancer/projects/40486904'
OUTER_ZIP = os.path.join(PROJECT_DIR, 'Incoming_Inprocess&FinalInspections_20260621133436 (1).zip')
MSAPP_PATH = 'Microsoft.PowerApps/apps/18391596269880809910/N615f6b13-50de-4d08-9ffc-9d1837bf6e37-document.msapp'
OUTPUT = os.path.join(PROJECT_DIR, 'v215_aql.msapp')


def find_control(node, name):
    if isinstance(node, dict):
        if node.get("Name") == name:
            return node
        for v in node.values():
            r = find_control(v, name)
            if r: return r
    elif isinstance(node, list):
        for item in node:
            r = find_control(item, name)
            if r: return r
    return None


def set_rule(control, prop, script, category="Design"):
    for r in control.get("Rules", []):
        if r["Property"] == prop:
            r["InvariantScript"] = script
            return
    control["Rules"].append({
        "Property": prop, "Category": category,
        "InvariantScript": script, "RuleProviderType": "Unknown"
    })


def get_rule(control, prop):
    for r in control.get("Rules", []):
        if r["Property"] == prop:
            return r["InvariantScript"]
    return None


IS_ON_HOLD = 'RecordsGallery1.Selected.DispositionStatus.Value = "On Hold"'


def build():
    msapp_dir = os.path.join(PROJECT_DIR, 'june21_v2_msapp')
    with open(os.path.join(msapp_dir, 'Src\\MainScreen1.pa.yaml'), 'r', encoding='utf-8') as f:
        yaml_text = f.read()
    with open(os.path.join(msapp_dir, 'Controls\\4.json'), 'rb') as f:
        json_raw = f.read()
    json_data = json.loads(json_raw)
    changes = 0

    # ============================================================
    # YAML CHANGES
    # ============================================================

    # --- Y1. OnSuccess: Hold Reason as SEPARATE Patch (avoid Blank() crash on Choice) ---
    # Don't modify the main Patch - add a separate Patch after it for Hold Reason
    old_patch_end = "pending sorting or rework\", \"\"))});"
    new_patch_end = ("pending sorting or rework\", \"\")))});\n"
                     "                                      If(gblIsFail, Patch([@'Incoming/In process & Final Inspections'], "
                     "LookUp([@'Incoming/In process & Final Inspections'], ID = Form1.LastSubmit.ID), "
                     "{'Hold Reason': {Value: \"Hold for 100% Sorting\"}}));")
    assert old_patch_end in yaml_text, 'Y1 fail'
    yaml_text = yaml_text.replace(old_patch_end, new_patch_end, 1); changes += 1
    print('Y1: Hold Reason as separate Patch (fail-only)')

    # --- Y2. OnSuccess: Refresh after auto-hold ---
    old = ('Notify("Hold notification email failed.", NotificationType.Warning)));\n'
           '                                      ViewForm(Form1);')
    new = ('Notify("Hold notification email failed.", NotificationType.Warning)));\n'
           '                                      If(gblIsFail, Refresh([@\'Incoming/In process & Final Inspections\']));\n'
           '                                      ViewForm(Form1);')
    assert old in yaml_text, 'Y2 fail'
    yaml_text = yaml_text.replace(old, new, 1); changes += 1
    print('Y2: Refresh after auto-hold')

    # --- Y3. Hide DataCardValue23 (empty justification text input below AQL calc) ---
    old = ('- DataCardValue23:\n'
           '                                              Control: Classic/TextInput@2.3.2\n'
           '                                              MetadataKey: FieldValue\n'
           '                                              Properties:\n'
           '                                                BorderColor: =If(IsBlank(Parent.Error), Parent.BorderColor, Color.Red)\n'
           '                                                Color: =RGBA(50, 49, 48, 1)\n'
           '                                                Default: =Parent.Default\n')
    new = ('- DataCardValue23:\n'
           '                                              Control: Classic/TextInput@2.3.2\n'
           '                                              MetadataKey: FieldValue\n'
           '                                              Properties:\n'
           '                                                BorderColor: =If(IsBlank(Parent.Error), Parent.BorderColor, Color.Red)\n'
           '                                                Color: =RGBA(50, 49, 48, 1)\n'
           '                                                Default: =Parent.Default\n'
           '                                                Visible: =false\n')
    assert old in yaml_text, 'Y3 fail'
    yaml_text = yaml_text.replace(old, new, 1); changes += 1
    print('Y3: DataCardValue23 hidden (empty field below AQL)')

    # --- Y4. Headerlbl_41 Text: conditional ---
    old = '="Hold Request"'
    new = f'=If({IS_ON_HOLD}, "Release Hold", "Hold Request")'
    assert yaml_text.count(old) == 1, 'Y4 not unique'
    yaml_text = yaml_text.replace(old, new, 1); changes += 1
    print('Y4: Header dynamic')

    # --- Y5. lbl_Director_Comments_6 Text: conditional ---
    old = ('- lbl_Director_Comments_6:\n'
           '                Control: Label@2.5.1\n'
           '                Group: Grp_Director_Comments_6\n'
           '                Properties:\n'
           '                  FontWeight: =FontWeight.Semibold\n'
           '                  Size: =14\n'
           '                  Text: ="Reason"\n')
    new = ('- lbl_Director_Comments_6:\n'
           '                Control: Label@2.5.1\n'
           '                Group: Grp_Director_Comments_6\n'
           '                Properties:\n'
           '                  FontWeight: =FontWeight.Semibold\n'
           '                  Size: =14\n'
           f'                  Text: =If({IS_ON_HOLD}, "QTY Passed (100% Inspection)", "Reason")\n')
    assert old in yaml_text, 'Y5 fail'
    yaml_text = yaml_text.replace(old, new, 1); changes += 1
    print('Y5: Label dynamic')

    # --- Y6. txt_Reason: conditional Height, Y, HintText ---
    old = ('- txt_Reason:\n'
           '                Control: Classic/TextInput@2.3.2\n'
           '                Group: Grp_Director_Comments_6\n'
           '                Properties:\n'
           '                  BorderColor: =RGBA(64, 52, 118, 1)\n'
           '                  Default: =\n'
           '                  Height: =159\n'
           '                  HintText: =\n'
           '                  HoverBorderColor: =RGBA(64, 52, 118, 1)\n'
           '                  Mode: =TextMode.MultiLine\n'
           '                  OnChange: =Set(gblReasonText, Self.Text)\n'
           '                  Reset: =gblReset\n'
           '                  Width: =493\n'
           '                  X: =28\n'
           '                  Y: =100')
    new = ('- txt_Reason:\n'
           '                Control: Classic/TextInput@2.3.2\n'
           '                Group: Grp_Director_Comments_6\n'
           '                Properties:\n'
           '                  BorderColor: =RGBA(64, 52, 118, 1)\n'
           '                  Default: =\n'
           f'                  Height: =If({IS_ON_HOLD}, 100, 159)\n'
           f'                  HintText: =If({IS_ON_HOLD}, "Enter release reason, e.g. 100% inspection performed", "")\n'
           '                  HoverBorderColor: =RGBA(64, 52, 118, 1)\n'
           '                  Mode: =TextMode.MultiLine\n'
           '                  OnChange: =Set(gblReasonText, Self.Text)\n'
           '                  Reset: =gblReset\n'
           '                  Width: =493\n'
           '                  X: =28\n'
           f'                  Y: =If({IS_ON_HOLD}, 130, 100)')
    assert old in yaml_text, 'Y6 fail'
    yaml_text = yaml_text.replace(old, new, 1); changes += 1
    print('Y6: txt_Reason conditional')

    # --- Y7. Add txt_QTY control (after txt_Reason, before lbl_New_Section_SEL_28) ---
    insert_marker = '            - lbl_New_Section_SEL_28:\n'
    assert insert_marker in yaml_text, 'Y7 marker fail'
    txt_qty_yaml = (
        '            - txt_QTY:\n'
        '                Control: Classic/TextInput@2.3.2\n'
        '                Group: Grp_Director_Comments_6\n'
        '                Properties:\n'
        '                  BorderColor: =RGBA(64, 52, 118, 1)\n'
        '                  Default: =\n'
        '                  Height: =36\n'
        f'                  HintText: ="Enter total QTY passed"\n'
        '                  HoverBorderColor: =RGBA(64, 52, 118, 1)\n'
        '                  Mode: =TextMode.SingleLine\n'
        '                  Reset: =gblReset\n'
        f'                  Visible: ={IS_ON_HOLD}\n'
        '                  Width: =493\n'
        '                  X: =28\n'
        '                  Y: =85\n'
    )
    yaml_text = yaml_text.replace(insert_marker, txt_qty_yaml + insert_marker, 1)
    changes += 1
    print('Y7: txt_QTY added')

    # --- Y8. Release Patch: use txt_QTY.Text for QTY, keep txt_Reason for memo ---
    old_rel = (
        "DispositionStatus: {Value: \"Accepted\"},\n"
        "                                DispositionDate: Today(),\n"
        "                                DispositionReason: If(IsBlank(RecordsGallery1.Selected.DispositionReason),\n"
        "                                Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & gblReasonText,\n"
        "                                RecordsGallery1.Selected.DispositionReason & Char(10) & Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & gblReasonText),\n"
        "                                'Notes / Observations': If(IsBlank(RecordsGallery1.Selected.'Notes / Observations'),\n"
        "                                Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & gblReasonText,\n"
        "                                RecordsGallery1.Selected.'Notes / Observations' & Char(10) & Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & gblReasonText)\n"
        "                            }"
    )
    new_rel = (
        "DispositionStatus: {Value: \"Accepted\"},\n"
        "                                DispositionDate: Today(),\n"
        "                                'Release Confirmation': {Value: \"Released to inventory / warehouse location\"},\n"
        "                                'Hold Reason': Blank(),\n"
        "                                '100% inspection total QTY passed': txt_QTY.Text,\n"
        "                                DispositionReason: If(IsBlank(RecordsGallery1.Selected.DispositionReason),\n"
        "                                Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & txt_QTY.Text & \" units passed - \" & gblReasonText,\n"
        "                                RecordsGallery1.Selected.DispositionReason & Char(10) & Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & txt_QTY.Text & \" units passed - \" & gblReasonText),\n"
        "                                'Notes / Observations': If(IsBlank(RecordsGallery1.Selected.'Notes / Observations'),\n"
        "                                Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & txt_QTY.Text & \" units passed - \" & gblReasonText,\n"
        "                                RecordsGallery1.Selected.'Notes / Observations' & Char(10) & Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & txt_QTY.Text & \" units passed - \" & gblReasonText)\n"
        "                            }"
    )
    assert old_rel in yaml_text, 'Y8 fail'
    yaml_text = yaml_text.replace(old_rel, new_rel, 1); changes += 1
    print('Y8: Release Patch with txt_QTY + Release Confirmation')

    # --- Y9. Release email: QTY row from txt_QTY ---
    rel_marker = "Inspection Hold Removed:"
    rel_idx = yaml_text.find(rel_marker)
    assert rel_idx != -1, 'Y9a fail'
    old_reason = ("<tr><td style='padding:5px;font-weight:bold;width:40%;'>Reason</td>"
                  "<td style='padding:5px;'>\" & gblReasonText & \"</td></tr>"
                  "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Actioned By</td>")
    pos = yaml_text.find(old_reason, rel_idx)
    assert pos != -1, 'Y9b fail'
    new_reason = ("<tr><td style='padding:5px;font-weight:bold;width:40%;'>QTY Passed</td>"
                  "<td style='padding:5px;'>\" & txt_QTY.Text & \"</td></tr>"
                  "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Reason</td>"
                  "<td style='padding:5px;'>\" & gblReasonText & \"</td></tr>"
                  "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Actioned By</td>")
    yaml_text = yaml_text[:pos] + new_reason + yaml_text[pos + len(old_reason):]
    changes += 1
    print('Y9: Release email QTY row')

    # --- Y10. Auto-hold email: Quantity row ---
    ah_marker = "Inspection Auto-Hold (AQL Fail):"
    ah_idx = yaml_text.find(ah_marker)
    assert ah_idx != -1, 'Y10 fail'
    ah_id = "<tr><td style='font-weight:bold;'>ID</td><td>\" & Text(Form1.LastSubmit.ID) & \"</td></tr>"
    ah_pos = yaml_text.find(ah_id, ah_idx)
    assert ah_pos != -1, 'Y10b fail'
    ah_new = (ah_id +
              "<tr><td style='font-weight:bold;'>Quantity</td><td>\" & Text(Form1.LastSubmit.'Quantity Recieved') & \"</td></tr>")
    yaml_text = yaml_text[:ah_pos] + ah_new + yaml_text[ah_pos + len(ah_id):]
    changes += 1
    print('Y10: Auto-hold email Quantity')

    # --- Y11. Hold set email: Quantity row ---
    hs_marker = "Inspection Record On Hold:"
    hs_idx = yaml_text.find(hs_marker)
    assert hs_idx != -1, 'Y11 fail'
    hs_old = ("<tr><td style='padding:5px;font-weight:bold;width:40%;'>Reason</td>"
              "<td style='padding:5px;'>\" & gblReasonText & \"</td></tr>"
              "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Actioned By</td>")
    hs_pos = yaml_text.find(hs_old, hs_idx)
    assert hs_pos != -1, 'Y11b fail'
    hs_new = ("<tr><td style='padding:5px;font-weight:bold;width:40%;'>Reason</td>"
              "<td style='padding:5px;'>\" & gblReasonText & \"</td></tr>"
              "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Quantity</td>"
              "<td style='padding:5px;'>\" & Text(RecordsGallery1.Selected.'Quantity Recieved') & \"</td></tr>"
              "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Actioned By</td>")
    yaml_text = yaml_text[:hs_pos] + hs_new + yaml_text[hs_pos + len(hs_old):]
    changes += 1
    print('Y11: Hold set email Quantity')

    # --- Y12. Fix minSS for Level I (use same table as critSS) ---
    old_min = "minSS: If(lv = 1, If(lotN<2,0,lotN<=90,3,lotN<=280,13,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125),"
    new_min = "minSS: If(lv = 1, If(lotN<2,0,lotN<=8,2,lotN<=15,2,lotN<=25,3,lotN<=50,5,lotN<=90,5,lotN<=150,8,lotN<=280,13,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125),"
    assert old_min in yaml_text, 'Y12 fail'
    yaml_text = yaml_text.replace(old_min, new_min, 1); changes += 1
    print('Y12: minSS Level I fixed (base code letter)')

    # --- Y13. Fix majSS for Level I (use same table as critSS) ---
    old_maj = "majSS: If(lv = 1, If(lotN<2,0,lotN<=150,5,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125),"
    new_maj = "majSS: If(lv = 1, If(lotN<2,0,lotN<=8,2,lotN<=15,2,lotN<=25,3,lotN<=50,5,lotN<=90,5,lotN<=150,8,lotN<=280,13,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125),"
    assert old_maj in yaml_text, 'Y13 fail'
    yaml_text = yaml_text.replace(old_maj, new_maj, 1); changes += 1
    print('Y13: majSS Level I fixed (base code letter)')

    # --- Y14. Fix Ac formula: d=-1 should give Ac=1 (not 0) per Z1.4 Table II-A ---
    # This appears twice (once for majAc, once for minAc)
    old_ac = "If(d<0,0,d=0,1,d=1,2,d=2,3,d=3,5,d=4,7,d=5,10,d=6,14,21)"
    new_ac = "If(d<-1,0,Or(d=-1,d=0),1,d=1,2,d=2,3,d=3,5,d=4,7,d=5,10,d=6,14,21)"
    ac_count = yaml_text.count(old_ac)
    assert ac_count == 2, f'Y14 fail: expected 2 occurrences, found {ac_count}'
    yaml_text = yaml_text.replace(old_ac, new_ac)
    changes += 1
    print(f'Y14: Ac formula fixed (d=-1→Ac=1), {ac_count} occurrences')

    # --- Y15. Move popup label up (lbl_Director_Comments_6 Y from 60 to 56) ---
    # The label Y=60 is a bit too close to the QTY input at Y=85
    old_lbl_y = ('                  Width: =480\n'
                 '                  X: =28\n'
                 '                  Y: =60')
    new_lbl_y = ('                  Width: =480\n'
                 '                  X: =28\n'
                 '                  Y: =56')
    if old_lbl_y in yaml_text:
        yaml_text = yaml_text.replace(old_lbl_y, new_lbl_y, 1)
        changes += 1
        print('Y15: Popup label moved up')
    else:
        print('Y15: Label Y marker not found (non-critical)')

    yaml_data = yaml_text.encode('utf-8')
    print(f'YAML: {changes} changes')

    # ============================================================
    # JSON CHANGES (programmatic)
    # ============================================================

    # --- J1. Form1 OnSuccess: Hold Reason + Refresh + Qty email ---
    form1 = find_control(json_data, "Form1")
    assert form1, 'J1 fail'
    os_script = get_rule(form1, "OnSuccess")

    # Hold Reason as SEPARATE Patch (avoid Blank() crash on Choice columns)
    # Find end of main Patch and add separate Hold Reason Patch after it
    patch_end_marker = 'pending sorting or rework", ""))});'
    if patch_end_marker not in os_script:
        patch_end_marker = "pending sorting or rework\", \"\")))});"
    pe_idx = os_script.find(patch_end_marker)
    if pe_idx != -1:
        insert_pos = pe_idx + len(patch_end_marker)
        hold_reason_patch = ("\nIf(gblIsFail, Patch([@'Incoming/In process & Final Inspections'], "
                            "LookUp([@'Incoming/In process & Final Inspections'], ID = Form1.LastSubmit.ID), "
                            "{'Hold Reason': {Value: \"Hold for 100% Sorting\"}}));")
        os_script = os_script[:insert_pos] + hold_reason_patch + os_script[insert_pos:]
        print('J1a: Hold Reason as separate Patch')
    else:
        print('J1a: Patch end marker not found (non-critical)')

    # Add Refresh
    warn_end = 'Notify("Hold notification email failed.", NotificationType.Warning)))'
    vf = 'ViewForm(Form1);'
    warn_idx = os_script.find(warn_end)
    vf_idx = os_script.find(vf, warn_idx)
    assert warn_idx != -1 and vf_idx != -1, 'J1b fail'
    sep = os_script[warn_idx + len(warn_end):vf_idx]
    os_script = (os_script[:warn_idx + len(warn_end)] + sep +
                 "If(gblIsFail, Refresh([@'Incoming/In process & Final Inspections']));" + sep +
                 os_script[vf_idx:])

    # Quantity in auto-hold email
    ah_id_j = "<tr><td style='font-weight:bold;'>ID</td><td>\" & Text(Form1.LastSubmit.ID) & \"</td></tr>"
    ah_qty_j = (ah_id_j +
                "<tr><td style='font-weight:bold;'>Quantity</td><td>\" & Text(Form1.LastSubmit.'Quantity Recieved') & \"</td></tr>")
    os_script = os_script.replace(ah_id_j, ah_qty_j, 1)

    set_rule(form1, "OnSuccess", os_script, "Behavior")
    print('J1: OnSuccess updated')

    # --- J2. DataCardValue23: Visible=false ---
    dcv23 = find_control(json_data, "DataCardValue23")
    assert dcv23, 'J2 fail'
    set_rule(dcv23, "Visible", "false", "Design")
    print('J2: DataCardValue23 hidden')

    # --- J3. Headerlbl_41 Text ---
    h41 = find_control(json_data, "Headerlbl_41")
    set_rule(h41, "Text", f'If({IS_ON_HOLD}, "Release Hold", "Hold Request")', "Data")
    print('J3: Header dynamic')

    # --- J4. lbl_Director_Comments_6 Text ---
    lbl = find_control(json_data, "lbl_Director_Comments_6")
    set_rule(lbl, "Text", f'If({IS_ON_HOLD}, "QTY Passed (100% Inspection)", "Reason")', "Data")
    print('J4: Label dynamic')

    # --- J5. txt_Reason: Height, Y, HintText ---
    txt_r = find_control(json_data, "txt_Reason")
    set_rule(txt_r, "Height", f'If({IS_ON_HOLD}, 100, 159)', "Design")
    set_rule(txt_r, "Y", f'If({IS_ON_HOLD}, 130, 100)', "Design")
    set_rule(txt_r, "HintText", f'If({IS_ON_HOLD}, "Enter release reason, e.g. 100% inspection performed", "")', "Data")
    print('J5: txt_Reason conditional')

    # --- J6. Add txt_QTY control (clone txt_Reason, modify) ---
    txt_qty = copy.deepcopy(txt_r)
    txt_qty["Name"] = "txt_QTY"
    txt_qty["PublishOrderIndex"] = 280
    set_rule(txt_qty, "Height", "36", "Design")
    set_rule(txt_qty, "Y", "85", "Design")
    set_rule(txt_qty, "Mode", "TextMode.SingleLine", "Design")
    set_rule(txt_qty, "HintText", '"Enter total QTY passed"', "Data")
    set_rule(txt_qty, "Visible", IS_ON_HOLD, "Design")
    set_rule(txt_qty, "Default", "", "Data")
    # Remove OnChange (don't set gblReasonText)
    for r in txt_qty.get("Rules", []):
        if r["Property"] == "OnChange":
            r["InvariantScript"] = ""
            break

    container39 = find_control(json_data, "Container2_39")
    container39["Children"].append(txt_qty)
    print('J6: txt_QTY added to JSON')

    # --- J7. btn_Submit_17 OnSelect: update release Patch ---
    btn = find_control(json_data, "btn_Submit_17")
    sel = get_rule(btn, "OnSelect")

    # Release Patch
    old_j_rel = (
        "DispositionStatus: {Value: \"Accepted\"},\n"
        "            DispositionDate: Today(),\n"
        "            DispositionReason: If(IsBlank(RecordsGallery1.Selected.DispositionReason),\n"
        "            Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & gblReasonText,\n"
        "            RecordsGallery1.Selected.DispositionReason & Char(10) & Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & gblReasonText),\n"
        "            'Notes / Observations': If(IsBlank(RecordsGallery1.Selected.'Notes / Observations'),\n"
        "            Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & gblReasonText,\n"
        "            RecordsGallery1.Selected.'Notes / Observations' & Char(10) & Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & gblReasonText)\n"
        "        }"
    )
    new_j_rel = (
        "DispositionStatus: {Value: \"Accepted\"},\n"
        "            DispositionDate: Today(),\n"
        "            'Release Confirmation': {Value: \"Released to inventory / warehouse location\"},\n"
        "            'Hold Reason': Blank(),\n"
        "            '100% inspection total QTY passed': txt_QTY.Text,\n"
        "            DispositionReason: If(IsBlank(RecordsGallery1.Selected.DispositionReason),\n"
        "            Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & txt_QTY.Text & \" units passed - \" & gblReasonText,\n"
        "            RecordsGallery1.Selected.DispositionReason & Char(10) & Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & txt_QTY.Text & \" units passed - \" & gblReasonText),\n"
        "            'Notes / Observations': If(IsBlank(RecordsGallery1.Selected.'Notes / Observations'),\n"
        "            Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & txt_QTY.Text & \" units passed - \" & gblReasonText,\n"
        "            RecordsGallery1.Selected.'Notes / Observations' & Char(10) & Text(Now(), \"[$-en-US]mm/dd/yyyy hh:mm\") & \" - Hold Released: \" & txt_QTY.Text & \" units passed - \" & gblReasonText)\n"
        "        }"
    )
    assert old_j_rel in sel, 'J7a fail'
    sel = sel.replace(old_j_rel, new_j_rel, 1)

    # Release email: QTY row
    rel_reason = ("Reason</td><td style='padding:5px;'>\" & gblReasonText & \"</td></tr>"
                  "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Actioned By</td>")
    rel_idx = sel.find("Inspection Hold Removed:")
    if rel_idx != -1:
        rp = sel.find(rel_reason, rel_idx)
        if rp != -1:
            rel_new = ("QTY Passed</td><td style='padding:5px;'>\" & txt_QTY.Text & \"</td></tr>"
                       "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Reason</td>"
                       "<td style='padding:5px;'>\" & gblReasonText & \"</td></tr>"
                       "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Actioned By</td>")
            sel = sel[:rp] + rel_new + sel[rp + len(rel_reason):]

    # Hold set email: Quantity row
    hs_reason = ("Reason</td><td style='padding:5px;'>\" & gblReasonText & \"</td></tr>"
                 "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Actioned By</td>")
    hs_idx = sel.find("Inspection Record On Hold:")
    if hs_idx != -1:
        hp = sel.find(hs_reason, hs_idx)
        if hp != -1:
            hs_new = ("Reason</td><td style='padding:5px;'>\" & gblReasonText & \"</td></tr>"
                      "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Quantity</td>"
                      "<td style='padding:5px;'>\" & Text(RecordsGallery1.Selected.'Quantity Recieved') & \"</td></tr>"
                      "<tr><td style='padding:5px;font-weight:bold;width:40%;'>Actioned By</td>")
            sel = sel[:hp] + hs_new + sel[hp + len(hs_reason):]

    set_rule(btn, "OnSelect", sel, "Behavior")
    print('J7: btn_Submit_17 OnSelect updated')

    # --- J8. Fix minSS for Level I in AQL formula ---
    # Find the AQL calculator formula in the JSON - it's in DataCardKey24's Text rule
    dck24 = find_control(json_data, "DataCardKey24")
    if dck24:
        aql_formula = get_rule(dck24, "Text")
        if aql_formula:
            old_minss = "minSS: If(lv = 1, If(lotN<2,0,lotN<=90,3,lotN<=280,13,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125),"
            new_minss = "minSS: If(lv = 1, If(lotN<2,0,lotN<=8,2,lotN<=15,2,lotN<=25,3,lotN<=50,5,lotN<=90,5,lotN<=150,8,lotN<=280,13,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125),"
            if old_minss in aql_formula:
                aql_formula = aql_formula.replace(old_minss, new_minss, 1)
                set_rule(dck24, "Text", aql_formula, "Data")
                print('J8: minSS Level I fixed in JSON')
            else:
                print('J8: minSS marker not found in JSON AQL formula')
    else:
        print('J8: DataCardKey24 not found')

    # --- J9. Fix majSS for Level I in AQL formula ---
    if dck24:
        aql_formula = get_rule(dck24, "Text")
        if aql_formula:
            old_majss = "majSS: If(lv = 1, If(lotN<2,0,lotN<=150,5,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125),"
            new_majss = "majSS: If(lv = 1, If(lotN<2,0,lotN<=8,2,lotN<=15,2,lotN<=25,3,lotN<=50,5,lotN<=90,5,lotN<=150,8,lotN<=280,13,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125),"
            if old_majss in aql_formula:
                aql_formula = aql_formula.replace(old_majss, new_majss, 1)
                set_rule(dck24, "Text", aql_formula, "Data")
                print('J9: majSS Level I fixed in JSON')
            else:
                print('J9: majSS marker not found in JSON')

    # --- J10. Fix Ac formula in AQL (d=-1 → Ac=1) ---
    if dck24:
        aql_formula = get_rule(dck24, "Text")
        if aql_formula:
            old_ac_j = "If(d<0,0,d=0,1,d=1,2,d=2,3,d=3,5,d=4,7,d=5,10,d=6,14,21)"
            new_ac_j = "If(d<-1,0,Or(d=-1,d=0),1,d=1,2,d=2,3,d=3,5,d=4,7,d=5,10,d=6,14,21)"
            ac_count_j = aql_formula.count(old_ac_j)
            if ac_count_j > 0:
                aql_formula = aql_formula.replace(old_ac_j, new_ac_j)
                set_rule(dck24, "Text", aql_formula, "Data")
                print(f'J10: Ac formula fixed in JSON ({ac_count_j} occurrences)')
            else:
                print('J10: Ac formula marker not found in JSON')

    # --- J11. Move popup label Y ---
    if lbl:
        set_rule(lbl, "Y", "56", "Design")
        print('J11: Label Y moved up')

    # Serialize JSON
    json_output = json.dumps(json_data, ensure_ascii=False, indent=2).encode('utf-8')
    json.loads(json_output)
    print(f'JSON: VALID ({len(json_output)} bytes)')

    # ============================================================
    # Build output msapp
    # ============================================================
    with open(OUTER_ZIP, 'rb') as f:
        outer_data = f.read()
    with zipfile.ZipFile(io.BytesIO(outer_data), 'r') as zf:
        msapp_data = zf.read(MSAPP_PATH)

    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(msapp_data), 'r') as src:
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as out:
            for item in src.infolist():
                if item.filename == 'Src\\MainScreen1.pa.yaml':
                    out.writestr(item, yaml_data)
                elif item.filename == 'Controls\\4.json':
                    out.writestr(item, json_output)
                else:
                    out.writestr(item, src.read(item.filename))

    with open(OUTPUT, 'wb') as f:
        f.write(buf.getvalue())
    print(f'\nOutput: {OUTPUT} ({os.path.getsize(OUTPUT)} bytes)')
    print(f'Total YAML changes: {changes}')


if __name__ == '__main__':
    build()
