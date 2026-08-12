from __future__ import annotations


def build_subscription_request() -> dict[str, object]:
    return {
        "scenario": "subscribe_incident",
        "agent_card_query": {
            "name": "A2A-T Subscribe Incident Sample",
            "organization": "SampleOrg",
        },
        "subscription_filter": {
            "alarm_type": "flash",
            "severity": "critical",
            "province": "fujian",
        },
        "subscription_condition_incident_level": ["critical"],
        "subscription_condition_incident_name": ["fiber break"],
        "diagnosis_context": {
            "domain": "spn",
            "source": "transport_workspace",
        },
    }
