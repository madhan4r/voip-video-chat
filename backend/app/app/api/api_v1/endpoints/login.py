from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils import (
    generate_password_reset_token,
    send_reset_password_email,
    verify_password_reset_token,
)
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import SyncGrant, VoiceGrant, VideoGrant, ChatGrant
from app.core import config
from twilio.twiml.voice_response import VoiceResponse, Dial
import re

router = APIRouter()


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}", response_model=schemas.Msg)
def recover_password(email: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Password Recovery
    """
    user = crud.user.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Password recovery email sent"}


@router.post("/reset-password/", response_model=schemas.Msg)
def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    return {"msg": "Password updated successfully"}


@router.post("/communication/token")
def generate_voice_call_token(
    identity: str,
):
    account_sid = config.settings.TWILIO_ACCOUNT_SID
    api_key = config.settings.TWILIO_API_KEY
    api_secret = config.settings.TWILIO_API_SECRET
    twiml_application_sid = config.settings.TWIML_APPLICATION_SID
    TWILIO_CHAT_SERVICE_SID = config.settings.TWILIO_CHAT_SERVICE_SID

    # Create access token with credentials
    token = AccessToken(account_sid, api_key, api_secret, identity=identity)

    # Create a Voice grant and add to token
    voice_grant = VoiceGrant()
    voice_grant.incoming_allow = True
    voice_grant.outgoing_application_sid = twiml_application_sid
    token.add_grant(voice_grant)

    # Create a Video grant and add to token
    video_grant = VideoGrant()
    token.add_grant(video_grant)

    # Create an Chat grant and add to token
    if TWILIO_CHAT_SERVICE_SID:
        chat_grant = ChatGrant(service_sid=TWILIO_CHAT_SERVICE_SID)
        token.add_grant(chat_grant)

    # Return token info as JSON
    decode_token = token.to_jwt().decode('utf-8')
    return {"identity":identity, "token":decode_token}

phone_pattern = re.compile(r"^[\d\+\-\(\) ]+$")

IDENTITY = {"identity": ""}

@router.post("/communication/call")
async def make_outgoing_voice_call(request: Request):
    response = VoiceResponse()
    number = await request.form()
    print(number)
    if number["To"] == config.settings.TWILIO_CALLER_ID:
        # Receiving an incoming call to our Twilio number
        dial = Dial()
        # Route to the most recently created client based on the identity stored in the session
        dial.client(IDENTITY["identity"])
        response.append(dial)
    elif number["phone"]:
        # Placing an outbound call from the Twilio client
        dial = Dial(caller_id=config.settings.TWILIO_CALLER_ID)
        # wrap the phone number or client name in the appropriate TwiML verb
        # by checking if the number given has only digits and format symbols
        if phone_pattern.match(number["phone"]):
            dial.number(number["phone"])
        else:
            dial.client(number["phone"])
        response.append(dial)
    else:
        response.say("Thanks for calling!")

    return Response(str(response), media_type="text/xml")