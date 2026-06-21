#!/usr/bin/env python3
"""v211: Auto-set Hold Reason on fail + hide empty Notes field.
Source: June 21 export #2 (already has v210 auto-hold + AQL fixes).

Changes:
1. Auto-set Hold Reason to "Hold for 100% Sorting" when gblIsFail
2. Hide Notes_DataCard1 (empty field below AQL calculator)
"""
import zipfile, io, os, json

PROJECT_DIR = '/var/lib/freelancer/projects/40486904'
OUTER_ZIP = os.path.join(PROJECT_DIR, 'Incoming_Inprocess&FinalInspections_20260621133436 (1).zip')
MSAPP_PATH = 'Microsoft.PowerApps/apps/18391596269880809910/N615f6b13-50de-4d08-9ffc-9d1837bf6e37-document.msapp'
OUTPUT = os.path.join(PROJECT_DIR, 'v211_aql.msapp')


def build():
    msapp_dir = os.path.join(PROJECT_DIR, 'june21_v2_msapp')
    with open(os.path.join(msapp_dir, 'Src\\MainScreen1.pa.yaml'), 'r', encoding='utf-8') as f:
        yaml_text = f.read()
    with open(os.path.join(msapp_dir, 'Controls\\4.json'), 'rb') as f:
        json_data = f.read()

    changes = 0

    # ============================================================
    # YAML CHANGES
    # ============================================================

    # 1. Add Hold Reason to the OnSuccess Patch
    old_patch = (
        '{DispositionStatus: If(gblIsFail, {Value: "On Hold"}, {Value: "Accepted"}), '
        "'Notes / Observations':"
    )
    new_patch = (
        '{DispositionStatus: If(gblIsFail, {Value: "On Hold"}, {Value: "Accepted"}), '
        '\'Hold Reason\': If(gblIsFail, {Value: "Hold for 100% Sorting"}, Blank()), '
        "'Notes / Observations':"
    )
    assert old_patch in yaml_text, 'YAML: Patch marker not found'
    yaml_text = yaml_text.replace(old_patch, new_patch, 1)
    changes += 1
    print('YAML [1/2]: Hold Reason auto-set on fail')

    # 2. Hide Notes_DataCard1 - add Visible: =false
    old_notes = (
        "- Notes_DataCard1:\n"
        "                                        Control: TypedDataCard@1.0.7\n"
        "                                        Variant: ClassicTextualEdit\n"
        "                                        IsLocked: true\n"
        "                                        Properties:\n"
        "                                          BorderColor: =RGBA(245, 245, 245, 1)\n"
        '                                          DataField: ="Notes"\n'
        "                                          Default: =ThisItem.Notes\n"
    )
    new_notes = (
        "- Notes_DataCard1:\n"
        "                                        Control: TypedDataCard@1.0.7\n"
        "                                        Variant: ClassicTextualEdit\n"
        "                                        IsLocked: true\n"
        "                                        Properties:\n"
        "                                          BorderColor: =RGBA(245, 245, 245, 1)\n"
        '                                          DataField: ="Notes"\n'
        "                                          Default: =ThisItem.Notes\n"
        "                                          Visible: =false\n"
    )
    assert old_notes in yaml_text, 'YAML: Notes_DataCard1 marker not found'
    yaml_text = yaml_text.replace(old_notes, new_notes, 1)
    changes += 1
    print('YAML [2/2]: Notes_DataCard1 hidden')

    yaml_data = yaml_text.encode('utf-8')

    # ============================================================
    # JSON CHANGES (binary-safe)
    # ============================================================

    # 1. Add Hold Reason to Patch in JSON
    old_j_patch = (
        b'{DispositionStatus: If(gblIsFail, {Value: \\"On Hold\\"}, {Value: \\"Accepted\\"}), '
        b"'Notes / Observations':"
    )
    new_j_patch = (
        b'{DispositionStatus: If(gblIsFail, {Value: \\"On Hold\\"}, {Value: \\"Accepted\\"}), '
        b"'Hold Reason': If(gblIsFail, {Value: \\\"Hold for 100% Sorting\\\"}, Blank()), "
        b"'Notes / Observations':"
    )
    assert old_j_patch in json_data, 'JSON: Patch marker not found'
    json_data = json_data.replace(old_j_patch, new_j_patch, 1)
    print('JSON [1/2]: Hold Reason added to Patch')

    # 2. Hide Notes_DataCard1 - add Visible rule to Rules array
    #    Find Notes_DataCard1 in JSON, then find its Rules array, then insert Visible rule
    notes_card_marker = b'Notes_DataCard1"'
    notes_pos = json_data.find(notes_card_marker)
    assert notes_pos != -1, 'JSON: Notes_DataCard1 not found'

    # Find the DataField="Notes" rule to confirm we have the right card
    datafield_marker = b'"InvariantScript": "\\"Notes\\""'
    df_pos = json_data.find(datafield_marker, notes_pos)
    assert df_pos != -1 and df_pos - notes_pos < 3000, 'JSON: Notes DataField not found near card'
    print(f'  Notes_DataCard1 confirmed at offset {notes_pos}')

    # Find "Rules": [ for this card
    rules_marker = b'"Rules": ['
    rules_pos = json_data.find(rules_marker, notes_pos)
    assert rules_pos != -1 and rules_pos - notes_pos < 2000, 'JSON: Rules array not found'

    # Find the opening bracket position
    bracket_pos = rules_pos + len(rules_marker)

    # Insert Visible rule as the first rule in the array
    # Match the existing format with \r\n and indentation
    visible_rule = (
        b'\r\n                              {\r\n'
        b'                                "Property": "Visible",\r\n'
        b'                                "Category": "Design",\r\n'
        b'                                "InvariantScript": "false",\r\n'
        b'                                "RuleProviderType": "Unknown"\r\n'
        b'                              },'
    )
    json_data = json_data[:bracket_pos] + visible_rule + json_data[bracket_pos:]
    print('JSON [2/2]: Notes_DataCard1 Visible=false rule added')

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
    print(f'Changes: {changes} YAML + 2 JSON = done')


if __name__ == '__main__':
    build()
