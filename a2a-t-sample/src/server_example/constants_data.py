from __future__ import annotations

from copy import deepcopy
from typing import Any

SUBMITTED_MESSAGE = "Subscription accepted, starting Incident reporting task"
WORKING_MESSAGE = "Incident reporting task in progress"
COMPLETED_MESSAGE = "Incident reporting completed"
ARTIFACT_SEND_INTERVAL_SECONDS = 5.0

PUBLIC_AGENT_CARD: dict[str, Any] = {
    "name": "A2A-T Subscribe Incident Sample",
    "description": "A2A-T sample server for incident subscription with streaming artifact push",
    "version": "1.0.0",
    "provider": {"organization": "SampleOrg"},
    "skills": [
        {
            "id": "incident-subscription",
            "name": "Incident Subscription",
            "description": "Subscribe to incident notifications with streaming artifact push",
            "tags": ["incident", "subscription", "streaming"],
        }
    ],
    "capabilities": {
        "streaming": True,
        "pushNotifications": False,
        "extensions": [
            {
                "uri": "https://projects.tmforum.org/a2aproject/telecommunication/extensions/Notification-T/v1",
                "description": "Extension of structured prompt Notification-T requests.",
            }
        ],
    },
    "defaultInputModes": ["text", "json"],
    "defaultOutputModes": ["text", "json"],
    "supportedInterfaces": [],
}

INCIDENT_ARTIFACT_DATA: dict[str, Any] = {
    "faultManagement.Incident": {
        "csn": 1673735459373056,
        "name": "LASER_MOD_ERR",
        "domain": "PTN",
        "priority": "high",
        "occurTime": "2026-04-28T07:21:00Z",
        "createTime": "2026-04-28T07:29:19Z",
        "updateTime": "2026-04-28T12:35:15Z",
        "status": "unacknowledged-and-uncleared",
        "category": "Line",
        "sourceObjects": [
            {
                "id": "9fc7ee3b-e4fb-450e-87d3-e03f027a4f64",
                "type": "network-element",
                "location": "Level1",
                "name": "HUAWEI40-SPE",
            }
        ],
        "rootCauses": [
            {
                "name": "HUAWEI40-SPE power failure",
                "repairAdvice": "Check power connection.",
            }
        ],
        "detail": "HUAWEI40-SPE laser module error at 1-TPA1EG24-15(M)-LASER:1.",
        "repairAdvice": "Check power connection.",
        "messageType": "update",
    }
}


def get_public_agent_card() -> dict[str, Any]:
    return deepcopy(PUBLIC_AGENT_CARD)


def get_incident_artifact_data() -> dict[str, Any]:
    return deepcopy(INCIDENT_ARTIFACT_DATA)
