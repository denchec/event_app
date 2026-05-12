from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter()


@router.get("/health", response_model=JSONResponse)
async def get_wallet_balance():
    return {'status': 'ok'}
