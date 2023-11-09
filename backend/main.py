from typing import Annotated

from fastapi import Depends, FastAPI, Request, UploadFile
from fastapi.openapi.utils import get_openapi
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from backend.config import STATIC_DIR
from backend.models.db_helper import db_helper
from backend.routes.tweets_routes import router as tweets_router
from backend.routes.users_rouets import router as users_router
from backend.schemas import Error, OutMediaSchema
from backend.services.medias_services import add_image_path_to_db, save_image
from backend.services.security import get_user_id_from_api_key
from backend.tests.factories import generate_data

app = FastAPI()

app.include_router(tweets_router)
app.include_router(users_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=STATIC_DIR)


@app.get("/openapi.json", tags=["documentation"])
async def get_open_api_endpoint(
    _: Annotated[int, Depends(get_user_id_from_api_key)],
) -> JSONResponse:
    """Get OpenAPI schema."""
    return JSONResponse(
        get_openapi(
            title="FastAPI security test",
            version="1.0",
            routes=app.routes,
        ),
    )


@app.post(
    "/api/medias",
    status_code=201,
    tags=["tweets"],
    response_model=OutMediaSchema,
    responses={415: {"model": Error}},
)
async def upload_image(
    file: UploadFile,
    _: Annotated[int, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Upload an image. Expects a JPEG or PNG image."""
    error = Error(
        error_type="Media Type error",
        error_message="Only JPEG and PNG images are allowed.",
    )

    if file.content_type not in {"image/jpeg", "image/png"}:
        return JSONResponse(status_code=415, content=error.model_dump())

    file_data = await file.read()
    try:
        image_path = await save_image(image=file_data)
    except TypeError:
        return JSONResponse(status_code=415, content=error.model_dump())

    image_id = await add_image_path_to_db(session=session, photo_path=image_path)

    return OutMediaSchema(media_id=image_id)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """User interface page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test/generate_data")
async def create_test_data(
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Create test data."""
    await generate_data(session=session)
    return {"result": True}
