from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, Request, UploadFile
from fastapi.openapi.utils import get_openapi
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from backend.models.db_helper import db_helper
from backend.routes.tweets_routes import router as tweets_router
from backend.routes.users_rouets import router as users_router
from backend.schemas import Error, OutMediaSchema
from backend.services.other_services import add_image_path_to_db, save_image
from backend.services.security import get_user_id_from_api_key
from backend.tests.factories import generate_data

app = FastAPI()

app.include_router(tweets_router)
app.include_router(users_router)

static_dir = Path(__file__).parent.parent / "static"

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=static_dir)


@app.get("/openapi.json", tags=["documentation"])
async def get_open_api_endpoint(
    _: Annotated[int, Depends(get_user_id_from_api_key)],
) -> JSONResponse:
    """Получение OpenAPI схемы."""
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
    """Загрузка изображения."""
    if file.content_type not in {"image/jpeg", "image/png"}:
        error = Error(
            error_type="Media Type error",
            error_message="Only JPEG and PNG images are allowed.",
        )
        return JSONResponse(status_code=415, content=error.model_dump())

    image_path = await save_image(file)
    image_id = await add_image_path_to_db(session=session, photo_path=image_path)

    return OutMediaSchema(media_id=image_id)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Страница с пользовательским интерфейсом."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test/generate_data")
async def create_test_data():
    """Создание тестовых данных."""
    await generate_data()
    return {"result": True}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
