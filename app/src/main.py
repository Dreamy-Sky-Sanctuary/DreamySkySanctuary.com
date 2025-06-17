import typing

from fastapi import Form
from fastapi.responses import HTMLResponse
from src.utils.database import create_connection
from src.utils.flash import flash, get_flashed_messages, FlashCategory
from src.utils.refresh_team_file import refresh_team_file
from src.dependencies import *
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.schemas.errors.FileNotFoundException import FileNotFoundException
from src.schemas.errors.FileTypeException import FileTypeException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi_login.exceptions import InvalidCredentialsException, InsufficientScopeException
import http
from jinja2 import Environment
from src.routes.auth.auth import login_manager

# app config
app = FastAPI(
    title=config.APP_NAME,
    description=config.DESCRIPTION,
    version=config.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CLIENT_ORIGIN,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware, 
    secret_key=config.SERVER_SECRET,
)

login_manager.attach_middleware(app)

# mount static files
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
app.mount("/public", StaticFiles(directory=config.PUBLIC_DIR), name="public")
app.mount('/images', StaticFiles(directory=config.UPLOAD_DIR), name='images')

app.include_router(main_route.router)
app.include_router(auth_route.router)
app.include_router(file_upload_route.router)

templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
templates.env.globals["get_flashed_messages"] = get_flashed_messages

connection = create_connection("Website")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    http_status = http.HTTPStatus(exc.status_code)
    context = {"request": request, "exc": exc, "http_status": http_status}
    
    if exc.status_code == 401:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    
    if http_status.is_client_error:
        return templates.TemplateResponse(
            name="error/error.html",
            context=context,
            status_code=exc.status_code,
            headers=exc.headers,
        )
    
    if http_status.is_server_error:
        return templates.TemplateResponse(
            name="error/error.html",
            context=context,
            status_code=exc.status_code,
            headers=exc.headers,
        )

# @app.exception_handler(InvalidCredentialsException)
# def invalid_credentials_handler(request, exc: HTTPException):
#     return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


# @app.exception_handler(InsufficientScopeException)
# def insufficient_scope_handler(request, exc: HTTPException):
#     pass
#     # return RedirectResponse(request.headers.get('referer') if request.headers.get('referer').startswith(str(request.base_url)) else "/upload", status_code=status.HTTP_303_SEE_OTHER)



@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    print(f"ValueError: {exc}")
    flash(request, "The given input was not valid, pls check your input", FlashCategory.DANGER)
    return RedirectResponse(request.headers.get('referer') if request.headers.get('referer').startswith(str(request.base_url)) else "/register", status_code=status.HTTP_303_SEE_OTHER) # redirect to the previous page if a validation error is raised. or to the register page becuase that is the most common page where validation errors are raised

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation Error: {exc}")
    flash(request, "The given input was not valid, pls check your input", FlashCategory.DANGER)
    referer = request.headers.get('referer')
    url = referer if referer and referer.startswith(str(request.base_url)) else "/register"
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER) # redirect to the previous page if a validation error is raised. or to the register page becuase that is the most common page where validation errors are raised

@app.exception_handler(FileTypeException)
async def unicorn_filetype_exception_handler(request: Request, exc: FileTypeException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": exc.message,
            "file_name": exc.file_name,
            "file_type": exc.file_type,
            "allowed_types": exc.allowed_types,
        },
    )

@app.exception_handler(FileNotFoundException)
async def unicorn_file_not_found_exception_handler(request: Request, exc: FileNotFoundException):
    return RedirectResponse(url="/upload", 
                            status_code=status.HTTP_303_SEE_OTHER,) # redirect to home page if 3xx is raised

@app.on_event("startup")
@repeat_every(seconds=60*60)  # check every hour for expired files
async def remove_expired_files_task():
    await remove_expired_files(connection=connection, path=config.UPLOAD_DIR)
    await refresh_team_file(file_path="team.json", expire_time=config.TEAM_EXPIRE_TIME)


@app.get("/error/{code}")
async def error_page(request: Request, code: int):
    http_status = http.HTTPStatus(code)
    return templates.TemplateResponse(
        name="error/error.html",
        context={"request": request, "error": code, "http_status": http_status},
        status_code=code,
    )

@app.get("/redirect/{code}")
async def redirect_with_error(request: Request, code: int):
    return RedirectResponse(url="/", status_code=code)