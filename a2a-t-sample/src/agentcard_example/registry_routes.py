from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from agentcard_example.registry_data import get_card, store_card


async def register_agentcards(request: Request) -> JSONResponse:
    body = await request.json()
    agent_cards = body.get("agentCards", [])
    for card in agent_cards:
        if isinstance(card, dict):
            store_card(card)
    return JSONResponse(
        {"status": "success", "message": "Agent card registered successfully"},
        status_code=201,
    )


async def query_agentcard_by_name_org(request: Request) -> JSONResponse:
    organization = request.path_params["organization"]
    name = request.path_params["name"]
    card = get_card(organization, name)
    if card is None:
        return JSONResponse(
            {"errors": {"error": [{"errorMessage": "Agent not found"}]}},
            status_code=404,
        )
    return JSONResponse({"agentCards": [card]}, status_code=200)


def build_registry_app() -> Starlette:
    routes = [
        Route(
            path="/rest/v1/registry-center/agent-cards",
            endpoint=register_agentcards,
            methods=["POST"],
        ),
        Route(
            path="/rest/v1/registry-center/agent-cards/{organization}/{name}",
            endpoint=query_agentcard_by_name_org,
            methods=["GET"],
        ),
    ]
    return Starlette(routes=routes)
