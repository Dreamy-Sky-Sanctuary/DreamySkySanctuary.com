from src.utils.image_utils import resize_and_crop_image
from src.utils.flash import get_flashed_messages, flash, FlashCategory
from src.schemas.Image import ImageGalleryLink, GalleryData, ImageData
from src.utils.database import add_gallery_to_db, add_image_gallery_link_to_db, add_image_to_db, close_connection, create_connection, get_gallery_by_user_from_db, get_gallery_from_db, get_image_from_db, get_image_gallery_links_from_db, get_images_by_user_from_db, remove_gallery_from_db, remove_gallery_links_from_db, remove_image_from_db, remove_image_links_from_db
from src.dependencies import *
import hashlib
import shutil
from src.schemas.errors.FileNotFoundException import FileNotFoundException
from src.schemas.errors.FileTypeException import FileTypeException
from fastapi import Form, status
import time
import datetime


router = APIRouter(
    prefix="",
    tags=["Upload"],
)

templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
templates.env.globals["get_flashed_messages"] = get_flashed_messages

@router.get("/upload", include_in_schema=True)
async def main(request: Request, response: Response):
    user = request.state.user
    string_types = ""
    for type in config.ALLOWED_FILE_TYPES:
        string_types += f"{type}, "
    return templates.TemplateResponse(name="main/upload.html", context={"request": request, "user": user, "allowed_types": string_types, "base_url": "https://" +str(request.base_url)[:-1].strip("http://")})


@router.post("/upload", include_in_schema=True)
async def upload_file(request: Request, uploaded_images: List[UploadFile] = File(...), expire: int = Form(0), imgsize: int = Form("original"), width: int = Form(-1), height: int = Form(-1)):
    user = request.state.user
    sizes = {
        0: [-1, -1],
        1: [934, 282],
        2: [512, 512],
        3: [960, 540],
        4: [1920, 1080],
        5: [3840, 2160],
        6: [-1, -1]
    }
    if imgsize not in sizes:
        raise ValueError(f"Invalid image size: {imgsize}")
    if imgsize != 6:
        width = sizes[imgsize][0]
        height = sizes[imgsize][1]
    if width < -1 or height < -1:
        raise ValueError(f"Invalid width or height: {width} x {height}, must be greater than 0.")
    
    saved_files: list[ImageData] = []
    for image in uploaded_images:
        if image.content_type not in config.ALLOWED_FILE_TYPES:
            raise FileTypeException(image.filename, image.content_type, config.ALLOWED_FILE_TYPES)
        
        auth_hash = hashlib.md5(f"{time.time_ns()}-{image.size}-{image.filename}".encode("utf-8"))
        hash = hashlib.sha512(f"{image.filename}-{image.size}-{time.time_ns()}".encode("utf-8"))
        
        filename = f"{hash.hexdigest()}.{config.ALLOWED_FILE_TYPES[image.content_type]}"
        filename = filename[-15:]
        save_path = os.path.join(config.UPLOAD_DIR, filename)
        
        with open(save_path, "wb+") as f:
            shutil.copyfileobj(image.file, f)
        
        if width > 0 and height > 0:
            resize_and_crop_image(save_path, height, width)
        
        image_data = ImageData(
            filename=filename,
            path=save_path,
            url=f"/images/{filename}",
            auth_code=auth_hash.hexdigest()[-15:],
            filesize=os.path.getsize(save_path),
            uploaded_by=user.username if user else None,
            delete_after=datetime.datetime.now() + datetime.timedelta(days=expire) if expire > 0 else None,
        )
        
        saved_files.append(image_data)
    if len(saved_files) == 1:
        connection = create_connection("Website")
        image = saved_files[0]
        
        add_image_to_db(connection, image)
        close_connection(connection)
        
        return RedirectResponse(f"/image/{image.filename}/{image.auth_code}", status_code=status.HTTP_303_SEE_OTHER)
    
    if len(saved_files) > 1:
        hashstring = ""
        for image in saved_files:
            hashstring += image.filename
        
        auth_hash = hashlib.md5(f"{time.time_ns()}-{hashstring}".encode("utf-8"))
        gallery_hash = hashlib.sha512(f"{hashstring}-{time.time_ns()}".encode("utf-8"))

        gallery_data = GalleryData(
            gallery_code=gallery_hash.hexdigest()[-15:],
            auth_code=gallery_hash.hexdigest()[-15:],
            uploaded_by=user.username if user else None,
            delete_after=datetime.datetime.now() + datetime.timedelta(days=expire) if expire > 0 else None,
        )
        
        connection = create_connection("Website")
        
        add_gallery_to_db(connection, gallery_data)
        
        for image in saved_files:
            add_image_to_db(connection, image)
            add_image_gallery_link_to_db(connection, ImageGalleryLink(
                gallery_code=gallery_data.gallery_code, 
                filename=image.filename
                )
            )
        
        return RedirectResponse(f"/gallery/{gallery_data.gallery_code}/{gallery_data.auth_code}", status_code=status.HTTP_303_SEE_OTHER)
    
    return RedirectResponse("/upload", status_code=status.HTTP_400_BAD_REQUEST)


@router.get('/gallery')
async def gallery(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    connection = create_connection("Website")
    
    galleries = get_gallery_by_user_from_db(connection, user)
    gallery_list = []
    if galleries:
        for gallery in galleries:
            links = get_image_gallery_links_from_db(connection, gallery.gallery_code)
            if not links:
                remove_gallery_from_db(connection, gallery.gallery_code)
                close_connection(connection)
                continue # If the gallery has no images, remove it from the database and continue to the next gallery
                # raise FileNotFoundException(file_name=gallery.gallery_code, message="Gallery not found.")
            gallery_list.append(gallery)
            preview_image = get_image_from_db(connection, links[0].filename)
            gallery.preview_image = preview_image.url
        
    # if not galleries:
    #     close_connection(connection)
    #     raise FileNotFoundException(file_name=user.username, message="No gallerys found.")

    close_connection(connection)
    return templates.TemplateResponse(
        name="main/galleries.html",
        context={"request": request, "user": user, "galleries": gallery_list, "base_url": "https://" +str(request.base_url)[:-1].strip("http://")}
    )


@router.get('/gallery/{gallery_code}')
async def gallery(request: Request, gallery_code: str):
    user = request.state.user
    connection = create_connection("Website")
    
    gallery_data = get_gallery_from_db(connection, gallery_code)
    
    if not gallery_data:
        close_connection(connection)
        raise FileNotFoundException(file_name=gallery_code, message="Gallery not found.")
    
    links = get_image_gallery_links_from_db(connection, gallery_code)
    if not links:
        remove_gallery_from_db(connection, gallery_code)
        close_connection(connection)
        raise FileNotFoundException(file_name=gallery_code, message="Gallery not found.")
    
    images = []
    
    for link in links:
        image = get_image_from_db(connection, link.filename)
        images.append(image)

    close_connection(connection)
    return templates.TemplateResponse(
        name="main/gallery.html",
        context={"request": request, "user": user, "images": images, "base_url": "https://" +str(request.base_url)[:-1].strip("http://")}
    )


@router.get('/gallery/{gallery_code}/{auth_code}')
async def gallery(request: Request, gallery_code: str, auth_code: str):
    user = request.state.user
    connection = create_connection("Website")
    
    gallery_data = get_gallery_from_db(connection, gallery_code)
    
    if not gallery_data:
        close_connection(connection)
        raise FileNotFoundException(file_name=gallery_code, message="Gallery not found.")
    
    if auth_code != gallery_data.auth_code:
        return RedirectResponse(f"/gallery/{gallery_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    
    links = get_image_gallery_links_from_db(connection, gallery_code)
    if not links:
        remove_gallery_from_db(connection, gallery_code)
        close_connection(connection)
        raise FileNotFoundException(file_name=gallery_code, message="Gallery not found.")
    
    images = []
    
    for link in links:
        image = get_image_from_db(connection, link.filename)
        images.append(image)

    close_connection(connection)
    return templates.TemplateResponse(
        name="main/gallery.html",
        context={"request": request, "user": user, "images": images, "gallery_code": gallery_code, "auth_code": auth_code, "base_url": "https://" +str(request.base_url)[:-1].strip("http://")}
    )


@router.get('/image')
async def image(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    connection = create_connection("Website")
    
    images = get_images_by_user_from_db(connection, user)
    
    close_connection(connection)
    return templates.TemplateResponse(
        name="main/images.html",
        context={"request": request, "user": user, "images": images, "base_url": "https://" +str(request.base_url)[:-1].strip("http://")}
    )


@router.get('/image/{file_name}')
async def image(request: Request, file_name: str):
    user = request.state.user
    connection = create_connection("Website")
    
    image = get_image_from_db(connection, file_name)

    if not image:
        close_connection(connection)
        raise FileNotFoundException(file_name=file_name, message="Image not found.")
    
    close_connection(connection)
    return templates.TemplateResponse(
        name="main/image.html",
        context={"request": request, "user": user, "image": image, "base_url": "https://" +str(request.base_url)[:-1].strip("http://")}
    )


@router.get('/image/{file_name}/{auth_code}')
async def manage_image(request: Request, file_name: str, auth_code: str):
    user = request.state.user
    connection = create_connection("Website")
    
    image = get_image_from_db(connection, file_name)

    if not image:
        close_connection(connection)
        raise FileNotFoundException(file_name=file_name, message="Image not found.")
    
    if auth_code != image.auth_code:
        close_connection(connection)
        return RedirectResponse(f"/image/{file_name}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    
    close_connection(connection)
    return templates.TemplateResponse(
        name="main/image.html",
        context={"request": request, "user": user, "image": image, "auth_code": auth_code, "base_url": "https://" +str(request.base_url)[:-1].strip("http://")}
    )


@router.post('/image/remove/{file_name}/{auth_code}')
async def remove_image(request: Request, file_name: str, auth_code: str):
    connection = create_connection("Website")
    
    image = get_image_from_db(connection, file_name)

    if not image:
        close_connection(connection)
        return JSONResponse(
            content={
                "success": False,
                "detail": "Image not found.",
                "category": FlashCategory.WARNING.value,
                }, 
            status_code=status.HTTP_404_NOT_FOUND
            )
    
    if auth_code != image.auth_code:
        close_connection(connection)
        return JSONResponse(
            content={
                "success": False,
                "detail": "Invalid auth code.",
                "category": FlashCategory.WARNING.value,
                },
            status_code=status.HTTP_403_FORBIDDEN
            )
    
    if os.path.exists(image.path):
        os.remove(image.path)
    
    remove_image_from_db(connection, file_name)
    remove_image_links_from_db(connection, file_name)
    
    close_connection(connection)
    return JSONResponse(
        content={
            "success": True,
            "detail": "Image removed.",
            "category": FlashCategory.SUCCESS.value,
            },
        status_code=status.HTTP_200_OK
        )


@router.post('/gallery/remove/{gallery_code}/{auth_code}')
async def remove_gallery(request: Request, gallery_code: str, auth_code: str):
    connection = create_connection("Website")
    
    gallery_data = get_gallery_from_db(connection, gallery_code)
    
    if not gallery_data:
        close_connection(connection)
        return JSONResponse(
            content={
                "success": False,
                "detail": "Gallery not found.",
                "category": FlashCategory.WARNING.value,
                }, 
            status_code=status.HTTP_404_NOT_FOUND
            )
    
    if auth_code != gallery_data.auth_code:
        close_connection(connection)
        return JSONResponse(
            content={
                "success": False,
                "detail": "Invalid auth code.",
                "category": FlashCategory.WARNING.value,
                },
            status_code=status.HTTP_403_FORBIDDEN
            )
    
    links = get_image_gallery_links_from_db(connection, gallery_code)
    if not links:
        remove_gallery_from_db(connection, gallery_code)
        close_connection(connection)
        return JSONResponse(
            content={
                "success": False,
                "detail": "Gallery not found.",
                "category": FlashCategory.WARNING.value,
                }, 
            status_code=status.HTTP_404_NOT_FOUND
            )
    
    remove_gallery_from_db(connection, gallery_code)
    remove_gallery_links_from_db(connection, gallery_code)
    
    for link in links:
        remove_image_from_db(connection, link.filename)
    
    close_connection(connection)
    return JSONResponse(
        content={
            "success": True,
            "detail": "Gallery removed.",
            "category": FlashCategory.SUCCESS.value,
            },
        status_code=status.HTTP_200_OK
        )


@router.get('/download/{file_name}')
async def download(request: Request, file_name: str):
    connection = create_connection("Website")
    
    image = get_image_from_db(connection, file_name)
    
    if not image:
        close_connection(connection)
        raise FileNotFoundException(file_name=file_name, message="Image not found.")

    if not os.path.exists(image.path):
        raise FileNotFoundException(file_name=file_name, file_path=image.path)
    return FileResponse(path=image.path, filename=file_name)