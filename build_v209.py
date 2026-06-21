#!/usr/bin/env python3
"""v209: Fix S-level sample size boundaries (Table I corrections),
100% inspection = zero tolerance (Ac=0, Re=1 for all categories),
add S-level index mappings to autofail formula."""
import zipfile, io, os, sys, json

PROJECT_DIR = '/var/lib/freelancer/projects/40486904'
OUTER_ZIP = os.path.join(PROJECT_DIR, 'Incoming_Inprocess&FinalInspections_20260620100614.zip')
MSAPP_PATH = 'Microsoft.PowerApps/apps/18391596269880809910/N30314c2b-e7af-4e2d-a9ee-0ada822be283-document.msapp'
OUTPUT = os.path.join(PROJECT_DIR, 'v209_aql.msapp')

LV_CALC = (
    'With({l: Lower(lvl)}, If('
    'Or(l = "aql level iii", l = "aql level 3", l = "iii", l = "gi-iii", l = "3", l = "level iii", l = "level 3"), 3,'
    'Or(l = "aql level i", l = "aql level 1", l = "i", l = "gi-i", l = "1", l = "level i", l = "level 1"), 1,'
    'Or(l = "s-1", l = "s1"), 41, Or(l = "s-2", l = "s2"), 42, '
    'Or(l = "s-3", l = "s3"), 43, Or(l = "s-4", l = "s4"), 44, '
    'Or(l = "10%", l = "10 %"), 10, Or(l = "100%", l = "100 %"), 100, 2))'
)

# ============================================================
# CORRECTED Table I code letter → sample size mappings
# Based on ANSI/ASQ Z1.4 Table I
# ============================================================
# S-1: 2-500→A(2), 501-10000→B(3), 10001+→C(5)
# S-2: 2-50→A(2), 51-500→B(3), 501-10000→C(5), 10001+→D(8)
# S-3: 2-15→A(2), 16-90→B(3), 91-280→C(5), 281-1200→D(8), 1201-10000→E(13), 10001+→F(20)
# S-4: 2-15→A(2), 16-25→B(3), 26-90→C(5), 91-280→D(8), 281-1200→E(13), 1201-3200→F(20), 3201+→G(32)

# Generic Table A sample sizes (for Critical / Not Allowed - no AQL shifts)
CRIT_SS = (
    'If(lv = 1, If(lotN<2,0,lotN<=8,2,lotN<=15,2,lotN<=25,3,lotN<=50,5,lotN<=90,5,lotN<=150,8,lotN<=280,13,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125), '
    'lv = 3, If(lotN<2,0,lotN<=8,3,lotN<=15,5,lotN<=25,8,lotN<=50,13,lotN<=90,20,lotN<=150,32,lotN<=280,50,lotN<=500,80,lotN<=1200,125,lotN<=3200,200,315), '
    'lv=41, If(lotN<2,0,lotN<=500,2,lotN<=10000,3,5), '
    'lv=42, If(lotN<2,0,lotN<=50,2,lotN<=500,3,lotN<=10000,5,8), '
    'lv=43, If(lotN<2,0,lotN<=15,2,lotN<=90,3,lotN<=280,5,lotN<=1200,8,lotN<=10000,13,20), '
    'lv=44, If(lotN<2,0,lotN<=15,2,lotN<=25,3,lotN<=90,5,lotN<=280,8,lotN<=1200,13,lotN<=3200,20,32), '
    'lv = 10, If(lotN<10,0,Max(RoundUp(lotN*0.1,0),1)), lv = 100, If(lotN<2,0,lotN), '
    'If(lotN<2,0,lotN<=8,2,lotN<=15,3,lotN<=25,5,lotN<=50,8,lotN<=90,13,lotN<=150,20,lotN<=280,32,lotN<=500,50,lotN<=1200,80,lotN<=3200,125,200))'
)

# Major (default AQL 2.5) - shifted sample sizes
# AQL 2.5 startIdx=5. Arrow shifts give sample=5 for d<=-2, sample=20 for d=-1
# S-1: all practical lots → d<=-2 → sample 5
# S-2: all practical lots → d<=-2 → sample 5
# S-3: lot<=1200 (code A-D, idx 0-3) → d<=-2 → sample 5; lot>1200 (code E+) → sample 20
# S-4: lot<=280 (code A-D, idx 0-3) → d<=-2 → sample 5; lot>280 (code E+) → sample 20
MAJ_SS = (
    'If(lv = 1, If(lotN<2,0,lotN<=150,5,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125), '
    'lv = 3, If(lotN<2,0,lotN<=25,5,lotN<=90,20,lotN<=150,32,lotN<=280,50,lotN<=500,80,lotN<=1200,125,lotN<=3200,200,315), '
    'Or(lv=41,lv=42), If(lotN<2,0,5), '
    'lv=43, If(lotN<2,0,lotN<=1200,5,20), '
    'lv=44, If(lotN<2,0,lotN<=280,5,20), '
    'lv = 10, If(lotN<10,0,Max(RoundUp(lotN*0.1,0),1)), lv = 100, If(lotN<2,0,lotN), '
    'If(lotN<2,0,lotN<=50,5,lotN<=150,20,lotN<=280,32,lotN<=500,50,lotN<=1200,80,lotN<=3200,125,200))'
)

# Minor (default AQL 4.0) - shifted sample sizes
# AQL 4.0 startIdx=4. Arrow shifts give sample=3 for d<=-2, sample=13 for d=-1
# S-1 & S-2: all practical lots → d<=-2 → sample 3
# S-3: lot<=280 (code A-C, idx 0-2) → d<=-2 → sample 3; lot>280 (code D+) → d=-1 → sample 13
# S-4: lot<=90 (code A-C, idx 0-2) → d<=-2 → sample 3; lot 91-1200 (code D-E) → sample 13; lot>1200 → sample 20
MIN_SS = (
    'If(lv = 1, If(lotN<2,0,lotN<=90,3,lotN<=280,13,lotN<=500,20,lotN<=1200,32,lotN<=3200,50,lotN<=10000,80,125), '
    'lv = 3, If(lotN<2,0,lotN<=15,3,lotN<=50,13,lotN<=90,20,lotN<=150,32,lotN<=280,50,lotN<=500,80,lotN<=1200,125,lotN<=3200,200,315), '
    'Or(lv=41,lv=42), If(lotN<2,0,3), '
    'lv=43, If(lotN<2,0,lotN<=280,3,13), '
    'lv=44, If(lotN<2,0,lotN<=90,3,lotN<=1200,13,20), '
    'lv = 10, If(lotN<10,0,Max(RoundUp(lotN*0.1,0),1)), lv = 100, If(lotN<2,0,lotN), '
    'If(lotN<2,0,lotN<=25,3,lotN<=90,13,lotN<=150,20,lotN<=280,32,lotN<=500,50,lotN<=1200,80,lotN<=3200,125,200))'
)

AC_CALC = (
    'If(aqlN <= 0, 0, '
    'With({d: '
    'If(ss>=315,11,ss>=200,10,ss>=125,9,ss>=80,8,ss>=50,7,ss>=32,6,ss>=20,5,ss>=13,4,ss>=8,3,ss>=5,2,ss>=3,1,0)'
    ' - '
    'If(aqlN>=6.5,3,aqlN>=4.0,4,aqlN>=2.5,5,aqlN>=1.5,6,aqlN>=1.0,7,aqlN>=0.65,8,aqlN>=0.40,9,aqlN>=0.25,10,aqlN>=0.15,11,aqlN>=0.10,12,13)'
    '}, If(d<0,0,d=0,1,d=1,2,d=2,3,d=3,5,d=4,7,d=5,10,d=6,14,21)))'
)

IDX2SS = 'If(ei>=11,315,ei>=10,200,ei>=9,125,ei>=8,80,ei>=7,50,ei>=6,32,ei>=5,20,ei>=4,13,ei>=3,8,ei>=2,5,ei>=1,3,2)'

def build_dn(category, combo, default_aql, ss_calc):
    return (
        '=With({lotN: If(Or(IsBlank(DataCardValue19.Text), Not(IsNumeric(DataCardValue19.Text))), 0, Value(DataCardValue19.Text)), '
        'lvl: Coalesce(DataCardValue20.Selected.Value, ""), '
        f'aql: Coalesce({combo}.Selected.Value, "")'
        '}, With({'
        f'lv: {LV_CALC}, '
        f'aqlN: With({{a: Lower(Coalesce(aql, ""))}}, If(Or(IsBlank(a), a = ""), {default_aql}, Or(a = "not allowed", a = "n/a", a = "0", a = "0%"), -1, IsNumeric(a), Value(a), {default_aql}))'
        '}, With({'
        f'ss: {ss_calc}'
        '}, '
        # 100% special case: zero tolerance for all categories
        'If(lv = 100 && ss > 0, '
        f'If(aqlN > 0, "{category}  |  AQL: " & If(Or(IsBlank(aql), aql = ""), "{default_aql}", aql) & "  |  Sample Size: " & Text(ss) & "  |  Accept: 0  |  Reject: 1", '
        f'aqlN = -1, "{category}  |  AQL: Not Allowed  |  Sample Size: " & Text(ss) & "  |  Accept: 0  |  Reject: 0", '
        f'"{category}"), '
        # Normal AQL calculation
        'ss > 0 && aqlN > 0, '
        'With({'
        'ssi: If(ss>=315,11,ss>=200,10,ss>=125,9,ss>=80,8,ss>=50,7,ss>=32,6,ss>=20,5,ss>=13,4,ss>=8,3,ss>=5,2,ss>=3,1,0), '
        'sti: If(aqlN>=6.5,3,aqlN>=4.0,4,aqlN>=2.5,5,aqlN>=1.5,6,aqlN>=1.0,7,aqlN>=0.65,8,aqlN>=0.40,9,aqlN>=0.25,10,aqlN>=0.15,11,aqlN>=0.10,12,13)'
        '}, With({d: ssi - sti}, '
        'If(d >= 0, '
        f'"{category}  |  AQL: " & If(Or(IsBlank(aql), aql = ""), "{default_aql}", aql) & "  |  Sample Size: " & Text(ss) & "  |  Accept: " & Text(If(d=0,1,d=1,2,d=2,3,d=3,5,d=4,7,d=5,10,d=6,14,21)) & "  |  Reject: " & Text(If(d=0,1,d=1,2,d=2,3,d=3,5,d=4,7,d=5,10,d=6,14,21) + 1), '
        f'd = -1, With({{ei: sti}}, "{category}  |  AQL: " & If(Or(IsBlank(aql), aql = ""), "{default_aql}", aql) & "  |  Sample Size: " & Text({IDX2SS}) & "  |  Accept: 1  |  Reject: 2"), '
        f'With({{ei: Max(sti - 3, 0)}}, "{category}  |  AQL: " & If(Or(IsBlank(aql), aql = ""), "{default_aql}", aql) & "  |  Sample Size: " & Text({IDX2SS}) & "  |  Accept: 0  |  Reject: 1")'
        '))), '
        f'If(ss > 0 && aqlN = -1, '
        f'"{category}  |  AQL: Not Allowed  |  Sample Size: " & Text(ss) & "  |  Accept: 0  |  Reject: 0", '
        f'"{category}")))))'
    )


def build_summary():
    return (
        '=With({qty: Value(If(Form1.Mode = FormMode.View, Text(ThisItem.\'Quantity Recieved\'), DataCardValue19.Text)), '
        'lvl: If(Form1.Mode = FormMode.View, ThisItem.\'Sampling Method\'.Value, DataCardValue20.Selected.Value), '
        'critAql: Coalesce(If(Form1.Mode = FormMode.View, ThisItem.\'Critical Defect Count\'.Value, DataCardValue36.Selected.Value), ""), '
        'majAql: Coalesce(If(Form1.Mode = FormMode.View, ThisItem.\'Major Defect Count\'.Value, DataCardValue34.Selected.Value), ""), '
        'minAql: Coalesce(If(Form1.Mode = FormMode.View, ThisItem.\'Minor Defect Count\'.Value, DataCardValue35.Selected.Value), "")'
        '}, If(Or(IsBlank(qty), qty <= 0, IsBlank(lvl)), "AQL Calculator: Enter Quantity Received and select a Sampling Method", '
        f'With({{lotN: qty, lv: {LV_CALC}}}, '
        'With({'
        'majAqlN: With({a: Lower(Coalesce(majAql, ""))}, If(Or(IsBlank(a), a = ""), 2.5, Or(a = "not allowed", a = "n/a", a = "0"), -1, IsNumeric(a), Value(a), 2.5)), '
        'minAqlN: With({a: Lower(Coalesce(minAql, ""))}, If(Or(IsBlank(a), a = ""), 4.0, Or(a = "not allowed", a = "n/a", a = "0"), -1, IsNumeric(a), Value(a), 4.0)), '
        f'critSS: {CRIT_SS}, '
        f'majSS: {MAJ_SS}, '
        f'minSS: {MIN_SS}'
        '}, With({'
        # 100% override: Ac=0 for all categories
        f'majAc: If(lv = 100, 0, majAqlN = -1, 0, majAqlN <= 0, 0, With({{ss: majSS, d: If(majSS>=315,11,majSS>=200,10,majSS>=125,9,majSS>=80,8,majSS>=50,7,majSS>=32,6,majSS>=20,5,majSS>=13,4,majSS>=8,3,majSS>=5,2,majSS>=3,1,0) - If(majAqlN>=6.5,3,majAqlN>=4.0,4,majAqlN>=2.5,5,majAqlN>=1.5,6,majAqlN>=1.0,7,majAqlN>=0.65,8,majAqlN>=0.40,9,majAqlN>=0.25,10,majAqlN>=0.15,11,majAqlN>=0.10,12,13)}}, If(d<0,0,d=0,1,d=1,2,d=2,3,d=3,5,d=4,7,d=5,10,d=6,14,21))), '
        f'minAc: If(lv = 100, 0, minAqlN = -1, 0, minAqlN <= 0, 0, With({{ss: minSS, d: If(minSS>=315,11,minSS>=200,10,minSS>=125,9,minSS>=80,8,minSS>=50,7,minSS>=32,6,minSS>=20,5,minSS>=13,4,minSS>=8,3,minSS>=5,2,minSS>=3,1,0) - If(minAqlN>=6.5,3,minAqlN>=4.0,4,minAqlN>=2.5,5,minAqlN>=1.5,6,minAqlN>=1.0,7,minAqlN>=0.65,8,minAqlN>=0.40,9,minAqlN>=0.25,10,minAqlN>=0.15,11,minAqlN>=0.10,12,13)}}, If(d<0,0,d=0,1,d=1,2,d=2,3,d=3,5,d=4,7,d=5,10,d=6,14,21)))'
        '}, '
        '"AQL SAMPLING PLAN" & Char(10) & "Lot: " & Text(qty) & " units  |  Level: " & lvl & Char(10) & Char(10) & '
        '"CRITICAL (Not Allowed)" & Char(10) & "  Sample: " & Text(critSS) & " units  |  Ac: 0  |  Re: 0" & Char(10) & Char(10) & '
        '"MAJOR (" & If(majAqlN = -1, "Not Allowed", "AQL " & If(Or(IsBlank(majAql), majAql = ""), "2.5", majAql)) & ")" & Char(10) & '
        '"  Sample: " & Text(majSS) & " units  |  Ac: " & Text(majAc) & "  |  Re: " & Text(If(Or(lv = 100, majAqlN = -1), 0, majAc + 1)) & Char(10) & Char(10) & '
        '"MINOR (" & If(minAqlN = -1, "Not Allowed", "AQL " & If(Or(IsBlank(minAql), minAql = ""), "4.0", minAql)) & ")" & Char(10) & '
        '"  Sample: " & Text(minSS) & " units  |  Ac: " & Text(minAc) & "  |  Re: " & Text(If(Or(lv = 100, minAqlN = -1), 0, minAc + 1))'
        '))))'
        ')'
    )


# Autofail with corrected S-level index mappings and 100% support
AUTOFAIL = (
    '=With({'
    'lot: If(Or(IsBlank(DataCardValue19.Text), Not(IsNumeric(DataCardValue19.Text))), 0, Value(DataCardValue19.Text)), '
    'lv: Lower(Coalesce(DataCardValue20.Selected.Value, "")), '
    'critAq: With({a: Lower(Coalesce(DataCardValue36.Selected.Value, ""))}, If(Or(IsBlank(a), a = ""), -1, Or(a = "not allowed", a = "n/a", a = "0"), -1, IsNumeric(a), Value(a), -1)), '
    'majAq: With({a: Lower(Coalesce(DataCardValue34.Selected.Value, ""))}, If(Or(IsBlank(a), a = ""), 2.5, Or(a = "not allowed", a = "n/a", a = "0"), -1, IsNumeric(a), Value(a), 2.5)), '
    'minAq: With({a: Lower(Coalesce(DataCardValue35.Selected.Value, ""))}, If(Or(IsBlank(a), a = ""), 4.0, Or(a = "not allowed", a = "n/a", a = "0"), -1, IsNumeric(a), Value(a), 4.0))'
    '}, With({'
    # si: sample index - now with S-level and 100%/10% support
    'si: If('
    'Or(lv = "100%", lv = "100 %"), 0, '
    'Or(lv = "10%", lv = "10 %"), With({pss: Max(RoundUp(lot*0.1,0),1)}, If(pss>=315,11,pss>=200,10,pss>=125,9,pss>=80,8,pss>=50,7,pss>=32,6,pss>=20,5,pss>=13,4,pss>=8,3,pss>=5,2,pss>=3,1,0)), '
    'Or(lv = "s-1", lv = "s1"), If(lot<=500,0,lot<=10000,1,2), '
    'Or(lv = "s-2", lv = "s2"), If(lot<=50,0,lot<=500,1,lot<=10000,2,3), '
    'Or(lv = "s-3", lv = "s3"), If(lot<=15,0,lot<=90,1,lot<=280,2,lot<=1200,3,lot<=10000,4,5), '
    'Or(lv = "s-4", lv = "s4"), If(lot<=15,0,lot<=25,1,lot<=90,2,lot<=280,3,lot<=1200,4,lot<=3200,5,6), '
    'Or(lv = "aql level i", lv = "aql level 1", lv = "i", lv = "level i", lv = "gi-i", lv = "1", lv = "level 1"), '
    'If(lot<=15,0,lot<=25,1,lot<=90,2,lot<=150,3,lot<=280,4,lot<=500,5,lot<=1200,6,lot<=3200,7,lot<=10000,8,9), '
    'Or(lv = "aql level iii", lv = "aql level 3", lv = "iii", lv = "level iii", lv = "gi-iii", lv = "3", lv = "level 3"), '
    'If(lot<=8,1,lot<=15,2,lot<=25,3,lot<=50,4,lot<=90,5,lot<=150,6,lot<=280,7,lot<=500,8,lot<=1200,9,lot<=3200,10,11), '
    'If(lot<=8,0,lot<=15,1,lot<=25,2,lot<=50,3,lot<=90,4,lot<=150,5,lot<=280,6,lot<=500,7,lot<=1200,8,lot<=3200,9,10))'
    '}, With({'
    'critRe: If(critAq = -1, 1, With({d: si - If(critAq>=6.5,3,critAq>=4.0,4,critAq>=2.5,5,critAq>=1.5,6,critAq>=1.0,7,critAq>=0.65,8,critAq>=0.40,9,critAq>=0.25,10,critAq>=0.15,11,critAq>=0.10,12,13)}, If(d<=-2,1,d=-1,2,d=0,2,d=1,3,d=2,4,d=3,6,d=4,8,d=5,11,d=6,15,22))), '
    'majRe: If(majAq = -1, 1, With({d: si - If(majAq>=6.5,3,majAq>=4.0,4,majAq>=2.5,5,majAq>=1.5,6,majAq>=1.0,7,majAq>=0.65,8,majAq>=0.40,9,majAq>=0.25,10,majAq>=0.15,11,majAq>=0.10,12,13)}, If(d<=-2,1,d=-1,2,d=0,2,d=1,3,d=2,4,d=3,6,d=4,8,d=5,11,d=6,15,22))), '
    'minRe: If(minAq = -1, 1, With({d: si - If(minAq>=6.5,3,minAq>=4.0,4,minAq>=2.5,5,minAq>=1.5,6,minAq>=1.0,7,minAq>=0.65,8,minAq>=0.40,9,minAq>=0.25,10,minAq>=0.15,11,minAq>=0.10,12,13)}, If(d<=-2,1,d=-1,2,d=0,2,d=1,3,d=2,4,d=3,6,d=4,8,d=5,11,d=6,15,22)))'
    '}, If('
    'And(Not(IsBlank(DataCardValue22.Text)), IsNumeric(DataCardValue22.Text), Value(DataCardValue22.Text) >= critRe), {Value: "Fail"}, '
    'And(Not(IsBlank(DataCardValue39.Text)), IsNumeric(DataCardValue39.Text), Value(DataCardValue39.Text) >= majRe), {Value: "Fail"}, '
    'And(Not(IsBlank(DataCardValue42.Text)), IsNumeric(DataCardValue42.Text), Value(DataCardValue42.Text) >= minRe), {Value: "Fail"}, '
    'CountRows(Filter(DataCardValue12.SelectedItems, And(Not(IsBlank(ThisRecord.Value)), Lower(Trim(Text(ThisRecord.Value))) <> "no defects"))) > 0, {Value: "Fail"}, '
    'And(Not(IsBlank(DataCardValue24.Selected)), DataCardValue24.Selected.Value <> "Yes"), {Value: "Fail"}, '
    'CountRows(Filter(DataCardValue14.SelectedItems, And(Not(IsBlank(Value)), Value = "Fail"))) > 0, {Value: "Fail"}, '
    'And(Not(IsBlank(DataCardValue15.Selected)), DataCardValue15.Selected.Value = "Fail"), {Value: "Fail"}, '
    'And(Not(IsBlank(DataCardValue16.Selected)), DataCardValue16.Selected.Value = "Fail"), {Value: "Fail"}, '
    'And(Not(IsBlank(DataCardValue33.Selected)), DataCardValue33.Selected.Value = "Fail"), {Value: "Fail"}, '
    '{Value: "Pass"}))))'
)


def build():
    crit_dn = build_dn("Critical Defect Count", "DataCardValue36", "-1", CRIT_SS)
    maj_dn = build_dn("Major Defect Count", "DataCardValue34", "2.5", MAJ_SS)
    min_dn = build_dn("Minor Defect Count", "DataCardValue35", "4.0", MIN_SS)
    summary = build_summary()

    # Verify ALL
    for name, f in [('Crit', crit_dn), ('Maj', maj_dn), ('Min', min_dn), ('Sum', summary), ('AF', AUTOFAIL)]:
        o, c, q = f.count('('), f.count(')'), f.count('"')
        ok = o == c and q % 2 == 0
        print(f'{name}: {len(f)} chars, parens={o}/{c}, quotes={q} {"OK" if ok else "BAD"}')
        if not ok:
            # Show context around mismatch
            print(f'  Formula start: {f[:200]}')
            print(f'  Formula end: {f[-200:]}')
            sys.exit(1)

    with zipfile.ZipFile(OUTER_ZIP, 'r') as zf:
        msapp_data = zf.read(MSAPP_PATH)
    with zipfile.ZipFile(io.BytesIO(msapp_data), 'r') as mz:
        yaml_data = mz.read('Src\\MainScreen1.pa.yaml')
        json_data = mz.read('Controls\\4.json')

    # YAML
    lines = yaml_data.decode('utf-8').split('\n')
    done = 0
    for i, line in enumerate(lines):
        s = line.strip()
        indent = line[:len(line) - len(line.lstrip())]
        if 'Critical Defect Count  |  AQL: Not Allowed' in s and s.startswith('=With('): lines[i] = indent + crit_dn; done += 1
        elif 'Major Defect Count  |  AQL: 2.5' in s and s.startswith('=With('): lines[i] = indent + maj_dn; done += 1
        elif 'Minor Defect Count  |  AQL: 4.0' in s and s.startswith('=With('): lines[i] = indent + min_dn; done += 1
        elif 'AQL SAMPLING PLAN' in s and s.startswith('=With('): lines[i] = indent + summary; done += 1
        elif 'Value(DataCardValue22.Text) > 0), {Value: "Fail"}, And(Not(IsBlank(DataCardValue39' in s and s.startswith('=If('): lines[i] = indent + AUTOFAIL; done += 1
    assert done == 5, f'YAML: {done}/5'
    yaml_data = '\n'.join(lines).encode('utf-8')

    # JSON
    def to_json(f): return (f[1:] if f.startswith('=') else f).replace('"', '\\"')
    inv_marker = b'"InvariantScript": "'
    def rep_json(data, marker, new_f, label):
        idx = data.find(marker)
        assert idx != -1, f'{label}: not found'
        inv_s = data.rfind(inv_marker, 0, idx)
        fs = inv_s + len(inv_marker)
        pos = fs
        while pos < len(data):
            if data[pos:pos+1] == b'"' and data[pos-1:pos] != b'\\': break
            if data[pos:pos+2] == b'\\\\': pos += 2; continue
            pos += 1
        nf = to_json(new_f).encode('utf-8')
        return data[:fs] + nf + data[pos:]

    json_data = rep_json(json_data, b'\\"Critical Defect Count  |  AQL: Not Allowed', crit_dn, 'Crit')
    json_data = rep_json(json_data, b'\\"Major Defect Count  |  AQL: 2.5', maj_dn, 'Maj')
    json_data = rep_json(json_data, b'\\"Minor Defect Count  |  AQL: 4.0', min_dn, 'Min')
    json_data = rep_json(json_data, b'AQL SAMPLING PLAN', summary, 'Sum')
    json_data = rep_json(json_data, b'Value(DataCardValue22.Text) > 0), {Value: \\"Fail\\"}, And(Not(IsBlank(DataCardValue39', AUTOFAIL, 'AF')
    json.loads(json_data)
    print('JSON: VALID')

    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(msapp_data), 'r') as src:
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as out:
            for item in src.infolist():
                if item.filename == 'Src\\MainScreen1.pa.yaml': out.writestr(item, yaml_data)
                elif item.filename == 'Controls\\4.json': out.writestr(item, json_data)
                else: out.writestr(item, src.read(item.filename))
    with open(OUTPUT, 'wb') as f:
        f.write(buf.getvalue())
    print(f'Output: {OUTPUT} ({os.path.getsize(OUTPUT)} bytes)')


if __name__ == '__main__':
    build()
