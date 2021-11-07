# Run using: uvicorn run:app --reload --port 3000
# FastAPI simultaneously creates documentation for us on localhost:3000/docs

from fastapi import FastAPI, Depends, HTTPException
from routes.v1 import app_v1
from routes.v2 import app_v2
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED
from utils.security import check_jwt_token
from datetime import datetime
from fastapi.security import OAuth2PasswordRequestForm
from utils.security import authenticate_user, create_jwt_token
from models.jwt_user import JWTUser
from utils.const import TOKEN_SUMMARY, TOKEN_DESCRIPTION, REDIS_URL
from utils.db_object import db
import aioredis
import utils.redis_object as re


app = FastAPI(title="Bookstore API Documentation", description="It's an API that is used for bookstores.", version="1.0.0")

#  Use API router to check jwt token to authenticate every endpoint
# We change our versioning system with Depends so we authorization mechanism in swagger documentation
app.include_router(app_v1, prefix="/v1", dependencies=[Depends(check_jwt_token)])
app.include_router(app_v2, prefix="/v2", dependencies=[Depends(check_jwt_token)])


@app.on_event("startup")
async def connect_db():
    await db.connect()
    re.redis = await aioredis.create_redis_pool(REDIS_URL)  # Connect to redis cache


@app.on_event("shutdown")
async def disconnect_db():
    await db.disconnect()

    re.redis.close()
    await re.redis.wait_closed()  # disconnect redis


# Create endpoint that takes and verifies username and password from user
@app.post("/token", description=TOKEN_DESCRIPTION, summary=TOKEN_SUMMARY)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    jwt_user_dict = {"username": form_data.username,
                     "password": form_data.password}
    jwt_user = JWTUser(**jwt_user_dict)

    user = await authenticate_user(jwt_user)
    if user is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    jwt_token = create_jwt_token(user)
    # return access_token so OAUTH2 can recognize the token
    return {"access_token": jwt_token}


# Implement our middleware
# Instead of defining the jwt_token to authenticate using OAUTH every single endpoint
# we implement the check jwt token in the middle request
@app.middleware("http")
async def middleware(request: Request, call_next):
    start_time = datetime.utcnow()
    # modify request herew

    response = await call_next(request)  # Use await because it's async func

    # modify response here
    execution_time = (datetime.utcnow() - start_time).microseconds
    response.headers["x-execution-time"] = str(execution_time)
    return response
