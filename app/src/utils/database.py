# python imports
from collections.abc import Sequence
from typing import Any, Dict
from dotenv import load_dotenv
import os

# 3rd party imports
import mysql.connector
from mysql.connector import Error
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

# local imports
from src.schemas.Login import User, UserDB
from src.schemas.Image import ImageGalleryLink, GalleryData, ImageData
from src.logger import logger

load_dotenv()
DATABASE_ENDPOINT: str = os.getenv("DATABASE_ENDPOINT", "localhost")  # Default to localhost if not set
DATABASE_USER: str = os.getenv("DATABASE_USERNAME", "root") # Default to 'root' if not set
DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "root") # Default to 'root' if not set
DATABASE_PORT: str = os.getenv("DATABASE_PORT", "3306")  # Default MySQL port is 3306


# Function to create MySQL database connection
def create_connection(database_name: str) -> PooledMySQLConnection | MySQLConnectionAbstract:
    # logger.debug(f"Connecting to the database: {database_name}")
    connection: PooledMySQLConnection | MySQLConnectionAbstract | None = None
    try:
        connection = mysql.connector.connect(
            host=DATABASE_ENDPOINT,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=database_name,
            port=DATABASE_PORT
        )
        if not connection.is_connected():
            logger.error("Failed to connect to the database.", extra={
                "host": DATABASE_ENDPOINT,
                "user": DATABASE_USER,
                "database": database_name,
                "port": DATABASE_PORT
            })
    except Error as e:
        logger.error(f"The error '{e}' occurred")
    return connection # type: ignore


# Close MySQL connection
def close_connection(connection: PooledMySQLConnection | MySQLConnectionAbstract) -> None:
    if connection.is_connected():
        # logger.debug("Closing the database connection.")
        connection.close()
    if connection.is_connected():
        logger.error("Failed to close the database connection.")
    # else:
        # logger.debug("Database connection closed.")


# Insert query function
def insert_query(connection: PooledMySQLConnection | MySQLConnectionAbstract, query, values):
    # logger.debug(f"Inserting data into the database: {values}") # Commented out to reduce log verbosity
    cursor = connection.cursor()
    try:
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        logger.error(f"The error '{e}' occurred")


# Select query function
def select_query(connection: PooledMySQLConnection | MySQLConnectionAbstract, query, values: Any = None):
    # logger.debug(f"Selecting data from the database: {query}") # Commented out to reduce log verbosity
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, values)
        result = cursor.fetchall()
        return result
    except Error as e:
        logger.error(f"The error '{e}' occurred")


# Update query function
def update_query(connection: PooledMySQLConnection | MySQLConnectionAbstract, query, values):
    # logger.debug(f"Updating data in the database: {values}") # Commented out to reduce log verbosity
    cursor = connection.cursor()
    try:
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        logger.error(f"The error '{e}' occurred")


# Delete query function
def delete_query(connection: PooledMySQLConnection | MySQLConnectionAbstract, query, values):
    # logger.debug(f"Deleting data from the database: {values}") # Commented out to reduce log verbosity
    cursor = connection.cursor()
    try:
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        logger.error(f"The error '{e}' occurred")


def add_image_to_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, image: ImageData) -> None:
    logger.debug(f"Adding image: `{image.filename}` to the database.")
    query = "INSERT INTO images (filename, auth_code, path, url, filesize, uploaded_by, delete_after) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = (image.filename, image.auth_code, image.path, image.url, image.filesize, image.uploaded_by, image.delete_after.strftime('%Y-%m-%d %H:%M:%S') if image.delete_after else None)
    insert_query(connection, query, values)


def get_image_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, filename: str) -> ImageData | None:
    # logger.debug(f"Getting image: `{filename}` from the database.")
    query = "SELECT * FROM images WHERE filename = %s"
    values = (filename,)
    result = select_query(connection, query, values)
    if result:
        return ImageData(**result[0]) # type: ignore
    return None


def get_images_by_user_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, user: UserDB) -> list[ImageData] | None:
    logger.debug(f"Getting images of user: `{user.username}` from the database.")
    query = "SELECT * FROM images WHERE uploaded_by = %s"
    values = (user.username,)
    result = select_query(connection, query, values)
    if result:
        return [ImageData(**image) for image in result] # type: ignore
    return None


def remove_image_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, filename: str) -> None:
    logger.debug(f"Removing image: `{filename}` from the database.")
    query = "DELETE FROM images WHERE filename = %s"
    values = (filename,)
    delete_query(connection, query, values)


def add_gallery_to_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, gallery: GalleryData) -> None:
    logger.debug(f"Adding gallery: `{gallery.gallery_code}` to the database.")
    query = "INSERT INTO galleries (gallery_code, auth_code, uploaded_by, delete_after) VALUES (%s, %s, %s, %s)"
    values = (gallery.gallery_code, gallery.auth_code, gallery.uploaded_by, gallery.delete_after.strftime('%Y-%m-%d %H:%M:%S') if gallery.delete_after else None)
    insert_query(connection, query, values)


def get_gallery_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, gallery_code: str) -> GalleryData | None:
    # logger.debug(f"Getting gallery: `{gallery_code}` from the database.")
    query = "SELECT * FROM galleries WHERE gallery_code = %s"
    values = (gallery_code,)
    result = select_query(connection, query, values)
    if result:
        return GalleryData(**result[0]) # type: ignore
    return None


def get_gallery_by_user_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, user: UserDB) -> list[GalleryData] | None:
    logger.debug(f"Getting galleries of user: `{user.username}` from the database.")
    query = "SELECT * FROM galleries WHERE uploaded_by = %s"
    values = (user.username,)
    result = select_query(connection, query, values)
    if result:
        return [GalleryData(**gallery) for gallery in result] # type: ignore
    return None


def remove_gallery_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, gallery_code: str) -> None:
    logger.debug(f"Removing gallery: `{gallery_code}` from the database.")
    query = "DELETE FROM galleries WHERE gallery_code = %s"
    values = (gallery_code,)
    delete_query(connection, query, values)


def add_image_gallery_link_to_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, link: ImageGalleryLink) -> None:
    logger.debug(f"Adding link: `{link.gallery_code}`, `{link.filename}` to the database.")
    query = "INSERT INTO links (gallery_code, filename) VALUES (%s, %s)"
    values = (link.gallery_code, link.filename)
    insert_query(connection, query, values)


def get_image_gallery_links_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, gallery_code: str) -> list[ImageGalleryLink] | None:
    # logger.debug(f"Getting links: `{gallery_code}` from the database.")
    query = "SELECT * FROM links WHERE gallery_code = %s"
    values = (gallery_code,)
    result = select_query(connection, query, values)
    if result:
        return [ImageGalleryLink(**link) for link in result] # type: ignore
    return None


def remove_gallery_links_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, gallery_code: str) -> None:
    logger.debug(f"Removing gallery-`{gallery_code}`'s links from the database.")
    query = "DELETE FROM links WHERE gallery_code = %s"
    values = (gallery_code,)
    delete_query(connection, query, values)


def remove_image_links_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, filename: str) -> None:
    logger.debug(f"Removing image-`{filename}`'s links from the database.")
    query = "DELETE FROM links WHERE filename = %s"
    values = (filename,)
    delete_query(connection, query, values)


def get_images_of_gallery_from_db(connection: PooledMySQLConnection | MySQLConnectionAbstract, gallery_code: str) -> list[ImageData]:
    # logger.debug(f"Getting images of gallery: `{gallery_code}` from the database.")
    links = get_image_gallery_links_from_db(connection, gallery_code)
    images = []
    if not links:
        logger.debug(f"No images found for gallery: `{gallery_code}`.")
        return images
    for link in links:
        image = get_image_from_db(connection, link.filename)
        images.append(image)
    return images


def get_user_id_by_username(connection: PooledMySQLConnection | MySQLConnectionAbstract, username: str) -> int | None:
    # logger.debug(f"Getting user: `{username}` from the database.")
    query = "SELECT id FROM users WHERE username = %s"
    values = (username,)
    result = select_query(connection, query, values)
    if result:
        return result[0]["id"] # type: ignore
    return None


def get_user_id(connection: PooledMySQLConnection | MySQLConnectionAbstract, user: UserDB) -> int | None:
    # logger.debug(f"Getting user: `{username}` from the database.")
    query = "SELECT id FROM users WHERE username = %s"
    values = (user.username,)
    result = select_query(connection, query, values)
    if result:
        return result[0]["id"] # type: ignore
    return None


def get_user_by_id(connection: PooledMySQLConnection | MySQLConnectionAbstract, user_id: int) -> UserDB | None:
    # logger.debug(f"Getting user: `{user_id}` from the database.")
    query = "SELECT * FROM users WHERE id = %s"
    values = (user_id,)
    result = select_query(connection, query, values)
    if result:
        return UserDB(**result[0]) # type: ignore
    return None


def get_user_by_username(connection: PooledMySQLConnection | MySQLConnectionAbstract, username: str) -> UserDB | None:
    # logger.debug(f"Getting user: `{username}` from the database.")
    query = "SELECT * FROM users WHERE username = %s"
    values = (username,)
    result = select_query(connection, query, values)
    if result:
        return UserDB(**result[0]) # type: ignore
    return None 


def get_user_by_email(connection: PooledMySQLConnection | MySQLConnectionAbstract, email: str) -> UserDB | None:
    # logger.debug(f"Getting user: `{username}` from the database.")
    query = "SELECT * FROM users WHERE email = %s"
    values = (email,)
    result = select_query(connection, query, values)
    if result:
        return UserDB(**result[0]) # type: ignore
    return None


def create_user(connection: PooledMySQLConnection | MySQLConnectionAbstract, user: UserDB) -> None:
    logger.debug(f"Creating user: `{user.username}` in the database.")
    query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
    values = (user.username, user.email, user.password_hash)
    insert_query(connection, query, values)


def update_user_details(connection: PooledMySQLConnection | MySQLConnectionAbstract, user: UserDB) -> None:
    logger.debug(f"Updating user: `{user.username}` in the database.")
    query = "UPDATE users SET email = %s, is_disabled = %s, is_admin = %s, password_hash = %s WHERE username = %s"
    values = (user.email, user.is_disabled, user.is_admin, user.password_hash, user.username)
    update_query(connection, query, values)


def update_user_name(connection: PooledMySQLConnection | MySQLConnectionAbstract, user: UserDB, username: str) -> None:
    logger.debug(f"Updating username from `{user.username}` to `{username}` in the database.")
    query = "UPDATE users SET username = %s WHERE id = %s"
    values = (username, get_user_id(connection, user))
    update_query(connection, query, values)


def update_otp_user(connection: PooledMySQLConnection | MySQLConnectionAbstract, user: UserDB) -> None:
    logger.debug(f"Updating user: `{user.username}` in the database.")
    query = "UPDATE users SET otp_base32 = %s, otp_auth_url = %s, otp_enabled = %s, otp_verified = %s WHERE username = %s"
    values = (user.otp_base32, user.otp_auth_url, user.otp_enabled, user.otp_verified, user.username)
    update_query(connection, query, values)


def get_save_user(user: UserDB) -> User:
    return User(username=user.username, email=user.email, is_disabled=user.is_disabled, is_admin=user.is_admin,
                otp_enabled=user.otp_enabled, otp_verified=user.otp_verified)


def save_forgot_password_token(connection: PooledMySQLConnection | MySQLConnectionAbstract, user: UserDB, token: str) -> None:
    logger.debug(f"Saving forgot password token for: `{user.email}` in the database.")
    temp_token = get_forgot_password_token_from_username(connection, user.username)
    if temp_token:
        remove_forgot_password_token(connection, temp_token)
    query = "INSERT INTO forgot_password (username, email, token) VALUES (%s, %s, %s)"
    values = (user.username, user.email, token)
    insert_query(connection, query, values)


def get_forgot_password_token_from_username(connection: PooledMySQLConnection | MySQLConnectionAbstract, username: str) -> str | None:
    logger.debug(f"Getting forgot password account: `{username}` from the database.")
    query = "SELECT * FROM forgot_password WHERE username = %s"
    values = (username,)
    result = select_query(connection, query, values)
    if result:
        return result[0]["token"] # type: ignore
    return None


def get_forgot_password_account_from_token(connection: PooledMySQLConnection | MySQLConnectionAbstract, token: str) -> UserDB | None:
    logger.debug(f"Getting forgot password token: `{token}` from the database.")
    query = "SELECT * FROM forgot_password WHERE token = %s"
    values = (token,)
    result = select_query(connection, query, values)
    if result:
        user = get_user_by_username(connection, result[0]["username"]) # type: ignore
        return user
    return None


def remove_forgot_password_token(connection: PooledMySQLConnection | MySQLConnectionAbstract, token: str) -> None:
    logger.debug(f"Removing forgot password token: `{token}` from the database.")
    query = "DELETE FROM forgot_password WHERE token = %s"
    values = (token,)
    delete_query(connection, query, values)