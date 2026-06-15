#!/usr/bin/env python3
"""
Build v180 - all changes + email subjects use Lot Number instead of Title.

Source: Incoming_Inprocess&FinalInspections_20260615181808 (1).zip
"""

import zipfile
import io
import os
import re

WORK = "/var/lib/freelancer/projects/40486904"
SRC_ZIP = os.path.join(WORK, "Incoming_Inprocess&FinalInspections_20260615181808 (1).zip")
OUT_MSAPP = os.path.join(WORK, "v180.msapp")

MSAPP_PATH = "Microsoft.PowerApps/apps/18391596269880809910/Na044e57e-f8be-4a19-889a-05f768b7a148-document.msapp"

# Read msapp from outer zip
with zipfile.ZipFile(SRC_ZIP, 'r') as oz:
    msapp_bytes = oz.read(MSAPP_PATH)

msapp_io = io.BytesIO(msapp_bytes)
with zipfile.ZipFile(msapp_io, 'r') as mz:
    yaml_data = mz.read('Src\\MainScreen1.pa.yaml')
    json_data = mz.read('Controls\\4.json')
    all_files = {}
    for item in mz.infolist():
        all_files[item.filename] = (item, mz.read(item.filename))

print(f"YAML: {len(yaml_data)} bytes | JSON: {len(json_data)} bytes")

# ================================================================
# YAML REPLACEMENTS
# ================================================================
yaml_mod = yaml_data

# --- EMAIL ENHANCEMENTS (same as v176) ---

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

PART_OUTCOME_NOTES_ROWS = (
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Part Number</td><td style='padding:5px;'>\" & Coalesce(Text(RecordsGallery1.Selected.'Part Number'), \"\xe2\x80\x94\") & \"</td></tr>"
    b"<tr style='background:#f9f9f9;'><td style='padding:5px;font-weight:bold;width:40%;'>Outcome</td><td style='padding:5px;'>\" & Coalesce(IfError(Text(RecordsGallery1.Selected.'Inspection outcome'.Value), \"\"), \"\xe2\x80\x94\") & \"</td></tr>"
    b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Notes/Observations</td><td style='padding:5px;'>\" & Coalesce(Text(RecordsGallery1.Selected.'Notes / Observations'), \"\xe2\x80\x94\") & \"</td></tr>"
)

BTN_PRODUCT_THEN_REASON = b"Product Name/Model</td><td style='padding:5px;'>\" & Text(RecordsGallery1.Selected.'Product Name') & \"</td></tr><tr><td style='padding:5px;font-weight:bold;width:40%;'>Reason"
BTN_PRODUCT_THEN_REASON_NEW = b"Product Name/Model</td><td style='padding:5px;'>\" & Text(RecordsGallery1.Selected.'Product Name') & \"</td></tr>" + PART_OUTCOME_NOTES_ROWS + b"<tr><td style='padding:5px;font-weight:bold;width:40%;'>Reason"

# Apply email changes
c = yaml_mod.count(NOTIFY_OLD)
assert c == 1, f"Notify: expected 1, got {c}"
yaml_mod = yaml_mod.replace(NOTIFY_OLD, NOTIFY_NEW)
print(f"[YAML] Notification email: 1 match replaced")

c = yaml_mod.count(REJECT_OLD)
assert c == 1, f"Reject: expected 1, got {c}"
yaml_mod = yaml_mod.replace(REJECT_OLD, REJECT_NEW)
print(f"[YAML] Rejection email: 1 match replaced")

c = yaml_mod.count(BTN_PRODUCT_THEN_REASON)
assert c == 4, f"Button emails: expected 4, got {c}"
yaml_mod = yaml_mod.replace(BTN_PRODUCT_THEN_REASON, BTN_PRODUCT_THEN_REASON_NEW)
print(f"[YAML] Button emails: 4 matches replaced")

# --- REQUIRED + PINK BORDER (Product Name, Minor Accept, Minor Reject) ---

# YAML patterns - need unique context for each
# Product Name DataCard:
#   BorderColor: =RGBA(245, 245, 245, 1)
#   DataField: ="ProductNameNumber"
#   ...
#   Required: =false

PN_YAML_BC_OLD = b'BorderColor: =RGBA(245, 245, 245, 1)\n                                          DataField: ="ProductNameNumber"'
PN_YAML_BC_NEW = b"BorderColor: =If(Parent.DisplayMode = DisplayMode.Edit && !IsBlank(Parent.Error), RGBA(168, 0, 0, 1), RGBA(245, 245, 245, 1))\n                                          DataField: =\"ProductNameNumber\""

c = yaml_mod.count(PN_YAML_BC_OLD)
assert c == 1, f"PN BorderColor YAML: expected 1, got {c}"
yaml_mod = yaml_mod.replace(PN_YAML_BC_OLD, PN_YAML_BC_NEW)
print(f"[YAML] Product Name BorderColor: 1 match replaced")

# Product Name Required - currently =false, change to =true
# Use context: MaxLength line before it + Required line
PN_YAML_REQ_OLD = b"MaxLength: =DataSourceInfo([@'Incoming/In process & Final Inspections'], DataSourceInfo.MaxLength, 'Product Name')\n                                          Required: =false"
PN_YAML_REQ_NEW = b"MaxLength: =DataSourceInfo([@'Incoming/In process & Final Inspections'], DataSourceInfo.MaxLength, 'Product Name')\n                                          Required: =true"

c = yaml_mod.count(PN_YAML_REQ_OLD)
assert c == 1, f"PN Required YAML: expected 1, got {c}"
yaml_mod = yaml_mod.replace(PN_YAML_REQ_OLD, PN_YAML_REQ_NEW)
print(f"[YAML] Product Name Required: 1 match replaced")

# Minor Accept Number DataCard:
MA_YAML_BC_OLD = b'BorderColor: =RGBA(245, 245, 245, 1)\n                                          DataField: ="MinorAcceptNumber"'
MA_YAML_BC_NEW = b"BorderColor: =If(Parent.DisplayMode = DisplayMode.Edit && !IsBlank(Parent.Error), RGBA(168, 0, 0, 1), RGBA(245, 245, 245, 1))\n                                          DataField: =\"MinorAcceptNumber\""

c = yaml_mod.count(MA_YAML_BC_OLD)
assert c == 1, f"MA BorderColor YAML: expected 1, got {c}"
yaml_mod = yaml_mod.replace(MA_YAML_BC_OLD, MA_YAML_BC_NEW)
print(f"[YAML] Minor Accept BorderColor: 1 match replaced")

# Minor Accept Required
MA_YAML_REQ_OLD = b"DataField: =\"MinorAcceptNumber\"\n                                          Default: =ThisItem.'Minor Accept Number'\n                                          DisplayName: =DataSourceInfo([@'Incoming/In process & Final Inspections'],DataSourceInfo.DisplayName,'Minor Accept Number')\n                                          Required: =false"
MA_YAML_REQ_NEW = b"DataField: =\"MinorAcceptNumber\"\n                                          Default: =ThisItem.'Minor Accept Number'\n                                          DisplayName: =DataSourceInfo([@'Incoming/In process & Final Inspections'],DataSourceInfo.DisplayName,'Minor Accept Number')\n                                          Required: =true"

c = yaml_mod.count(MA_YAML_REQ_OLD)
assert c == 1, f"MA Required YAML: expected 1, got {c}"
yaml_mod = yaml_mod.replace(MA_YAML_REQ_OLD, MA_YAML_REQ_NEW)
print(f"[YAML] Minor Accept Required: 1 match replaced")

# Minor Reject Number DataCard:
MR_YAML_BC_OLD = b'BorderColor: =RGBA(245, 245, 245, 1)\n                                          DataField: ="MinorRejectNumber"'
MR_YAML_BC_NEW = b"BorderColor: =If(Parent.DisplayMode = DisplayMode.Edit && !IsBlank(Parent.Error), RGBA(168, 0, 0, 1), RGBA(245, 245, 245, 1))\n                                          DataField: =\"MinorRejectNumber\""

c = yaml_mod.count(MR_YAML_BC_OLD)
assert c == 1, f"MR BorderColor YAML: expected 1, got {c}"
yaml_mod = yaml_mod.replace(MR_YAML_BC_OLD, MR_YAML_BC_NEW)
print(f"[YAML] Minor Reject BorderColor: 1 match replaced")

# Minor Reject Required
MR_YAML_REQ_OLD = b"DataField: =\"MinorRejectNumber\"\n                                          Default: =ThisItem.'Minor Reject Number'\n                                          DisplayName: =DataSourceInfo([@'Incoming/In process & Final Inspections'],DataSourceInfo.DisplayName,'Minor Reject Number')\n                                          Required: =false"
MR_YAML_REQ_NEW = b"DataField: =\"MinorRejectNumber\"\n                                          Default: =ThisItem.'Minor Reject Number'\n                                          DisplayName: =DataSourceInfo([@'Incoming/In process & Final Inspections'],DataSourceInfo.DisplayName,'Minor Reject Number')\n                                          Required: =true"

c = yaml_mod.count(MR_YAML_REQ_OLD)
assert c == 1, f"MR Required YAML: expected 1, got {c}"
yaml_mod = yaml_mod.replace(MR_YAML_REQ_OLD, MR_YAML_REQ_NEW)
print(f"[YAML] Minor Reject Required: 1 match replaced")

# --- PO# LABEL PREFIX on action bar ---
# SelectedRecordTitle1 Text: =RecordsGallery1.Selected.'PO Number'
# Change to: ="PO# " & Coalesce(Text(RecordsGallery1.Selected.'PO Number'), "")
PO_LABEL_OLD = b"LayoutMaxWidth: =75\n                                    PaddingLeft: =30\n                                    Text: =RecordsGallery1.Selected.'PO Number'"
PO_LABEL_NEW = b"LayoutMaxWidth: =180\n                                    PaddingLeft: =30\n                                    Text: =\"PO Number: \" & Coalesce(Text(RecordsGallery1.Selected.'PO Number'), \"\")"

c = yaml_mod.count(PO_LABEL_OLD)
assert c == 1, f"PO label YAML: expected 1, got {c}"
yaml_mod = yaml_mod.replace(PO_LABEL_OLD, PO_LABEL_NEW)
print(f"[YAML] PO# label prefix: 1 match replaced")

# --- EMAIL SUBJECT LINES: Title -> Lot Number ---

# 1. gblTitleLine: Form1.LastSubmit.Title -> Form1.LastSubmit.'Lot Number'
TITLE_LINE_OLD = b"Set(gblTitleLine, Coalesce(Text(Form1.LastSubmit.Title), \"ID \" & Text(Form1.LastSubmit.ID)));"
TITLE_LINE_NEW = b"Set(gblTitleLine, \"Lot# \" & Coalesce(Text(Form1.LastSubmit.'Lot Number'), \"ID \" & Text(Form1.LastSubmit.ID)));"

c = yaml_mod.count(TITLE_LINE_OLD)
assert c == 1, f"gblTitleLine YAML: expected 1, got {c}"
yaml_mod = yaml_mod.replace(TITLE_LINE_OLD, TITLE_LINE_NEW)
print(f"[YAML] gblTitleLine -> Lot Number: 1 match replaced")

# 2. Button email subjects: RecordsGallery1.Selected.Title -> Lot Number (5 occurrences)
GALLERY_TITLE_OLD = b"Text(RecordsGallery1.Selected.Title)"
GALLERY_TITLE_NEW = b"\"Lot# \" & Coalesce(Text(RecordsGallery1.Selected.'Lot Number'), Text(RecordsGallery1.Selected.ID))"

c = yaml_mod.count(GALLERY_TITLE_OLD)
assert c == 5, f"Gallery Title in subjects: expected 5, got {c}"
yaml_mod = yaml_mod.replace(GALLERY_TITLE_OLD, GALLERY_TITLE_NEW)
print(f"[YAML] Email subjects -> Lot Number: 5 matches replaced")

# --- MATH VALIDATION: Accept/Reject numbers cannot exceed Quantity Received ---
# Insert validation after Form.Valid check, before NCR check
# Pattern: the transition from Form.Valid error to NCR check
MATH_VAL_OLD = (
    b'Notify("Required fields are highlighted in red.", NotificationType.Error), '
    b'If(And(DataCardValue25.Selected.Value = "Fail", IsBlank(DataCardValue41.Text), Form1.Mode = FormMode.Edit)'
)

MATH_VAL_NEW = (
    b'Notify("Required fields are highlighted in red.", NotificationType.Error), '
    b'If(And(Not(IsBlank(DataCardValue19.Text)), IsNumeric(DataCardValue19.Text), Or('
    b'And(Not(IsBlank(DataCardValue21.Text)), IsNumeric(DataCardValue21.Text), Value(DataCardValue21.Text) > Value(DataCardValue19.Text)), '
    b'And(Not(IsBlank(DataCardValue22.Text)), IsNumeric(DataCardValue22.Text), Value(DataCardValue22.Text) > Value(DataCardValue19.Text)), '
    b'And(Not(IsBlank(DataCardValue37.Text)), IsNumeric(DataCardValue37.Text), Value(DataCardValue37.Text) > Value(DataCardValue19.Text)), '
    b'And(Not(IsBlank(DataCardValue39.Text)), IsNumeric(DataCardValue39.Text), Value(DataCardValue39.Text) > Value(DataCardValue19.Text)), '
    b'And(Not(IsBlank(DataCardValue40.Text)), IsNumeric(DataCardValue40.Text), Value(DataCardValue40.Text) > Value(DataCardValue19.Text)), '
    b'And(Not(IsBlank(DataCardValue42.Text)), IsNumeric(DataCardValue42.Text), Value(DataCardValue42.Text) > Value(DataCardValue19.Text))'
    b')), Notify("Accept/Reject numbers cannot exceed Quantity Received.", NotificationType.Error), '
    b'If(And(DataCardValue25.Selected.Value = "Fail", IsBlank(DataCardValue41.Text), Form1.Mode = FormMode.Edit)'
)

c = yaml_mod.count(MATH_VAL_OLD)
assert c == 1, f"Math validation insert: expected 1, got {c}"
yaml_mod = yaml_mod.replace(MATH_VAL_OLD, MATH_VAL_NEW)
print(f"[YAML] Math validation: 1 match replaced")

# Need an extra closing paren for the new If() at the end of the submit formula
# Current ends with: SubmitForm(Form1)))))
# New needs:        SubmitForm(Form1))))))  (one extra for the math If)
CLOSE_OLD = b"SubmitForm(Form1)))))"
CLOSE_NEW = b"SubmitForm(Form1))))))"

c = yaml_mod.count(CLOSE_OLD)
print(f"Closing parens matches: {c}")
assert c >= 1, f"Closing parens: expected >=1, got {c}"
# Only replace the FIRST occurrence (the submit button, not others)
idx = yaml_mod.find(CLOSE_OLD)
yaml_mod = yaml_mod[:idx] + CLOSE_NEW + yaml_mod[idx + len(CLOSE_OLD):]
print(f"[YAML] Added closing paren for math validation If()")

print(f"\nYAML: {len(yaml_data)} -> {len(yaml_mod)} bytes")

# ================================================================
# JSON REPLACEMENTS
# ================================================================
json_mod = json_data

# For JSON, we need to update Required and BorderColor InvariantScript
# using unique context near each DataField

# Helper: build unique JSON patterns using the DataField value as anchor
# The pattern: ...DataField InvariantScript...Required InvariantScript...
# These are in the same Rules array

# Product Name - Required
PN_JSON_REQ_OLD = b'ProductNameNumber\\",\\r\\n                                \\"RuleProviderType\\": \\"Unknown\\"\\r\\n                              },\\r\\n                              {\\r\\n                                \\"Property\\": \\"DisplayName\\"'
# Actually, let me use simpler unique patterns by combining DataField name with Required value

# Strategy: find each DataField in JSON, then do targeted replacement of Required and BorderColor
# within the specific byte range of that DataCard

def replace_in_range(data, anchor, old_pattern, new_pattern, label):
    """Replace old_pattern with new_pattern only in the vicinity of anchor."""
    anchor_idx = data.find(anchor)
    if anchor_idx < 0:
        print(f"  WARNING: anchor not found for {label}")
        return data

    # Search within 3000 bytes after the anchor for the pattern
    search_start = max(0, anchor_idx - 1000)
    search_end = min(len(data), anchor_idx + 3000)
    chunk = data[search_start:search_end]

    old_idx = chunk.find(old_pattern)
    if old_idx < 0:
        print(f"  WARNING: pattern not found for {label}")
        return data

    # Verify uniqueness within chunk
    count = chunk.count(old_pattern)
    if count != 1:
        print(f"  WARNING: pattern found {count} times for {label}")

    abs_start = search_start + old_idx
    data = data[:abs_start] + new_pattern + data[abs_start + len(old_pattern):]
    print(f"[JSON] {label}: replaced at byte {abs_start}")
    return data

# JSON Required: "false" -> "true"
JSON_REQ_FALSE = b'"InvariantScript": "false",\r\n                                "RuleProviderType": "Unknown"\r\n                              },\r\n                              {\r\n                                "Property": "Default"'
JSON_REQ_TRUE  = b'"InvariantScript": "true",\r\n                                "RuleProviderType": "Unknown"\r\n                              },\r\n                              {\r\n                                "Property": "Default"'

# This pattern (Required false before Default) should exist for each DataCard.
# Use DataField name as anchor to scope the replacement.

for anchor, label in [(b'ProductNameNumber', 'Product Name'), (b'MinorAcceptNumber', 'Minor Accept'), (b'MinorRejectNumber', 'Minor Reject')]:
    json_mod = replace_in_range(json_mod, anchor, JSON_REQ_FALSE, JSON_REQ_TRUE, f"{label} Required")

# JSON BorderColor: RGBA(245, 245, 245, 1) -> conditional
JSON_BC_OLD = b'"InvariantScript": "RGBA(245, 245, 245, 1)"'
JSON_BC_NEW = b'"InvariantScript": "If(Parent.DisplayMode = DisplayMode.Edit && !IsBlank(Parent.Error), RGBA(168, 0, 0, 1), RGBA(245, 245, 245, 1))"'

for anchor, label in [(b'ProductNameNumber', 'Product Name'), (b'MinorAcceptNumber', 'Minor Accept'), (b'MinorRejectNumber', 'Minor Reject')]:
    json_mod = replace_in_range(json_mod, anchor, JSON_BC_OLD, JSON_BC_NEW, f"{label} BorderColor")

# PO# label - update LayoutMaxWidth in JSON for SelectedRecordTitle1
JSON_MAXW_OLD = b'"InvariantScript": "75"'
json_mod = replace_in_range(json_mod, b'SelectedRecordTitle1', JSON_MAXW_OLD, b'"InvariantScript": "180"', "PO Number LayoutMaxWidth")

# --- JSON: Email subject lines - replace ALL Title references ---
# Replace RecordsGallery1.Selected.Title -> Lot Number in JSON (global replace)
JSON_GALLERY_TITLE_OLD = b'Text(RecordsGallery1.Selected.Title)'
JSON_GALLERY_TITLE_NEW = b'\\\"Lot# \\\" & Coalesce(Text(RecordsGallery1.Selected.\'Lot Number\'), Text(RecordsGallery1.Selected.ID))'

c = json_mod.count(JSON_GALLERY_TITLE_OLD)
print(f"JSON RecordsGallery1.Selected.Title occurrences: {c}")
json_mod = json_mod.replace(JSON_GALLERY_TITLE_OLD, JSON_GALLERY_TITLE_NEW)
print(f"[JSON] Gallery Title -> Lot Number: {c} matches replaced")

# Replace Form1.LastSubmit.Title -> Lot Number in JSON
JSON_LASTSUBMIT_TITLE_OLD = b"Coalesce(Text(Form1.LastSubmit.Title), \\\"ID \\\" & Text(Form1.LastSubmit.ID))"
JSON_LASTSUBMIT_TITLE_NEW = b"\\\"Lot# \\\" & Coalesce(Text(Form1.LastSubmit.'Lot Number'), \\\"ID \\\" & Text(Form1.LastSubmit.ID))"

c = json_mod.count(JSON_LASTSUBMIT_TITLE_OLD)
print(f"JSON Form1.LastSubmit.Title occurrences: {c}")
json_mod = json_mod.replace(JSON_LASTSUBMIT_TITLE_OLD, JSON_LASTSUBMIT_TITLE_NEW)
print(f"[JSON] LastSubmit Title -> Lot Number: {c} matches replaced")

print(f"\nJSON: {len(json_data)} -> {len(json_mod)} bytes")

# ================================================================
# BUILD OUTPUT MSAPP
# ================================================================

out_io = io.BytesIO()
with zipfile.ZipFile(out_io, 'w') as oz:
    for fname, (item, data) in all_files.items():
        if item.filename == 'Src\\MainScreen1.pa.yaml':
            oz.writestr(item, yaml_mod)
        elif item.filename == 'Controls\\4.json':
            oz.writestr(item, json_mod)
        else:
            oz.writestr(item, data)

out_bytes = out_io.getvalue()
with open(OUT_MSAPP, 'wb') as f:
    f.write(out_bytes)

print(f"\nOutput: {OUT_MSAPP} ({len(out_bytes)} bytes)")

# ================================================================
# VERIFY
# ================================================================
with zipfile.ZipFile(OUT_MSAPP, 'r') as z:
    v_yaml = z.read('Src\\MainScreen1.pa.yaml').decode('utf-8', errors='replace')
    v_json = z.read('Controls\\4.json').decode('utf-8', errors='replace')

print("\n=== VERIFICATION ===")

# Check Required=true in YAML
for field in ['Product Name', 'Minor Accept', 'Minor Reject']:
    if field == 'Product Name':
        df = 'ProductNameNumber'
    elif field == 'Minor Accept':
        df = 'MinorAcceptNumber'
    else:
        df = 'MinorRejectNumber'

    # Find DataField in YAML and check nearby Required
    idx = v_yaml.find(f'DataField: ="{df}"')
    if idx > 0:
        chunk = v_yaml[max(0,idx-200):idx+500]
        if 'Required: =true' in chunk:
            print(f"  [OK] {field} Required=true (YAML)")
        else:
            print(f"  [FAIL] {field} Required not true (YAML)")
        if 'Parent.Error' in chunk and 'RGBA(168, 0, 0, 1)' in chunk:
            print(f"  [OK] {field} pink BorderColor (YAML)")
        else:
            print(f"  [FAIL] {field} pink BorderColor missing (YAML)")

# Check JSON Required
for df, label in [('ProductNameNumber', 'Product Name'), ('MinorAcceptNumber', 'Minor Accept'), ('MinorRejectNumber', 'Minor Reject')]:
    idx = v_json.find(df)
    if idx > 0:
        chunk = v_json[max(0,idx-500):idx+3000]
        # Find Required InvariantScript
        if '"InvariantScript": "true"' in chunk:
            print(f"  [OK] {label} Required=true (JSON)")
        else:
            print(f"  [FAIL] {label} Required not true (JSON)")
        if 'Parent.Error' in chunk and 'RGBA(168, 0, 0, 1)' in chunk:
            print(f"  [OK] {label} pink BorderColor (JSON)")
        else:
            print(f"  [FAIL] {label} pink BorderColor missing (JSON)")

# Email verification
notify_fields = ['Inspector', 'Date', 'Type', 'Product Name', 'Part Number', 'Lot Number',
                 'PO Number', 'Serial Number', 'NCR Number', 'Outcome', 'Notes/Observations', 'ID']
print("\n  Email fields: all present" if all(f in v_yaml for f in notify_fields) else "\n  WARNING: some email fields missing")

if 'gblCh1 & gblCh2 & gblCh3 & gblCh4 & gblCh5 & gblCh6' in v_yaml:
    print("  [OK] Changed fields tracking in notification email")

# PO# label verification
if '"PO# "' in v_yaml or "'PO# '" in v_yaml:
    print("  [OK] PO# label prefix on action bar")
else:
    print("  [FAIL] PO# label prefix missing")

print("\n=== BUILD COMPLETE ===")
