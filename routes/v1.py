from fastapi import FastAPI, Body, Header, File, Depends, HTTPException, APIRouter
from models.user import User
from models.author import Author
from models.book import Book
from starlette.status import HTTP_201_CREATED
from starlette.responses import Response
from utils.helper_functions import upload_image_to_server
from utils.db_functions import (db_insert_personel, db_check_personel,
                                db_get_author, db_get_book_with_isbn,
                                db_get_author_from_id, db_patch_author_name)
import utils.redis_object as re
import pickle


app_v1 = APIRouter()


# Use tags to arrange the endpoints as you like in the documentation
@app_v1.post("/user", status_code=HTTP_201_CREATED, tags=["User"])
async def post_user(user: User):
    await db_insert_personel(user)
    return {"result": "personel is created"}


# Bad practice to put password in url, so we put it in body
@app_v1.post("/login", tags=["User"])
async def get_user_validation(username: str = Body(...), password: str = Body(...)):
    # Ask Redis Cache if it has data
    redis_key = f"{username},{password}"
    result = await re.redis.get(redis_key)

    # Redis has the data
    if result:
        if result == "true":
            return {"is_valid (redis)": True}
        else:
            return {"is_valid (redis)": False}
    # Redis does not have the data
    else:
        result = await db_check_personel(username, password)

        # Add the data to Redis and convert bool to str since it can't take bool
        await re.redis.set(redis_key, str(result), expire=10)

        return {"is_valid (db)": False}


@app_v1.get("/book/{isbn}", response_model=Book, response_model_include={"name", "year"}, tags=["Book"])
async def get_book_with_isbn(isbn: str):
    result = await re.redis.get(isbn)

    if result:
        result_book = pickle.loads(result)
        return result_book
    else:
        book = await db_get_book_with_isbn(isbn)
        author = await db_get_author(book["author"])
        author_obj = Author(**author)
        book["author"] = author_obj
        result_book = Book(**book)

        await re.redis.set(isbn, pickle.dumps(result_book))  # Redis cannot store object so we need to convert to bits
        return result_book


@app_v1.get("/author/{id}/book", tags=["Book"])
async def get_author_books(id: int, order: str = "asc"):
    author = await db_get_author_from_id(id)
    if author is not None:
        books = author["books"]
        if order =="asc":
            books = sorted(books)
        else:
            books = sorted(books, reverse=True)

        return {"books": books}
    else:
        return {"result": "no author with corresponding id!"}


@app_v1.patch("/author/{id}/name")
async def patch_author_name(id: int, name: str = Body(..., embed=True)):
    await db_patch_author_name(id, name)
    return {"result": "name is updated."}


@app_v1.post("/user/author")
async def post_user_and_author(user: User, author: Author, bookstore_name: str = Body(..., embed=True)):
    return {"user": user, "author": author, "bookstore_name": bookstore_name}


# Since we can't store the image file in postgres, we'll need to store the image
# somewhere online (api.imgbb.com) that takes the api key and we'll store the url
# in the table. But in our case we'll just print the file size.
@app_v1.post("/user/photo")
async def upload_user_photo(response: Response, profile_photo: bytes = File(...)):
    upload_image_to_server(profile_photo)
    return {"file size": len(profile_photo)}
