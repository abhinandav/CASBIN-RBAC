from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import casbin
import logging
import json

class AuthorizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enforcer: casbin.Enforcer):
        super().__init__(app)
        self.enforcer = enforcer
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("middleware")

    async def dispatch(self, request: Request, call_next):
        public_paths = ["/", "/docs", "/redoc", "/openapi.json", "/add_policy", "/assign_role"]
        if request.url.path in public_paths:
            return await call_next(request)

        user_roles = request.headers.get("X-User-Roles")
        if not user_roles:
            self.logger.error("User roles not provided")
            return JSONResponse(status_code=403, content={"detail": "User roles not provided"})

        user_roles = user_roles.split(",")  
        resource = request.headers.get("X-Resource")
        if not resource:
            self.logger.error("Resource not provided")
            return JSONResponse(status_code=403, content={"detail": "Resource not provided"})

        action = request.method.upper()
        self.logger.info(f"User roles: {user_roles}, Resource: {resource}, Action: {action}")

        if action in ["POST", "PUT"]:
            body = await request.json()
            fields_to_access = body.keys()

            for field in fields_to_access:
                if not any(self.enforcer.enforce(role, resource, action, field) for role in user_roles):
                    detail = f"None of the user roles have permission to access the field '{field}' in resource '{resource}' with action '{action}'."
                    self.logger.error(detail)
                    return JSONResponse(status_code=403, content={"detail": detail})

            return await call_next(request)

        if action == "DELETE":
            if not any(self.enforcer.enforce(role, resource, action,'all') for role in user_roles):
                detail = f"None of the user roles have permission to delete resource '{resource}'."
                self.logger.error(detail)
                return JSONResponse(status_code=403, content={"detail": detail})

            return await call_next(request)

        original_response = await call_next(request)
        if action == "GET":
            response_body = [section async for section in original_response.body_iterator]
            raw_response = b"".join(response_body).decode()

            self.logger.info(f"Raw response: {raw_response}")

            if not raw_response:
                return original_response

            try:
                response_data = json.loads(raw_response)
                filtered_data = self.filter_response(response_data, user_roles, resource)
                return JSONResponse(content=filtered_data, status_code=original_response.status_code)
            except json.JSONDecodeError:
                self.logger.warning("Response body could not be parsed as JSON.")
                return JSONResponse(status_code=500, content={"detail": "Response body could not be parsed as JSON."})

        return original_response

    def filter_response(self, response_data, user_roles, resource):
        filtered_data = {}
        for key in response_data.keys():
            if any(self.enforcer.enforce(role, resource, "GET", key) for role in user_roles):
                filtered_data[key] = response_data[key]
            else:
                self.logger.info(f"None of the user roles have access to field '{key}' in resource '{resource}'.")
        
        return filtered_data
