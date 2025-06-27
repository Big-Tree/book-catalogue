from __future__ import annotations

import uuid
from typing import NewType

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Book Catalogue REST API", version="1.0.0")

AuthorId = NewType('AuthorId', str)
BookId = NewType('BookId', str)

author_db = {}
book_db = {}


class Author(BaseModel):
    name: str
    surname: str
    birthyear: int
    books: list[BookId]


class Book(BaseModel):
    title: str
    author_list: list[AuthorId]
    publisher: str
    edition: int
    published_date: str


class Item(BaseModel):
    id: str | None = None
    name: str
    description: str | None = None
    price: float


class ItemResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    price: float


@app.get("/author/")
async def authors_summary() -> int:
    return len(author_db)


@app.post("/author/")
async def add_author(author: Author) -> AuthorId:
    id = AuthorId(str(uuid.uuid4()))
    author_db[id] = author
    return id


@app.get("/book/")
async def books_summary() -> int:
    return len(book_db)


@app.post("/book/")
async def add_book(book: Book) -> BookId:
    book_id = BookId(str(uuid.uuid4()))

    for author_id in book.author_list:
        if author_id not in author_db:
            raise HTTPException(status_code=400, detail=f"Author with ID {author_id} not found")
        else:
            author_db[author_id].books.append(book_id)

    book_db[book_id] = book

    return book_id


@app.get("/author/{author_id}")
async def get_author(author_id: AuthorId) -> Author:
    if author_id not in author_db:
        raise HTTPException(status_code=400, detail=f"Author with ID {author_id} not found")

    return author_db[author_id]


@app.get("/book/{book_id}")
async def get_book(book_id: BookId) -> Book:
    if book_id not in book_db:
        raise HTTPException(status_code=400, detail=f"Book with ID {book_id} not found")

    return book_db[book_id]


@app.put("/author/{author_id}")
async def update_author(author_id: AuthorId, author: Author) -> AuthorId:
    if author_id not in author_db:
        raise HTTPException(status_code=400, detail=f"Author with ID {author_id} not found")

    author_db[author_id] = author
    return author_id


@app.put("/book/{book_id}")
async def update_book(book_id: BookId, book: Book) -> BookId:
    if book_id not in book_db:
        raise HTTPException(status_code=400, detail=f"Book with ID {book_id} not found")

    book_db[book_id] = book
    return book_id


@app.delete("/author/{author_id}")
async def delete_author(author_id: AuthorId) -> AuthorId:
    if author_id not in author_db:
        raise HTTPException(status_code=400, detail=f"Author with ID {author_id} not found")
    elif len(author_db[author_id].books) > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete author {author_id}: Author has {len(author_db[author_id].books)} books associated"
        )

    del author_db[author_id]
    return author_id


@app.delete("/book/{book_id}")
async def delete_book(book_id: BookId) -> BookId:
    if book_id not in book_db:
        raise HTTPException(status_code=400, detail=f"Book with ID {book_id} not found")

    # Remove book from all authors' book lists
    for author_id in book_db[book_id].author_list:
        if author_id in author_db:
            author_db[author_id].books.remove(book_id)

    del book_db[book_id]
    return book_id
