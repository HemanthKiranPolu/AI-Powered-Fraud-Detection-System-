from __future__ import annotations

import re
from typing import Optional, Tuple


WEIGHTS = [7, 3, 1]


def _char_value(c: str) -> int:
    if c.isdigit():
        return int(c)
    if c == '<':
        return 0
    return ord(c.upper()) - 55  # A=10


def _check_digit(field: str) -> int:
    total = 0
    for i, ch in enumerate(field):
        total += _char_value(ch) * WEIGHTS[i % 3]
    return total % 10


def validate_mrz(lines: list[str]) -> Tuple[bool, dict]:
    """Validate MRZ checksum for TD1/TD3 formats when possible.
    Returns (valid, parsed_fields)
    """
    parsed: dict = {}
    if not lines:
        return False, parsed
    # Normalize
    lns = [re.sub(r"\s", "", l) for l in lines if l and len(l) >= 30]
    if len(lns) == 2 and len(lns[0]) in (44,) and len(lns[1]) in (44,):
        # TD3 passport
        l1, l2 = lns
        passport_num = l2[0:9]
        cd1 = l2[9]
        dob = l2[13:19]
        cd2 = l2[19]
        expiry = l2[21:27]
        cd3 = l2[27]
        composite = passport_num + cd1 + dob + cd2 + expiry + cd3 + l2[28:43]
        comp_cd = l2[43]
        ok = (
            str(_check_digit(passport_num)) == cd1
            and str(_check_digit(dob)) == cd2
            and str(_check_digit(expiry)) == cd3
            and str(_check_digit(composite)) == comp_cd
        )
        parsed.update({"passport_number": passport_num.replace('<', ''), "dob": dob, "expiry": expiry})
        return ok, parsed
    if len(lns) == 3 and len(lns[0]) in (30,) and len(lns[1]) in (30,) and len(lns[2]) in (30,):
        # TD1 ID card
        l1, l2, l3 = lns
        doc_num = l1[5:14]
        cd1 = l1[14]
        dob = l2[0:6]
        cd2 = l2[6]
        expiry = l2[8:14]
        cd3 = l2[14]
        composite = doc_num + cd1 + dob + cd2 + expiry + cd3 + l1[15:30] + l2[15:30]
        comp_cd = l3[29]
        ok = (
            str(_check_digit(doc_num)) == cd1
            and str(_check_digit(dob)) == cd2
            and str(_check_digit(expiry)) == cd3
            and str(_check_digit(composite)) == comp_cd
        )
        parsed.update({"id_number": doc_num.replace('<', ''), "dob": dob, "expiry": expiry})
        return ok, parsed
    return False, parsed

