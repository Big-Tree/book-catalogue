from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app, author_db, book_db


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Clear the databases before each test"""
    author_db.clear()
    book_db.clear()


class TestAuthorEndpoints:
    def test_get_authors_summary_empty(self, client: TestClient):
        """Test GET /author/ with empty database"""
        response = client.get("/author/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_author(self, client: TestClient):
        """Test POST /author/"""
        author_data = {
            "name": "John",
            "surname": "Doe",
            "birthyear": 1970,
            "book_ids": []
        }
        response = client.post("/author/", json=author_data)
        assert response.status_code == 200
        author_id = response.json()
        assert isinstance(author_id, str)
        assert len(author_id) > 0

    def test_get_authors_summary_with_data(self, client: TestClient):
        """Test GET /author/ after creating authors"""
        author_data = {
            "name": "Jane",
            "surname": "Smith",
            "birthyear": 1985,
            "book_ids": []
        }
        client.post("/author/", json=author_data)
        client.post("/author/", json=author_data)

        response = client.get("/author/")
        assert response.status_code == 200
        authors = response.json()
        assert len(authors) == 2
        assert all(author["name"] == "Jane" for author in authors)
        assert all(author["surname"] == "Smith" for author in authors)

    def test_get_author_by_id(self, client: TestClient):
        """Test GET /author/{author_id}"""
        author_data = {
            "name": "Alice",
            "surname": "Johnson",
            "birthyear": 1990,
            "book_ids": []
        }
        create_response = client.post("/author/", json=author_data)
        author_id = create_response.json()

        response = client.get(f"/author/{author_id}")
        assert response.status_code == 200
        returned_author = response.json()
        assert returned_author["name"] == "Alice"
        assert returned_author["surname"] == "Johnson"
        assert returned_author["birthyear"] == 1990
        assert returned_author["book_ids"] == []

    def test_get_author_not_found(self, client: TestClient):
        """Test GET /author/{author_id} with non-existent ID"""
        response = client.get("/author/nonexistent-id")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_update_author(self, client: TestClient):
        """Test PUT /author/{author_id}"""
        original_data = {
            "name": "Bob",
            "surname": "Wilson",
            "birthyear": 1975,
            "book_ids": []
        }
        create_response = client.post("/author/", json=original_data)
        author_id = create_response.json()

        updated_data = {
            "name": "Robert",
            "surname": "Wilson",
            "birthyear": 1976,
            "book_ids": []
        }
        response = client.put(f"/author/{author_id}", json=updated_data)
        assert response.status_code == 200

        # Verify the update
        get_response = client.get(f"/author/{author_id}")
        updated_author = get_response.json()
        assert updated_author["name"] == "Robert"
        assert updated_author["birthyear"] == 1976

    def test_update_author_not_found(self, client: TestClient):
        """Test PUT /author/{author_id} with non-existent ID"""
        author_data = {
            "name": "Test",
            "surname": "User",
            "birthyear": 2000,
            "book_ids": []
        }
        response = client.put("/author/nonexistent-id", json=author_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_delete_author(self, client: TestClient):
        """Test DELETE /author/{author_id}"""
        author_data = {
            "name": "Charlie",
            "surname": "Brown",
            "birthyear": 1980,
            "book_ids": []
        }
        create_response = client.post("/author/", json=author_data)
        author_id = create_response.json()

        response = client.delete(f"/author/{author_id}")
        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(f"/author/{author_id}")
        assert get_response.status_code == 400

    def test_delete_author_not_found(self, client: TestClient):
        """Test DELETE /author/{author_id} with non-existent ID"""
        response = client.delete("/author/nonexistent-id")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_delete_author_with_books_conflict(self, client: TestClient):
        """Test DELETE /author/{author_id} when author has books"""
        # Create author
        author_data = {
            "name": "Diana",
            "surname": "Prince",
            "birthyear": 1985,
            "book_ids": []
        }
        author_response = client.post("/author/", json=author_data)
        author_id = author_response.json()

        # Create book with this author
        book_data = {
            "title": "Test Book",
            "author_ids": [author_id],
            "publisher": "Test Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        client.post("/book/", json=book_data)

        # Try to delete author
        response = client.delete(f"/author/{author_id}")
        assert response.status_code == 409
        assert "Cannot delete author" in response.json()["detail"]

    def test_create_author_with_nonexistent_book(self, client: TestClient):
        """Test POST /author/ with non-existent book ID in books field"""
        author_data = {
            "name": "Test",
            "surname": "Author",
            "birthyear": 1980,
            "book_ids": ["nonexistent-book-id"]
        }
        response = client.post("/author/", json=author_data)
        assert response.status_code == 409
        assert "Book with ID nonexistent-book-id not found" in response.json()["detail"]

    def test_create_author_with_existing_books_bidirectional_consistency(self, client: TestClient):
        """Test POST /author/ with existing book_ids - verify bidirectional consistency"""
        # Create multiple books first (without authors)
        book1_data = {
            "title": "Book One",
            "author_ids": [],
            "publisher": "Publisher One",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        book2_data = {
            "title": "Book Two", 
            "author_ids": [],
            "publisher": "Publisher Two",
            "edition": 1,
            "published_date": "2023-02-01"
        }
        book3_data = {
            "title": "Book Three",
            "author_ids": [],
            "publisher": "Publisher Three",
            "edition": 1,
            "published_date": "2023-03-01"
        }
        
        book1_response = client.post("/book/", json=book1_data)
        book2_response = client.post("/book/", json=book2_data)
        book3_response = client.post("/book/", json=book3_data)
        
        book1_id = book1_response.json()
        book2_id = book2_response.json()
        book3_id = book3_response.json()

        # Create author with all three books
        author_data = {
            "name": "Multi",
            "surname": "BookAuthor",
            "birthyear": 1985,
            "book_ids": [book1_id, book2_id, book3_id]
        }
        author_response = client.post("/author/", json=author_data)
        assert author_response.status_code == 200
        author_id = author_response.json()

        # Verify the author was created with all books
        author_get = client.get(f"/author/{author_id}")
        author_info = author_get.json()
        assert len(author_info["book_ids"]) == 3
        assert book1_id in author_info["book_ids"]
        assert book2_id in author_info["book_ids"]  
        assert book3_id in author_info["book_ids"]

        # Verify bidirectional consistency - each book should have the author in their author_ids
        # NOTE: This test will reveal if the current implementation has a bug!
        # The current POST /author/ endpoint doesn't update books' author_ids when creating an author with book_ids
        book1_get = client.get(f"/book/{book1_id}")
        book2_get = client.get(f"/book/{book2_id}")
        book3_get = client.get(f"/book/{book3_id}")
        
        book1_info = book1_get.json()
        book2_info = book2_get.json()
        book3_info = book3_get.json()
        
        # These assertions will likely FAIL with current implementation - revealing the bug!
        assert author_id in book1_info["author_ids"], f"Author {author_id} not found in book1 author_ids: {book1_info['author_ids']}"
        assert author_id in book2_info["author_ids"], f"Author {author_id} not found in book2 author_ids: {book2_info['author_ids']}"
        assert author_id in book3_info["author_ids"], f"Author {author_id} not found in book3 author_ids: {book3_info['author_ids']}"


class TestBookEndpoints:
    def test_get_books_summary_empty(self, client: TestClient):
        """Test GET /book/ with empty database"""
        response = client.get("/book/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_book_without_authors(self, client: TestClient):
        """Test POST /book/ with empty author list"""
        book_data = {
            "title": "Solo Book",
            "author_ids": [],
            "publisher": "Solo Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        assert response.status_code == 200
        book_id = response.json()
        assert isinstance(book_id, str)
        assert len(book_id) > 0

    def test_create_book_with_authors(self, client: TestClient):
        """Test POST /book/ with valid authors"""
        # Create authors first
        author_data = {
            "name": "Author",
            "surname": "One",
            "birthyear": 1970,
            "book_ids": []
        }
        author_response = client.post("/author/", json=author_data)
        author_id = author_response.json()

        book_data = {
            "title": "Collaborative Book",
            "author_ids": [author_id],
            "publisher": "Collab Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        assert response.status_code == 200
        book_id = response.json()
        assert isinstance(book_id, str)

    def test_create_book_with_invalid_author(self, client: TestClient):
        """Test POST /book/ with non-existent author"""
        book_data = {
            "title": "Invalid Book",
            "author_ids": ["nonexistent-author-id"],
            "publisher": "Test Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_get_books_summary_with_data(self, client: TestClient):
        """Test GET /book/ after creating books"""
        book_data = {
            "title": "Test Book",
            "author_ids": [],
            "publisher": "Test Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        client.post("/book/", json=book_data)
        client.post("/book/", json=book_data)

        response = client.get("/book/")
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 2
        assert all(book["title"] == "Test Book" for book in books)

    def test_get_book_by_id(self, client: TestClient):
        """Test GET /book/{book_id}"""
        book_data = {
            "title": "Specific Book",
            "author_ids": [],
            "publisher": "Specific Publisher",
            "edition": 2,
            "published_date": "2023-06-01"
        }
        create_response = client.post("/book/", json=book_data)
        book_id = create_response.json()

        response = client.get(f"/book/{book_id}")
        assert response.status_code == 200
        returned_book = response.json()
        assert returned_book["title"] == "Specific Book"
        assert returned_book["publisher"] == "Specific Publisher"
        assert returned_book["edition"] == 2
        assert returned_book["published_date"] == "2023-06-01"
        assert returned_book["author_ids"] == []

    def test_get_book_not_found(self, client: TestClient):
        """Test GET /book/{book_id} with non-existent ID"""
        response = client.get("/book/nonexistent-id")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_update_book(self, client: TestClient):
        """Test PUT /book/{book_id}"""
        original_data = {
            "title": "Original Title",
            "author_ids": [],
            "publisher": "Original Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        create_response = client.post("/book/", json=original_data)
        book_id = create_response.json()

        updated_data = {
            "title": "Updated Title",
            "author_ids": [],
            "publisher": "Updated Publisher",
            "edition": 2,
            "published_date": "2023-12-01"
        }
        response = client.put(f"/book/{book_id}", json=updated_data)
        assert response.status_code == 200

        # Verify the update
        get_response = client.get(f"/book/{book_id}")
        updated_book = get_response.json()
        assert updated_book["title"] == "Updated Title"
        assert updated_book["publisher"] == "Updated Publisher"
        assert updated_book["edition"] == 2

    def test_update_book_not_found(self, client: TestClient):
        """Test PUT /book/{book_id} with non-existent ID"""
        book_data = {
            "title": "Test Book",
            "author_ids": [],
            "publisher": "Test Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.put("/book/nonexistent-id", json=book_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_delete_book(self, client: TestClient):
        """Test DELETE /book/{book_id}"""
        book_data = {
            "title": "Book to Delete",
            "author_ids": [],
            "publisher": "Delete Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        create_response = client.post("/book/", json=book_data)
        book_id = create_response.json()

        response = client.delete(f"/book/{book_id}")
        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(f"/book/{book_id}")
        assert get_response.status_code == 400

    def test_delete_book_not_found(self, client: TestClient):
        """Test DELETE /book/{book_id} with non-existent ID"""
        response = client.delete("/book/nonexistent-id")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_create_book_with_multiple_authors_bidirectional_consistency(self, client: TestClient):
        """Test POST /book/ with multiple authors - verify bidirectional reference consistency"""
        # Create multiple authors first
        author1_data = {
            "name": "Author",
            "surname": "One",
            "birthyear": 1970,
            "book_ids": []
        }
        author2_data = {
            "name": "Author",
            "surname": "Two", 
            "birthyear": 1980,
            "book_ids": []
        }
        author3_data = {
            "name": "Author",
            "surname": "Three",
            "birthyear": 1990,
            "book_ids": []
        }
        
        author1_response = client.post("/author/", json=author1_data)
        author2_response = client.post("/author/", json=author2_data)
        author3_response = client.post("/author/", json=author3_data)
        
        author1_id = author1_response.json()
        author2_id = author2_response.json()
        author3_id = author3_response.json()

        # Create book with all three authors
        book_data = {
            "title": "Multi-Author Book",
            "author_ids": [author1_id, author2_id, author3_id],
            "publisher": "Multi Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        book_response = client.post("/book/", json=book_data)
        assert book_response.status_code == 200
        book_id = book_response.json()

        # Verify bidirectional consistency - each author should have the book in their book_ids
        author1_get = client.get(f"/author/{author1_id}")
        author2_get = client.get(f"/author/{author2_id}")
        author3_get = client.get(f"/author/{author3_id}")
        
        author1_info = author1_get.json()
        author2_info = author2_get.json()
        author3_info = author3_get.json()
        
        assert book_id in author1_info["book_ids"], f"Book {book_id} not found in author1 book_ids: {author1_info['book_ids']}"
        assert book_id in author2_info["book_ids"], f"Book {book_id} not found in author2 book_ids: {author2_info['book_ids']}"
        assert book_id in author3_info["book_ids"], f"Book {book_id} not found in author3 book_ids: {author3_info['book_ids']}"
        
        # Verify each author has only one book (the one we just created)
        assert len(author1_info["book_ids"]) == 1
        assert len(author2_info["book_ids"]) == 1
        assert len(author3_info["book_ids"]) == 1
        
        # Verify the book has all three authors
        book_get = client.get(f"/book/{book_id}")
        book_info = book_get.json()
        assert len(book_info["author_ids"]) == 3
        assert author1_id in book_info["author_ids"]
        assert author2_id in book_info["author_ids"]
        assert author3_id in book_info["author_ids"]

    def test_create_book_with_duplicate_author_ids(self, client: TestClient):
        """Test POST /book/ with duplicate author IDs - should handle gracefully"""
        # Create an author first
        author_data = {
            "name": "Duplicate",
            "surname": "Test",
            "birthyear": 1975,
            "book_ids": []
        }
        author_response = client.post("/author/", json=author_data)
        author_id = author_response.json()

        # Create book with duplicate author IDs
        book_data = {
            "title": "Duplicate Author Book",
            "author_ids": [author_id, author_id, author_id],  # Same ID repeated
            "publisher": "Duplicate Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        book_response = client.post("/book/", json=book_data)
        assert book_response.status_code == 200
        book_id = book_response.json()

        # Verify author only has the book once in their book_ids (no duplicates)
        author_get = client.get(f"/author/{author_id}")
        author_info = author_get.json()
        assert book_id in author_info["book_ids"]
        assert author_info["book_ids"].count(book_id) == 1, "Book should appear only once in author's book_ids"

    def test_create_book_with_mixed_valid_invalid_authors(self, client: TestClient):
        """Test POST /book/ with mix of valid and invalid author IDs"""
        # Create one valid author
        author_data = {
            "name": "Valid",
            "surname": "Author",
            "birthyear": 1980,
            "book_ids": []
        }
        author_response = client.post("/author/", json=author_data)
        valid_author_id = author_response.json()

        # Try to create book with mix of valid and invalid author IDs
        book_data = {
            "title": "Mixed Authors Book",
            "author_ids": [valid_author_id, "invalid-author-id"],
            "publisher": "Mixed Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

        # Verify the valid author wasn't modified (atomic operation)
        author_get = client.get(f"/author/{valid_author_id}")
        author_info = author_get.json()
        assert len(author_info["book_ids"]) == 0, "Author should have no books due to failed book creation"

    def test_create_author_with_duplicate_book_ids(self, client: TestClient):
        """Test POST /author/ with duplicate book IDs"""
        # Create a book first
        book_data = {
            "title": "Duplicate Test Book",
            "author_ids": [],
            "publisher": "Test Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        book_response = client.post("/book/", json=book_data)
        book_id = book_response.json()

        # Create author with duplicate book IDs
        author_data = {
            "name": "Duplicate",
            "surname": "BookAuthor",
            "birthyear": 1990,
            "book_ids": [book_id, book_id, book_id]  # Same ID repeated
        }
        author_response = client.post("/author/", json=author_data)
        assert author_response.status_code == 200
        author_id = author_response.json()

        # Verify author has the book (should handle duplicates gracefully)
        author_get = client.get(f"/author/{author_id}")
        author_info = author_get.json()
        assert book_id in author_info["book_ids"]

    def test_create_author_with_mixed_valid_invalid_books(self, client: TestClient):
        """Test POST /author/ with mix of valid and invalid book IDs"""
        # Create one valid book
        book_data = {
            "title": "Valid Book",
            "author_ids": [],
            "publisher": "Valid Publisher", 
            "edition": 1,
            "published_date": "2023-01-01"
        }
        book_response = client.post("/book/", json=book_data)
        valid_book_id = book_response.json()

        # Try to create author with mix of valid and invalid book IDs
        author_data = {
            "name": "Mixed",
            "surname": "BooksAuthor",
            "birthyear": 1985,
            "book_ids": [valid_book_id, "invalid-book-id"]
        }
        response = client.post("/author/", json=author_data)
        assert response.status_code == 409
        assert "Book with ID invalid-book-id not found" in response.json()["detail"]

        # Verify the valid book wasn't modified (atomic operation)
        book_get = client.get(f"/book/{valid_book_id}")
        book_info = book_get.json()
        assert len(book_info["author_ids"]) == 0, "Book should have no authors due to failed author creation"

    def test_create_book_with_large_author_array(self, client: TestClient):
        """Test POST /book/ with large number of authors"""
        # Create 50 authors
        author_ids = []
        for i in range(50):
            author_data = {
                "name": f"Author{i}",
                "surname": f"Surname{i}",
                "birthyear": 1970 + i % 30,
                "book_ids": []
            }
            author_response = client.post("/author/", json=author_data)
            author_ids.append(author_response.json())

        # Create book with all 50 authors
        book_data = {
            "title": "Massive Collaboration Book",
            "author_ids": author_ids,
            "publisher": "Many Authors Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        book_response = client.post("/book/", json=book_data)
        assert book_response.status_code == 200
        book_id = book_response.json()

        # Verify bidirectional consistency for first and last authors
        first_author_get = client.get(f"/author/{author_ids[0]}")
        last_author_get = client.get(f"/author/{author_ids[-1]}")
        
        first_author_info = first_author_get.json()
        last_author_info = last_author_get.json()
        
        assert book_id in first_author_info["book_ids"]
        assert book_id in last_author_info["book_ids"]

        # Verify book has all authors
        book_get = client.get(f"/book/{book_id}")
        book_info = book_get.json()
        assert len(book_info["author_ids"]) == 50

    def test_create_author_with_large_book_array(self, client: TestClient):
        """Test POST /author/ with large number of books"""
        # Create 30 books
        book_ids = []
        for i in range(30):
            book_data = {
                "title": f"Book{i}",
                "author_ids": [],
                "publisher": f"Publisher{i}",
                "edition": i % 5 + 1,
                "published_date": f"2023-{(i % 12) + 1:02d}-01"
            }
            book_response = client.post("/book/", json=book_data)
            book_ids.append(book_response.json())

        # Create author with all 30 books
        author_data = {
            "name": "Prolific",
            "surname": "Author",
            "birthyear": 1960,
            "book_ids": book_ids
        }
        author_response = client.post("/author/", json=author_data)
        assert author_response.status_code == 200
        author_id = author_response.json()

        # Verify author has all books
        author_get = client.get(f"/author/{author_id}")
        author_info = author_get.json()
        assert len(author_info["book_ids"]) == 30
        assert all(book_id in author_info["book_ids"] for book_id in book_ids)

    def test_create_book_with_empty_string_author_ids(self, client: TestClient):
        """Test POST /book/ with empty strings in author_ids array"""
        book_data = {
            "title": "Empty String Test Book",
            "author_ids": ["", "  ", ""],  # Empty strings and whitespace
            "publisher": "Empty Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        # Should fail because empty strings are not valid author IDs
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_create_author_with_empty_string_book_ids(self, client: TestClient):
        """Test POST /author/ with empty strings in book_ids array"""
        author_data = {
            "name": "Empty",
            "surname": "StringTest",
            "birthyear": 1985,
            "book_ids": ["", "  ", ""]  # Empty strings and whitespace
        }
        response = client.post("/author/", json=author_data)
        # Should fail because empty strings are not valid book IDs
        assert response.status_code == 409
        assert "Book with ID" in response.json()["detail"]
        assert "not found" in response.json()["detail"]

    def test_create_book_with_none_values_in_author_ids(self, client: TestClient):
        """Test POST /book/ with None/null values in author_ids array"""
        book_data = {
            "title": "None Values Test Book",
            "author_ids": [None, "valid-id", None],  # None values mixed with string
            "publisher": "None Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        # Should fail due to invalid data types
        assert response.status_code == 422  # Pydantic validation error

    def test_atomic_reference_updates_on_book_creation_failure(self, client: TestClient):
        """Test that partial failures in POST /book/ don't leave database in inconsistent state"""
        # Create two valid authors
        author1_data = {
            "name": "Valid1",
            "surname": "Author1",
            "birthyear": 1980,
            "book_ids": []
        }
        author2_data = {
            "name": "Valid2", 
            "surname": "Author2",
            "birthyear": 1985,
            "book_ids": []
        }
        
        author1_response = client.post("/author/", json=author1_data)
        author2_response = client.post("/author/", json=author2_data)
        
        valid_author1_id = author1_response.json()
        valid_author2_id = author2_response.json()

        # Try to create book with valid authors + one invalid author
        # This should fail after processing some valid authors
        book_data = {
            "title": "Atomic Test Book",
            "author_ids": [valid_author1_id, valid_author2_id, "invalid-author-id"],
            "publisher": "Atomic Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

        # Verify that NO authors were modified (atomic operation)
        author1_get = client.get(f"/author/{valid_author1_id}")
        author2_get = client.get(f"/author/{valid_author2_id}")
        
        author1_info = author1_get.json()
        author2_info = author2_get.json()
        
        assert len(author1_info["book_ids"]) == 0, "Author1 should have no books due to failed book creation"
        assert len(author2_info["book_ids"]) == 0, "Author2 should have no books due to failed book creation"

        # Verify no book was created
        response = client.get("/book/")
        books = response.json()
        assert len(books) == 0, "No books should exist due to failed creation"

    def test_atomic_reference_updates_on_author_creation_failure(self, client: TestClient):
        """Test that partial failures in POST /author/ don't leave database in inconsistent state"""
        # Create two valid books
        book1_data = {
            "title": "Valid Book 1",
            "author_ids": [],
            "publisher": "Valid Publisher 1",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        book2_data = {
            "title": "Valid Book 2",
            "author_ids": [],
            "publisher": "Valid Publisher 2", 
            "edition": 1,
            "published_date": "2023-02-01"
        }
        
        book1_response = client.post("/book/", json=book1_data)
        book2_response = client.post("/book/", json=book2_data)
        
        valid_book1_id = book1_response.json()
        valid_book2_id = book2_response.json()

        # Try to create author with valid books + one invalid book
        author_data = {
            "name": "Atomic",
            "surname": "TestAuthor",
            "birthyear": 1990,
            "book_ids": [valid_book1_id, valid_book2_id, "invalid-book-id"]
        }
        response = client.post("/author/", json=author_data)
        assert response.status_code == 409
        assert "Book with ID invalid-book-id not found" in response.json()["detail"]

        # Verify that NO books were modified (atomic operation)
        book1_get = client.get(f"/book/{valid_book1_id}")
        book2_get = client.get(f"/book/{valid_book2_id}")
        
        book1_info = book1_get.json()
        book2_info = book2_get.json()
        
        assert len(book1_info["author_ids"]) == 0, "Book1 should have no authors due to failed author creation"
        assert len(book2_info["author_ids"]) == 0, "Book2 should have no authors due to failed author creation"

        # Verify no author was created
        response = client.get("/author/")
        authors = response.json()
        assert len(authors) == 0, "No authors should exist due to failed creation"


class TestIntegrationScenarios:
    def test_full_workflow(self, client: TestClient):
        """Test complete workflow: create author, create book, update, delete"""
        # Create author
        author_data = {
            "name": "Integration",
            "surname": "Test",
            "birthyear": 1990,
            "book_ids": []
        }
        author_response = client.post("/author/", json=author_data)
        author_id = author_response.json()

        # Create book with author
        book_data = {
            "title": "Integration Book",
            "author_ids": [author_id],
            "publisher": "Integration Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        book_response = client.post("/book/", json=book_data)
        book_id = book_response.json()

        # Verify author has book in their list
        author_get_response = client.get(f"/author/{author_id}")
        author_info = author_get_response.json()
        assert book_id in author_info["book_ids"]

        # Update book
        updated_book_data = {
            "title": "Updated Integration Book",
            "author_ids": [author_id],
            "publisher": "Updated Publisher",
            "edition": 2,
            "published_date": "2023-06-01"
        }
        client.put(f"/book/{book_id}", json=updated_book_data)

        # Delete book
        client.delete(f"/book/{book_id}")

        # Now should be able to delete author
        delete_response = client.delete(f"/author/{author_id}")
        assert delete_response.status_code == 200
