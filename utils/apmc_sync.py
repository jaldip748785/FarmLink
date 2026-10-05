import os
from datetime import datetime, date
from decimal import Decimal

import requests
from flask import current_app

from models import db
from models.apmc_rate import APMCRate


def _coerce_decimal(value):
    if value in (None, "", "N/A", "NA", "null", "None"):
        return None
    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        return None


def _parse_rate_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    return None


def _pick_value(record, *keys):
    if not isinstance(record, dict):
        return None
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    normalized = {str(k).lower(): v for k, v in record.items() if isinstance(k, str)}
    for key in keys:
        key_lower = str(key).lower()
        if key_lower in normalized and normalized[key_lower] not in (None, ""):
            return normalized[key_lower]
        alt = key_lower.replace("_", "")
        if alt in normalized and normalized[alt] not in (None, ""):
            return normalized[alt]
    return None


def _normalize_record(record):
    commodity_name = _pick_value(record, "commodity_name", "commodity", "commodity_name_en", "commodity_name_hi")
    market_name = _pick_value(record, "market_name", "market", "apmc_market", "market_name_en")
    state = _pick_value(record, "state", "state_name")
    district_name = _pick_value(record, "district", "district_name", "district_name_en")
    modal_price = _coerce_decimal(_pick_value(record, "modal_price", "modal_price_rs", "modal_price_in_rs", "price"))
    minimum_price = _coerce_decimal(_pick_value(record, "minimum_price", "min_price", "min_price_rs", "minimum_price_rs"))
    maximum_price = _coerce_decimal(_pick_value(record, "maximum_price", "max_price", "max_price_rs", "maximum_price_rs"))
    unit = _pick_value(record, "unit", "unit_name", "price_unit") or "kg"
    source = _pick_value(record, "source", "source_name") or "OGD API"
    rate_date = _parse_rate_date(_pick_value(record, "date", "rate_date", "report_date", "created_at")) or date.today()

    return {
        "commodity_name": str(commodity_name).strip() if commodity_name else None,
        "market_name": str(market_name).strip() if market_name else None,
        "state": str(state).strip() if state else None,
        "district_name": str(district_name).strip() if district_name else None,
        "modal_price": modal_price if modal_price is not None else Decimal("0"),
        "minimum_price": minimum_price,
        "maximum_price": maximum_price,
        "unit": str(unit).strip() or "kg",
        "rate_date": rate_date,
        "source": str(source).strip() or "OGD API",
    }


def sync_apmc_rates_from_api(api_key=None):
    api_key = (api_key or os.getenv("OGD_API_KEY") or current_app.config.get("OGD_API_KEY", "") or "").strip()
    resource_id = (os.getenv("OGD_APMC_RESOURCE_ID") or current_app.config.get("OGD_APMC_RESOURCE_ID", "") or "9ef84268-d588-465a-a308-a864a43d0070").strip()
    base_url = (os.getenv("OGD_APMC_API_BASE_URL") or current_app.config.get("OGD_APMC_API_BASE_URL", "") or "https://api.data.gov.in").strip()

    if not api_key or not resource_id:
        raise ValueError("OGD API key is not configured. Please enter your API key before syncing.")

    endpoints = [
        f"{base_url.rstrip('/')}/resource/{resource_id}?api-key={api_key}&format=json&limit=1000",
        f"{base_url.rstrip('/')}/api/{resource_id}?api-key={api_key}&format=json&limit=1000",
    ]

    last_error = None
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=25)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            last_error = exc
            continue

        records = []
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            for key in ("records", "data", "result", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    records = value
                    break
                if isinstance(value, dict):
                    records = [value]
                    break
            if not records and "records" in payload and isinstance(payload["records"], dict):
                records = [payload["records"]]

        if not records:
            continue

        imported = 0
        updated = 0
        skipped = 0
        for raw in records:
            normalized = _normalize_record(raw)
            if not normalized["commodity_name"] or not normalized["market_name"]:
                skipped += 1
                continue

            existing = APMCRate.query.filter_by(
                commodity_name=normalized["commodity_name"],
                market_name=normalized["market_name"],
                rate_date=normalized["rate_date"],
            ).first()

            if existing:
                existing.state = normalized["state"] or existing.state
                existing.modal_price = normalized["modal_price"] if normalized["modal_price"] is not None else existing.modal_price
                existing.minimum_price = normalized["minimum_price"] if normalized["minimum_price"] is not None else existing.minimum_price
                existing.maximum_price = normalized["maximum_price"] if normalized["maximum_price"] is not None else existing.maximum_price
                existing.unit = normalized["unit"] or existing.unit
                existing.source = normalized["source"] or existing.source
                updated += 1
            else:
                rate = APMCRate(
                    commodity_name=normalized["commodity_name"],
                    market_name=normalized["market_name"],
                    state=normalized["state"],
                    modal_price=normalized["modal_price"],
                    minimum_price=normalized["minimum_price"],
                    maximum_price=normalized["maximum_price"],
                    unit=normalized["unit"],
                    rate_date=normalized["rate_date"],
                    source=normalized["source"],
                )
                db.session.add(rate)
                imported += 1

        db.session.commit()
        return {"imported": imported, "updated": updated, "skipped": skipped, "endpoint": endpoint}

    raise RuntimeError(f"Unable to fetch APMC rates from the OGD API: {last_error}")
