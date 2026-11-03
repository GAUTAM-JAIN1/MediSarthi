import re
from typing import List


def parse_hospital_list(raw_text: str) -> List[dict]:
    if not raw_text:
        return []

    hospitals = []
    current = None

    name_line_re = re.compile(
        r"^[\*\-]\s*(?:\*\*(?P<bold>.+?)\*\*|`(?P<tick>.+?)`)\s*[:,]?\s*(?P<rest>.*)$"
    )

    for line in raw_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        m = name_line_re.match(line)
        if m:
            if current:
                hospitals.append(current)

            name = (m.group("bold") or m.group("tick") or "").strip()
            rest = (m.group("rest") or "").strip()
            rest = re.sub(r"^\*+\s*", "", rest)
            rest = re.sub(r"\s*\*+$", "", rest)

            phone_val = None
            phone_m = re.search(r"\|?\s*Phone\s*:\s*(.+)$", rest, re.IGNORECASE)
            if phone_m:
                phone_text = phone_m.group(1).strip()
                phone_text = re.sub(r"^\*+|\*+$", "", phone_text).strip()
                address_part = rest[: phone_m.start()].strip()
                address_part = re.sub(r"[\|,]\s*$", "", address_part).strip()
                if phone_text and phone_text.lower() not in (
                    "not available", "n/a", "na", "none", "unknown", "not provided", "",
                ):
                    phone_val = phone_text
                rest = address_part

            current = {
                "name": name,
                "address": rest,
                "phone": phone_val,
                "maps_url": None,
            }
            continue

        if current is None:
            continue

        addr_match = re.match(r"^[\*\-]\s*Address:\s*(.+)$", line, re.IGNORECASE)
        if addr_match:
            current["address"] = addr_match.group(1).strip()
            continue

        phone_match = re.match(r"^[\*\-]\s*Phone:\s*(.+)$", line, re.IGNORECASE)
        if phone_match:
            current["phone"] = phone_match.group(1).strip()
            continue

        maps_match = re.match(r"^[\*\-]\s*(?:Maps?|Map URL|Link):\s*(\S+)$", line, re.IGNORECASE)
        if maps_match:
            current["maps_url"] = maps_match.group(1).strip()
            continue

    if current:
        hospitals.append(current)

    return hospitals

