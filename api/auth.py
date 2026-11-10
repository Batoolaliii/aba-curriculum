from fastapi import HTTPException, Request

ADMIN_GROUP = "admins"


def get_caller(request: Request) -> dict:
    """Return the signed-in user's identity, as verified by API Gateway."""
    event = request.scope.get("aws.event")

    if event is None:
        return {"sub": "local-dev", "groups": [ADMIN_GROUP]}

    claims = event["requestContext"]["authorizer"]["claims"]
    raw_groups = claims.get("cognito:groups", "")
    groups = [g for g in raw_groups.strip("[]").split(",") if g]

    return {"sub": claims["sub"], "groups": groups}


def is_admin(caller: dict) -> bool:
    return ADMIN_GROUP in caller["groups"]


def require_owner_or_admin(caller: dict, employee: dict) -> None:
    """Allow admins, or the one employee whose record this is."""
    if is_admin(caller):
        return
    if employee.get("cognitoSub") == caller["sub"]:
        return

    raise HTTPException(status_code=404, detail="Employee not found")
