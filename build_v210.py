#!/usr/bin/env python3
"""v210: Auto-hold on AQL fail + hold button visible to all users.
Source: June 21 export (already has v209 AQL fixes baked in).

Changes:
1. Auto-hold on fail: DispositionStatus → "On Hold" instead of "Rejected"
2. Auto-hold note logged in Notes/Observations
3. Fail email changed from red "Rejected" to orange "Auto-Hold"
4. Hold button visible to ALL users (not just admins)
"""
import zipfile, io, os, json

PROJECT_DIR = '/var/lib/freelancer/projects/40486904'
OUTER_ZIP = os.path.join(PROJECT_DIR, 'Incoming_Inprocess&FinalInspections_20260621104412.zip')
MSAPP_PATH = 'Microsoft.PowerApps/apps/18391596269880809910/N3f615a81-54f8-4903-a655-a82f398a3cf6-document.msapp'
OUTPUT = os.path.join(PROJECT_DIR, 'v210_aql.msapp')


def build():
    # Read source files from extracted msapp
    msapp_dir = os.path.join(PROJECT_DIR, 'june21_msapp')
    with open(os.path.join(msapp_dir, 'Src', 'MainScreen1.pa.yaml'), 'r', encoding='utf-8') as f:
        yaml_text = f.read()
    with open(os.path.join(msapp_dir, 'Controls', '4.json'), 'rb') as f:
        json_data = f.read()

    changes = 0

    # ============================================================
    # YAML CHANGES
    # ============================================================

    # 1. Auto-hold on fail: Change Patch DispositionStatus from "Rejected" to "On Hold"
    #    and add auto-hold note to Notes/Observations
    old_patch = (
        '{DispositionStatus: If(gblIsFail, {Value: "Rejected"}, {Value: "Accepted"}), '
        "'Notes / Observations': If(IsBlank(Form1.LastSubmit.'Notes / Observations'), "
        "gblNoteEntry, Form1.LastSubmit.'Notes / Observations' & Char(10) & gblNoteEntry)}"
    )
    new_patch = (
        '{DispositionStatus: If(gblIsFail, {Value: "On Hold"}, {Value: "Accepted"}), '
        "'Notes / Observations': If(IsBlank(Form1.LastSubmit.'Notes / Observations'), "
        'gblNoteEntry & If(gblIsFail, Char(10) & Text(Now(), "[$-en-US]mm/dd/yyyy hh:mm") & " - Auto-hold: AQL Fail - pending sorting or rework", ""), '
        "Form1.LastSubmit.'Notes / Observations' & Char(10) & gblNoteEntry & "
        'If(gblIsFail, Char(10) & Text(Now(), "[$-en-US]mm/dd/yyyy hh:mm") & " - Auto-hold: AQL Fail - pending sorting or rework", ""))}'
    )
    assert old_patch in yaml_text, 'YAML: Patch marker not found'
    yaml_text = yaml_text.replace(old_patch, new_patch, 1)
    changes += 1
    print('YAML [1/5]: Patch → On Hold + auto-hold note')

    # 2. Fail email subject: "Rejected" → "Auto-Hold"
    old_subj = '"Inspection Record Rejected: " & gblTitleLine'
    new_subj = '"Inspection Auto-Hold (AQL Fail): " & gblTitleLine'
    assert old_subj in yaml_text, 'YAML: Fail email subject not found'
    yaml_text = yaml_text.replace(old_subj, new_subj, 1)
    changes += 1
    print('YAML [2/5]: Fail email subject → Auto-Hold')

    # 3. Fail email body: red Rejected → orange Auto-Hold
    old_body = (
        "<div style='background:#C0392B;padding:12px 16px;'>"
        "<span style='color:white;font-size:15px;font-weight:bold;'>Inspection Record Rejected</span></div>"
        "<div style='padding:16px;border:1px solid #ddd;'>"
        "<p style='color:#C0392B;font-weight:bold;'>This inspection has been rejected.</p>"
    )
    new_body = (
        "<div style='background:#E67E22;padding:12px 16px;'>"
        "<span style='color:white;font-size:15px;font-weight:bold;'>Inspection Auto-Hold: AQL Fail</span></div>"
        "<div style='padding:16px;border:1px solid #ddd;'>"
        "<p style='color:#E67E22;font-weight:bold;'>This inspection has failed and been automatically placed on hold pending sorting or rework.</p>"
    )
    assert old_body in yaml_text, 'YAML: Fail email body not found'
    yaml_text = yaml_text.replace(old_body, new_body, 1)
    changes += 1
    print('YAML [3/5]: Fail email body → orange Auto-Hold')

    # 4. Fail notify message
    old_notify = 'Notify("Rejection email failed.", NotificationType.Warning)'
    new_notify = 'Notify("Hold notification email failed.", NotificationType.Warning)'
    assert old_notify in yaml_text, 'YAML: Fail notify not found'
    yaml_text = yaml_text.replace(old_notify, new_notify, 1)
    changes += 1
    print('YAML [4/5]: Fail notify text updated')

    # 5. HoldButton1 Visible: remove gblAdminEmails check (visible to all users)
    #    Must change ONLY HoldButton1's Visible, not RejectButton1's
    tooltip_marker = '="Place record On Hold"'
    tip_idx = yaml_text.find(tooltip_marker)
    assert tip_idx != -1, 'YAML: HoldButton1 tooltip not found'

    old_vis = '=And(!editMode, !deleteMode, !newMode, User().Email in gblAdminEmails)'
    vis_idx = yaml_text.find(old_vis, tip_idx)
    assert vis_idx != -1 and vis_idx - tip_idx < 300, f'YAML: HoldButton1 Visible not found near tooltip'

    new_vis = '=And(!editMode, !deleteMode, !newMode)'
    yaml_text = yaml_text[:vis_idx] + new_vis + yaml_text[vis_idx + len(old_vis):]
    changes += 1
    print('YAML [5/5]: HoldButton1 visible to all users')

    yaml_data = yaml_text.encode('utf-8')

    # ============================================================
    # JSON CHANGES (same changes, binary-safe)
    # ============================================================

    # 1. Patch: "Rejected" → "On Hold" + auto-hold note
    old_j = b'gblIsFail, {Value: \\"Rejected\\"}, {Value: \\"Accepted\\"}), \'Notes / Observations\': If(IsBlank(Form1.LastSubmit.\'Notes / Observations\'), gblNoteEntry, Form1.LastSubmit.\'Notes / Observations\' & Char(10) & gblNoteEntry)}'
    new_j = (
        b'gblIsFail, {Value: \\"On Hold\\"}, {Value: \\"Accepted\\"}), \'Notes / Observations\': If(IsBlank(Form1.LastSubmit.\'Notes / Observations\'), '
        b'gblNoteEntry & If(gblIsFail, Char(10) & Text(Now(), \\"[$-en-US]mm/dd/yyyy hh:mm\\") & \\" - Auto-hold: AQL Fail - pending sorting or rework\\", \\"\\"), '
        b'Form1.LastSubmit.\'Notes / Observations\' & Char(10) & gblNoteEntry & '
        b'If(gblIsFail, Char(10) & Text(Now(), \\"[$-en-US]mm/dd/yyyy hh:mm\\") & \\" - Auto-hold: AQL Fail - pending sorting or rework\\", \\"\\"))}'
    )
    assert old_j in json_data, 'JSON: Patch marker not found'
    json_data = json_data.replace(old_j, new_j, 1)
    print('JSON [1/5]: Patch → On Hold + auto-hold note')

    # 2. Fail email subject
    old_j_subj = b'\\"Inspection Record Rejected: \\" & gblTitleLine'
    new_j_subj = b'\\"Inspection Auto-Hold (AQL Fail): \\" & gblTitleLine'
    assert old_j_subj in json_data, 'JSON: Fail email subject not found'
    json_data = json_data.replace(old_j_subj, new_j_subj, 1)
    print('JSON [2/5]: Fail email subject → Auto-Hold')

    # 3. Fail email body (find after the new subject to target the right occurrence)
    old_j_body = (
        b"<div style='background:#C0392B;padding:12px 16px;'>"
        b"<span style='color:white;font-size:15px;font-weight:bold;'>Inspection Record Rejected</span></div>"
        b"<div style='padding:16px;border:1px solid #ddd;'>"
        b"<p style='color:#C0392B;font-weight:bold;'>This inspection has been rejected.</p>"
    )
    new_j_body = (
        b"<div style='background:#E67E22;padding:12px 16px;'>"
        b"<span style='color:white;font-size:15px;font-weight:bold;'>Inspection Auto-Hold: AQL Fail</span></div>"
        b"<div style='padding:16px;border:1px solid #ddd;'>"
        b"<p style='color:#E67E22;font-weight:bold;'>This inspection has failed and been automatically placed on hold pending sorting or rework.</p>"
    )
    subj_pos = json_data.find(new_j_subj)
    body_pos = json_data.find(old_j_body, subj_pos)
    assert body_pos != -1, 'JSON: Fail email body not found after subject'
    json_data = json_data[:body_pos] + new_j_body + json_data[body_pos + len(old_j_body):]
    print('JSON [3/5]: Fail email body → orange Auto-Hold')

    # 4. Fail notify
    old_j_notify = b'\\"Rejection email failed.\\"'
    new_j_notify = b'\\"Hold notification email failed.\\"'
    notify_pos = json_data.find(old_j_notify, body_pos)
    if notify_pos != -1 and notify_pos - body_pos < 2000:
        json_data = json_data[:notify_pos] + new_j_notify + json_data[notify_pos + len(old_j_notify):]
        print('JSON [4/5]: Fail notify updated')
    else:
        print('JSON [4/5]: Fail notify not found (non-critical)')

    # 5. HoldButton1 Visible (find after HoldButton1 definition, not RejectButton1)
    hold_def = json_data.find(b'HoldButton1')
    assert hold_def != -1, 'JSON: HoldButton1 not found'
    old_j_vis = b'And(!editMode, !deleteMode, !newMode, User().Email in gblAdminEmails)'
    vis_pos = json_data.find(old_j_vis, hold_def)
    assert vis_pos != -1 and vis_pos - hold_def < 10000, 'JSON: HoldButton1 Visible not found'
    new_j_vis = b'And(!editMode, !deleteMode, !newMode)'
    json_data = json_data[:vis_pos] + new_j_vis + json_data[vis_pos + len(old_j_vis):]
    print('JSON [5/5]: HoldButton1 visible to all users')

    # Validate JSON
    json.loads(json_data)
    print('JSON: VALID')

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
                    out.writestr(item, json_data)
                else:
                    out.writestr(item, src.read(item.filename))

    with open(OUTPUT, 'wb') as f:
        f.write(buf.getvalue())
    print(f'\nOutput: {OUTPUT} ({os.path.getsize(OUTPUT)} bytes)')
    print(f'Changes: {changes} YAML + 5 JSON = done')


if __name__ == '__main__':
    build()
