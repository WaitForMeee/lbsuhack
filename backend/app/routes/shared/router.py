"""Mutation response metadata, shared by all business routes."""
import json
from fastapi import APIRouter as BaseRouter
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse

class MutationRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handle(request):
            response = await original(request)
            if request.method not in {"POST", "PATCH", "PUT", "DELETE"} or "/auth/" in request.url.path:
                return response
            if 200 <= response.status_code < 300 and "application/json" in response.headers.get("content-type", ""):
                if getattr(request.state, "demo_read_only", False):
                    return JSONResponse({"demo_mode": True})
                data = json.loads(response.body)
                data["demo_mode"] = False
                headers = {k: v for k, v in response.headers.items() if k not in {"content-length", "content-type"}}
                return JSONResponse(data, status_code=response.status_code, headers=headers, background=response.background)
            return response
        return handle

class APIRouter(BaseRouter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("route_class", MutationRoute)
        super().__init__(*args, **kwargs)
