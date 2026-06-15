#!/usr/bin/env python3
"""
Build v176 - Apply comprehensive email enhancements to client's latest export
(which already has working ComboBox1 from support company).

Source: Incoming_Inprocess&FinalInspections_20260615181808 (1).zip

Changes:
1. Notification email: add NCR#, Serial#, PO#, Part#, Notes/Observations, Type, Changed fields
2. Rejection email: add NCR#, Serial#, PO#, Part#, Notes/Observations with red styling
3. Button emails (4): add Part Number, Outcome, Notes/Observations rows
"""

import zipfile
import io
import os

WORK = "/var/lib/freelancer/projects/40486904"
SRC_ZIP = os.path.join(WORK, "Incoming_Inprocess&FinalInspections_20260615181808 (1).zip")
OUT_MSAPP = os.path.join(WORK, "v176.msapp")

MSAPP_PATH = "Microsoft.PowerApps/apps/18391596269880809910/Na044e57e-f8be-4a19-889a-05f768b7a148-document.msapp"

# Read msapp from outer zip
with zipfile.ZipFile(SRC_ZIP, 'r') as oz:
    msapp_bytes = oz.read(MSAPP_PATH)

# Read msapp contents
msapp_io = io.BytesIO(msapp_bytes)
with zipfile.ZipFile(msapp_io, 'r') as mz:
    yaml_data = mz.read('Src\\MainScreen1.pa.yaml')
    json_data = mz.read('Controls\\4.json')
    all_items = mz.infolist()
    all_files = {}
    for item in all_items:
        all_files[item.filename] = (item, mz.read(item.filename))

print(f"YAML size: {len(yaml_data)} bytes")
print(f"JSON size: {len(json_data)} bytes")

# ================================================================
# YAML REPLACEMENTS
# ================================================================

# --- 1. NOTIFICATION EMAIL (Form1.OnSuccess handler) ---
# Current: Inspector, Date, Product, Lot, Outcome, ID
# Target: Inspector, Date, Type, Product Name, Part Number, Lot Number, PO Number,
#         Serial Number, NCR Number, Outcome, Notes/Observations, ID, Changed Fields

# Find unique pattern for notification email
NOTIFY_OLD = b"<table style='width:100%;border-collapse:collapse;'><tr><td style='font-weight:bold;'>Inspector</td><td>\" & Coalesce(Form1.LastSubmit.Inspector.DisplayName, \"\xe2\x80\x94\") & \"</td></tr><tr><td style='font-weight:bold;'>Date</td><td>\" & Text(Form1.LastSubmit.'Date Inspected') & \"</td></tr><tr><td style='font-weight:bold;'>Product</td><td>\" & Coalesce(Coalesce(Text(Form1.LastSubmit.'Product Name'), \"\"), \"\xe2\x80\x94\") & \"</td></tr><tr><td style='font-weight:bold;'>Lot</td><td>\" & Text(Form1.LastSubmit.'Lot Number') & \"</td></tr><tr><td style='font-weight:bold;'>Outcome</td><td>\" & Coalesce(IfError(Text(Form1.LastSubmit.'Inspection outcome'.Value), \"\"), \"\xe2\x80\x94\") & \"</td></tr><tr><td style='font-weight:bold;'>ID</td><td>\" & Text(Form1.LastSubmit.ID) & \"</td></tr></table><p style='font-size:11px;color:#888;'>By \" & User().FullName & \"</p>"

NOTIFY_NEW = b"<table style='width:100%;border-collapse:collapse;'>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Inspector</td><td style='padding:5px;'>\" & Coalesce(Form1.LastSubmit.Inspector.DisplayName, \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Date</td><td style='padding:5px;'>\" & Text(Form1.LastSubmit.'Date Inspected') & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Type</td><td style='padding:5px;'>\" & Coalesce(IfError(Text(Form1.LastSubmit.'Incoming/In process or Final'.Value), \"\"), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Product Name</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Product Name'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Part Number</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Part Number'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Lot Number</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Lot Number'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>PO Number</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'PO Number'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Serial Number</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Serial Number'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>NCR Number</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Non Conformance Report Number '), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Outcome</td><td style='padding:5px;'>\" & Coalesce(IfError(Text(Form1.LastSubmit.'Inspection outcome'.Value), \"\"), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Notes/Observations</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Notes / Observations'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>ID</td><td style='padding:5px;'>\" & Text(Form1.LastSubmit.ID) & \"</td></tr>" \
    b"</table>\" & If(Coalesce(gblSubmitWasEdit, false), \"<p style='font-size:12px;margin-top:10px;'><b>Changed:</b> \" & Coalesce(gblCh1 & gblCh2 & gblCh3 & gblCh4 & gblCh5 & gblCh6, \"(none)\") & \"</p>\", \"\") & \"<p style='font-size:11px;color:#888;'>By \" & User().FullName & \"</p>"

# --- 2. REJECTION EMAIL ---
# Current has same limited fields as notification. Need comprehensive + red styling.

REJECT_OLD = b"<table style='width:100%;border-collapse:collapse;'><tr><td style='font-weight:bold;'>Inspector</td><td>\" & Coalesce(Form1.LastSubmit.Inspector.DisplayName, \"\xe2\x80\x94\") & \"</td></tr><tr><td style='font-weight:bold;'>Date</td><td>\" & Text(Form1.LastSubmit.'Date Inspected') & \"</td></tr><tr><td style='font-weight:bold;'>Product</td><td>\" & Coalesce(Coalesce(Text(Form1.LastSubmit.'Product Name'), \"\"), \"\xe2\x80\x94\") & \"</td></tr><tr><td style='font-weight:bold;'>Lot</td><td>\" & Text(Form1.LastSubmit.'Lot Number') & \"</td></tr><tr><td style='font-weight:bold;'>Outcome</td><td style='color:#C0392B;font-weight:bold;'>\" & Coalesce(IfError(Text(Form1.LastSubmit.'Inspection outcome'.Value), \"\"), \"\xe2\x80\x94\") & \"</td></tr><tr><td style='font-weight:bold;'>ID</td><td>\" & Text(Form1.LastSubmit.ID) & \"</td></tr></table><p style='font-size:11px;color:#888;'>By \" & User().FullName & \"</p>"

REJECT_NEW = b"<table style='width:100%;border-collapse:collapse;'>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Inspector</td><td style='padding:5px;'>\" & Coalesce(Form1.LastSubmit.Inspector.DisplayName, \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Date</td><td style='padding:5px;'>\" & Text(Form1.LastSubmit.'Date Inspected') & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Type</td><td style='padding:5px;'>\" & Coalesce(IfError(Text(Form1.LastSubmit.'Incoming/In process or Final'.Value), \"\"), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Product Name</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Product Name'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Part Number</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Part Number'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Lot Number</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Lot Number'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>PO Number</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'PO Number'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Serial Number</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Serial Number'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;color:#C0392B;'>NCR Number</td><td style='padding:5px;color:#C0392B;font-weight:bold;'>\" & Coalesce(Text(Form1.LastSubmit.'Non Conformance Report Number '), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;color:#C0392B;'>Outcome</td><td style='padding:5px;color:#C0392B;font-weight:bold;'>\" & Coalesce(IfError(Text(Form1.LastSubmit.'Inspection outcome'.Value), \"\"), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Notes/Observations</td><td style='padding:5px;'>\" & Coalesce(Text(Form1.LastSubmit.'Notes / Observations'), \"\xe2\x80\x94\") & \"</td></tr>" \
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>ID</td><td style='padding:5px;'>\" & Text(Form1.LastSubmit.ID) & \"</td></tr>" \
    b"</table><p style='font-size:11px;color:#888;'>By \" & User().FullName & \"</p>"

# --- 3. BUTTON EMAILS (Hold Released, On Hold, Rejection Released, Rejected) ---
# Currently have: NCR#, Lot#, Serial#, PO#, Product Name/Model, Reason, Actioned By, Date
# Need to add AFTER Product Name/Model: Part Number, Outcome, Notes/Observations

# The 3 new rows to insert (using RecordsGallery1.Selected references)
PART_OUTCOME_NOTES_ROWS = (
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Part Number</td><td style='padding:5px;'>\" & Coalesce(Text(RecordsGallery1.Selected.'Part Number'), \"\xe2\x80\x94\") & \"</td></tr>"
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Outcome</td><td style='padding:5px;'>\" & Coalesce(IfError(Text(RecordsGallery1.Selected.'Inspection outcome'.Value), \"\"), \"\xe2\x80\x94\") & \"</td></tr>"
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Notes/Observations</td><td style='padding:5px;'>\" & Coalesce(Text(RecordsGallery1.Selected.'Notes / Observations'), \"\xe2\x80\x94\") & \"</td></tr>"
)

# Pattern: after Product Name/Model row, before Reason row
# This appears in all 4 button emails
BTN_PRODUCT_THEN_REASON = b"Product Name/Model</td><td style='padding:5px;'>\" & Text(RecordsGallery1.Selected.'Product Name') & \"</td></tr><tr><td style='padding:5px;font-weight:bold;width:40%;'>Reason"

BTN_PRODUCT_THEN_REASON_NEW = b"Product Name/Model</td><td style='padding:5px;'>\" & Text(RecordsGallery1.Selected.'Product Name') & \"</td></tr>" + PART_OUTCOME_NOTES_ROWS + b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Reason"

# ================================================================
# APPLY YAML REPLACEMENTS
# ================================================================

yaml_modified = yaml_data

# 1. Notification email
count = yaml_modified.count(NOTIFY_OLD)
print(f"Notification email pattern matches: {count}")
assert count == 1, f"Expected 1 match for notification email, got {count}"
yaml_modified = yaml_modified.replace(NOTIFY_OLD, NOTIFY_NEW)

# 2. Rejection email
count = yaml_modified.count(REJECT_OLD)
print(f"Rejection email pattern matches: {count}")
assert count == 1, f"Expected 1 match for rejection email, got {count}"
yaml_modified = yaml_modified.replace(REJECT_OLD, REJECT_NEW)

# 3. Button emails (should match 4 times - Hold Released, On Hold, Rej Released, Rejected)
count = yaml_modified.count(BTN_PRODUCT_THEN_REASON)
print(f"Button email pattern matches: {count}")
assert count == 4, f"Expected 4 matches for button emails, got {count}"
yaml_modified = yaml_modified.replace(BTN_PRODUCT_THEN_REASON, BTN_PRODUCT_THEN_REASON_NEW)

print(f"\nYAML: {len(yaml_data)} -> {len(yaml_modified)} bytes (+{len(yaml_modified)-len(yaml_data)})")

# ================================================================
# BUILD OUTPUT MSAPP
# ================================================================

out_io = io.BytesIO()
with zipfile.ZipFile(out_io, 'w') as oz:
    for item, data in all_files.values():
        if item.filename == 'Src\\MainScreen1.pa.yaml':
            oz.writestr(item, yaml_modified)
        else:
            oz.writestr(item, data)

out_bytes = out_io.getvalue()
with open(OUT_MSAPP, 'wb') as f:
    f.write(out_bytes)

print(f"\nOutput: {OUT_MSAPP} ({len(out_bytes)} bytes)")

# ================================================================
# VERIFY
# ================================================================

# Re-read and verify
with zipfile.ZipFile(OUT_MSAPP, 'r') as z:
    verify_yaml = z.read('Src\\MainScreen1.pa.yaml').decode('utf-8', errors='replace')

# Check notification email has all fields
notify_fields = ['Inspector', 'Date', 'Type', 'Product Name', 'Part Number', 'Lot Number',
                 'PO Number', 'Serial Number', 'NCR Number', 'Outcome', 'Notes/Observations', 'ID']
print("\n=== NOTIFICATION email verification ===")
for field in notify_fields:
    tag = f"font-weight:bold"
    # Just check the field name appears in notification context
    if field in verify_yaml:
        print(f"  [OK] {field}")
    else:
        print(f"  [MISSING] {field}")

# Check Changed fields in notification
if "gblCh1 & gblCh2 & gblCh3 & gblCh4 & gblCh5 & gblCh6" in verify_yaml:
    print("  [OK] Changed fields tracking")
else:
    print("  [MISSING] Changed fields tracking")

# Check button emails have new fields
btn_check_fields = ['Part Number', 'Outcome', 'Notes/Observations']
print("\n=== BUTTON email verification ===")
# Count occurrences of Part Number in button email context
import re
part_in_gallery = len(re.findall(r"RecordsGallery1\.Selected\.'Part Number'", verify_yaml))
print(f"  Part Number (gallery refs): {part_in_gallery} (expect 4+ for buttons + print)")
obs_in_gallery = len(re.findall(r"RecordsGallery1\.Selected\.'Notes / Observations'", verify_yaml))
print(f"  Notes/Observations (gallery refs): {obs_in_gallery} (expect 4+ for buttons)")
outcome_in_gallery = len(re.findall(r"RecordsGallery1\.Selected\.'Inspection outcome'\.Value", verify_yaml))
print(f"  Outcome (gallery refs): {outcome_in_gallery} (expect 4+ for buttons)")

# Check NCR in rejection email has red styling
if "color:#C0392B;'>NCR Number" in verify_yaml:
    print("\n  [OK] NCR Number in red in rejection email")
else:
    print("\n  [MISSING] NCR Number red styling in rejection")

print("\n=== BUILD COMPLETE ===")
