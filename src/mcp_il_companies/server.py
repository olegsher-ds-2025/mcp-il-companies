"""mcp-il-companies — due diligence on Israeli companies, partnerships, nonprofits (עמותות) and PBCs (חל"צ).

All data is queried live from data.gov.il (Registrar of Companies, Registrar of Amutot — Ministry of Justice).
"""
from __future__ import annotations

import asyncio
import os
from datetime import date

from fastmcp import FastMCP

from .ckan import datastore_search, meta

R_COMPANIES = "f004176c-b85f-4542-8901-7b3176f9a054"  # מאגר חברות - רשם החברות
R_PARTNERSHIPS = "139aa193-fabb-4f6b-a71b-0bb40fd73eb2"  # מאגר שותפויות
R_CHANGES = "28780ab5-3ef1-44c7-8377-da82c0aa6781"  # פרטי שינויים בתאגידים (שעבודים ועוד)
R_LIQUIDATION = "6f3f0df3-5968-4135-81c5-8dd76bf89410"  # חברות בפירוק מרצון בהליך מזורז
R_AMUTOT = "be5b7935-3922-45d4-9638-08871b17ec95"  # עמותות רשומות
R_PBC = "85e40960-5426-4f4c-874f-2d1ec1b94609"  # חברות לתועלת הציבור
R_PROPER_MGMT = "cb12ac14-7429-4268-bc03-460f48157858"  # אישור ניהול תקין
R_FOREIGN_DONATIONS = "35cb40b5-3f13-4bca-9ce2-488085913107"  # תרומות מישות מדינית זרה

DS = {
    "companies": "Registrar of Companies — companies",
    "partnerships": "Registrar of Companies — partnerships",
    "changes": "Registrar of Companies — changes/charges",
    "liquidation": "Registrar of Companies — fast-track voluntary liquidation",
    "amutot": "Registrar of Amutot — nonprofits",
    "pbc": "Registrar of Amutot — public benefit companies",
    "proper": "Registrar of Amutot — proper management certificates",
    "foreign": "Registrar of Amutot — donations from foreign state entities",
}

mcp = FastMCP(
    "mcp-il-companies",
    instructions=(
        "Israeli corporate registry lookups. Use find_entity to resolve a name to a registration number, then "
        "entity_profile or due_diligence for details. Numbers starting 51/52 are companies, 55 partnerships, "
        "58 nonprofits (amutot). Data is Hebrew; names may be given in Hebrew or English."
    ),
)


def _num(n: str | int) -> int:
    s = str(n).strip().replace("-", "").replace(" ", "")
    if not s.isdigit():
        raise ValueError("Registration number must be digits, e.g. 515052702")
    return int(s)


def _company(r: dict) -> dict:
    return {
        "type": "company",
        "number": r.get("מספר חברה"),
        "name_he": r.get("שם חברה"),
        "name_en": r.get("שם באנגלית"),
        "corporation_type": r.get("סוג תאגיד"),
        "status": r.get("סטטוס חברה"),
        "sub_status": r.get("תת סטטוס"),
        "purpose": r.get("מטרת החברה"),
        "description": r.get("תאור חברה"),
        "incorporated": r.get("תאריך התאגדות"),
        "government_company": r.get("חברה ממשלתית"),
        "limitation": r.get("מגבלות"),
        "violator": r.get("מפרה"),
        "last_annual_report_year": r.get("שנה אחרונה של דוח שנתי (שהוגש)"),
        "address": ", ".join(
            str(x) for x in (r.get("שם רחוב"), r.get("מספר בית"), r.get("שם עיר"), r.get("מדינה")) if x
        )
        or None,
        "zip": r.get("מיקוד"),
    }


def _partnership(r: dict) -> dict:
    return {
        "type": "partnership",
        "number": r.get("מספר שותפות"),
        "name_he": r.get("שם שותפות"),
        "name_en": r.get("שם באנגלית"),
        "corporation_type": r.get("סוג תאגיד"),
        "status": r.get("סטטוס תאגיד"),
        "incorporated": r.get("תאריך התאגדות"),
        "address": ", ".join(str(x) for x in (r.get("רחוב"), r.get("מספר בית"), r.get("ישוב")) if x) or None,
    }


def _amuta(r: dict) -> dict:
    return {
        "type": "nonprofit",
        "number": r.get("מספר עמותה"),
        "name_he": r.get("שם עמותה בעברית"),
        "name_en": r.get("שם עמותה באנגלית"),
        "status": r.get("סטטוס עמותה"),
        "registered": r.get("תאריך רישום עמותה"),
        "sector": r.get("סיווג פעילות ענפי"),
        "secondary_field": r.get("תחום פעילות משני"),
        "goals": r.get("מטרות עמותה"),
        "last_financial_report_year": r.get("שנת דיווח דוח כספי אחרון"),
        "revenue": r.get("מחזור כספי (הכנסות)"),
        "expenses": r.get("סך הוצאות העמותה"),
        "employees": r.get("כמות עובדים"),
        "volunteers": r.get("כמות מתנדבים"),
        "members": r.get("מספר חברי עמותה"),
        "activity_regions": r.get("איזורי פעילות"),
        "city": r.get("כתובת - ישוב"),
        "street": r.get("כתובת - רחוב"),
    }


def _pbc(r: dict) -> dict:
    return {
        "type": "public_benefit_company",
        "number": r.get("מספר חלצ"),
        "name_he": r.get("שם חלצ בעברית"),
        "name_en": r.get("שם חלצ באנגלית"),
        "status": r.get("סטטוס חלצ"),
        "sector": r.get("סיווג פעילות ענפי"),
        "field": r.get("תחום פעילות"),
        "goals": r.get("מטרות ארגון רשמיות"),
        "last_financial_report_year": r.get("שנת דיווח דוח כספי אחרון"),
        "revenue": r.get("מחזור - נתונים מדוח מילולי מקוון"),
        "employees": r.get("עובדים- נתונים מדוח מילולי מקוון"),
        "volunteers": r.get("מתנדבים- נתונים מדוח מילולי מקוון"),
        "city": r.get("כתובת - ישוב"),
        "last_deep_audit": r.get("תאריך ביקורת עומק אחרונה"),
    }


def _brief(e: dict) -> dict:
    return {k: e.get(k) for k in ("type", "number", "name_he", "name_en", "status")}


@mcp.tool
async def find_entity(name: str, entity_type: str = "any", limit: int = 10) -> dict:
    """Find Israeli companies, partnerships, nonprofits (עמותות) or public benefit companies by name.

    Args:
        name: Full or partial name, Hebrew or English (e.g. "וסטמה" or "Vastama").
        entity_type: "any", "company", "partnership", "nonprofit" or "pbc".
        limit: Max results per registry (1-50).
    """
    limit = max(1, min(limit, 50))
    jobs = {
        "company": (R_COMPANIES, _company, "companies"),
        "partnership": (R_PARTNERSHIPS, _partnership, "partnerships"),
        "nonprofit": (R_AMUTOT, _amuta, "amutot"),
        "pbc": (R_PBC, _pbc, "pbc"),
    }
    if entity_type != "any" and entity_type not in jobs:
        raise ValueError("entity_type must be any, company, partnership, nonprofit or pbc")
    chosen = jobs if entity_type == "any" else {entity_type: jobs[entity_type]}
    results = await asyncio.gather(
        *(datastore_search(rid, q=name, limit=limit) for rid, _, _ in chosen.values()), return_exceptions=True
    )
    matches, totals, errors, sources = [], {}, {}, []
    for (kind, (_, mapper, ds_key)), res in zip(chosen.items(), results, strict=True):
        if isinstance(res, Exception):
            errors[kind] = str(res)
            continue
        totals[kind] = res["total"]
        sources.append(DS[ds_key])
        matches += [_brief(mapper(r)) for r in res["records"]]
    out = {"query": name, "total_by_registry": totals, "matches": matches, **meta(sources or "n/a")}
    if errors:
        out["errors"] = errors
    return out


async def _lookup(number: int) -> dict:
    keys = ["company", "partnership", "nonprofit", "pbc", "changes", "liquidation", "proper", "foreign"]
    calls = [
        datastore_search(R_COMPANIES, filters={"מספר חברה": number}, limit=1),
        datastore_search(R_PARTNERSHIPS, filters={"מספר שותפות": number}, limit=1),
        datastore_search(R_AMUTOT, filters={"מספר עמותה": number}, limit=1),
        datastore_search(R_PBC, filters={"מספר חלצ": number}, limit=1),
        datastore_search(R_CHANGES, filters={"מספר תאגיד": number}, limit=50, sort="_id desc"),
        datastore_search(R_LIQUIDATION, filters={"מספר חברה": number}, limit=1),
        datastore_search(R_PROPER_MGMT, filters={"מספר עמותה": str(number)}, limit=50),
        datastore_search(R_FOREIGN_DONATIONS, q=str(number), limit=20),
    ]
    res = await asyncio.gather(*calls, return_exceptions=True)
    return {k: (None if isinstance(v, Exception) else v) for k, v in zip(keys, res, strict=True)}


def _entity_from(raw: dict) -> dict | None:
    for key, mapper in (("company", _company), ("partnership", _partnership), ("nonprofit", _amuta), ("pbc", _pbc)):
        part = raw.get(key)
        if part and part["records"]:
            return mapper(part["records"][0])
    return None


@mcp.tool
async def entity_profile(number: str) -> dict:
    """Full registry profile for one registration number (company, partnership, nonprofit or PBC),
    including recent registry changes (e.g. charges/שעבודים), liquidation status and nonprofit certificates."""
    n = _num(number)
    raw = await _lookup(n)
    entity = _entity_from(raw)
    if not entity:
        return {"number": n, "found": False, "message": "No entity with this number in the open registries.",
                **meta("Registrar of Companies / Registrar of Amutot")}
    changes = raw["changes"]["records"] if raw["changes"] else []
    proper = raw["proper"]["records"] if raw["proper"] else []
    return {
        "found": True,
        "entity": entity,
        "registry_changes": [
            {"request_type": c.get("סוג בקשה"), "status_date": c.get("תאריך עדכון סטטוס")} for c in changes
        ],
        "fast_track_liquidation": (raw["liquidation"]["records"][0] if raw["liquidation"] and raw["liquidation"]["records"] else None),
        "proper_management_certificates": [
            {"year": p.get("שנת האישור"), "status": p.get("האם יש אישור"), "request": p.get("הגשת בקשה")}
            for p in sorted(proper, key=lambda p: p.get("שנת האישור") or 0, reverse=True)
        ],
        "foreign_state_donations": (raw["foreign"]["records"] if raw["foreign"] else []),
        **meta(list(DS.values())),
    }


@mcp.tool
async def due_diligence(number: str) -> dict:
    """Quick red-flag check for a counterparty (supplier, client, investee, grantee).

    Flags: not active, registry 'violator' (מפרה), stale annual reports, fast-track liquidation,
    many recent charges, missing nonprofit proper-management certificate. Returns a risk level with reasons.
    """
    n = _num(number)
    raw = await _lookup(n)
    entity = _entity_from(raw)
    if not entity:
        return {"number": n, "found": False, "risk": "unknown", "flags": ["Not found in open registries"],
                **meta("Registrar of Companies / Registrar of Amutot")}

    flags: list[str] = []
    positives: list[str] = []
    status = entity.get("status") or ""
    if status not in ("פעילה", "רשומה"):
        flags.append(f"Status is '{status}' (not active)")
    else:
        positives.append(f"Status: {status}")
    if entity.get("violator"):
        flags.append("Marked as violator (מפרה) by the Registrar — usually unpaid annual fees or missing reports")
    this_year = date.today().year
    last_rep = entity.get("last_annual_report_year") or entity.get("last_financial_report_year")
    if isinstance(last_rep, (int, float)):
        if this_year - int(last_rep) >= 2:
            flags.append(f"Last annual/financial report filed for {int(last_rep)}")
        else:
            positives.append(f"Recent report filed ({int(last_rep)})")
    if raw["liquidation"] and raw["liquidation"]["records"]:
        flags.append("In fast-track voluntary liquidation")
    changes = raw["changes"]["records"] if raw["changes"] else []
    charges = [c for c in changes if "שעבוד" in (c.get("סוג בקשה") or "")]
    if charges:
        flags.append(f"{len(charges)} charge-related registry filings (שעבודים) — check for secured debt")
    if entity["type"] == "nonprofit":
        proper = raw["proper"]["records"] if raw["proper"] else []
        years_ok = sorted({p.get("שנת האישור") for p in proper if "נחתם" in (p.get("האם יש אישור") or "")})
        if not years_ok:
            flags.append("No proper-management certificate (אישור ניהול תקין) on record")
        elif this_year - max(years_ok) >= 2:
            flags.append(f"Latest proper-management certificate is for {max(years_ok)}")
        else:
            positives.append(f"Proper-management certificate for {max(years_ok)}")
    if raw["foreign"] and raw["foreign"]["records"]:
        flags.append("Reports donations from foreign state entities (disclosure, not necessarily negative)")

    hard = any(k in f for f in flags for k in ("not active", "violator", "liquidation"))
    risk = "high" if hard else ("medium" if flags else "low")
    return {
        "found": True,
        "entity": _brief(entity),
        "risk": risk,
        "flags": flags,
        "positives": positives,
        "note": "Automated screen of public registry data only — not legal or credit advice.",
        **meta(list(DS.values())),
    }


@mcp.tool
async def search_nonprofits(
    query: str = "", sector: str = "", city: str = "", active_only: bool = True, limit: int = 20
) -> dict:
    """Search Israeli nonprofits (עמותות) by keyword, sector words (e.g. "חינוך", "רווחה", "בריאות") and exact city name."""
    filters: dict = {}
    if active_only:
        filters["סטטוס עמותה"] = "רשומה"
    if city:
        filters["כתובת - ישוב"] = city
    q = " ".join(x for x in (query, sector) if x) or None
    res = await datastore_search(R_AMUTOT, q=q, filters=filters or None, limit=max(1, min(limit, 100)))
    return {"total": res["total"], "results": [_amuta(r) for r in res["records"]], **meta(DS["amutot"])}


@mcp.tool
async def health() -> dict:
    """Check that the server can reach data.gov.il."""
    try:
        res = await datastore_search(R_COMPANIES, limit=1)
        return {"status": "ok", "companies_in_registry": res["total"], **meta(DS["companies"])}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}


def main() -> None:
    if os.environ.get("MCP_TRANSPORT", "stdio") == "stdio":
        mcp.run()
    else:
        mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
