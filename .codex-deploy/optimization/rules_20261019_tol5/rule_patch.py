from decimal import Decimal

POLICY = {
    'version':'20261019_tol5',
    'source':'User supplied competition rule update in this conversation on 2026-10-19',
    'baseline_ppl':'2.7696',
    'tolerance_percent':'5',
    'lower_inclusive':'2.63112',
    'upper_inclusive':'2.90808',
    'unchanged':'All other requirements, model/data, fixed PPL parameters and 590s process limit, fixed ten-repetition PP/TG, Intel compiler requirement and scoring formula remain unchanged.',
    'historical_records':'Preserve original JSON/verdicts and LSF state. Reassessment is an additional record, not a rerun or a successful job.'
}

def patch_gate(text):
    old='PPL_MAX_REL_DIFF_PERCENT=0.5  # Example engineering threshold, NOT an official standard'
    new='PPL_MAX_REL_DIFF_PERCENT=5.0  # Rule update 2026-10-19: inclusive +/-5%'
    assert old in text or new in text,'Unknown gate threshold declaration'
    text=text.replace(old,new)
    old_status='    status = "PASS" if abs(diff_pct) <= tolerance else "FAIL"'
    new_status='''    # Decimal bounds keep both stated endpoints inclusive.
    decimal_base = Decimal(str(reference["ppl"]))
    decimal_tolerance = Decimal(tolerance_s) / Decimal("100")
    lower = decimal_base * (Decimal("1") - decimal_tolerance)
    upper = decimal_base * (Decimal("1") + decimal_tolerance)
    status = "PASS" if lower <= Decimal(match[-1]) <= upper else "FAIL"
    result["allowed_ppl_interval"] = [str(lower), str(upper)]
    result["rule_version"] = "20261019_tol5"'''
    if old_status in text:
        text=text.replace('import hashlib\n','import hashlib\nfrom decimal import Decimal\n',1)
        text=text.replace(old_status,new_status)
    else:
        assert new_status in text,'Unknown gate comparison'
    return text

def patch_bounds(text):
    return text.replace('2.755752','2.63112').replace('2.783448','2.90808')

def current_verdict(ppl):
    value=Decimal(str(ppl))
    return 'PASS' if value.is_finite() and Decimal(POLICY['lower_inclusive']) <= value <= Decimal(POLICY['upper_inclusive']) else 'FAIL'
