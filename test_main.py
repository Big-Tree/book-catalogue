from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from main import app, author_db, book_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Clear the databases before each test"""
    author_db.clear()
    book_db.clear()


class TestAuthorEndpoints:
    def test_get_authors_summary_empty(self, client):
        """Test GET /author/ with empty database"""
        response = client.get("/author/")
        assert response.status_code == 200
        assert response.json() == 0

    def test_create_author(self, client):
        """Test POST /author/"""
        author_data = {
            "name": "John",
            "surname": "Doe",
            "birthyear": 1970,
            "books": []
        }
        response = client.post("/author/", json=author_data)
        assert response.status_code == 200
        author_id = response.json()
        assert isinstance(author_id, str)
        assert len(author_id) > 0

    def test_get_authors_summary_with_data(self, client):
        """Test GET /author/ after creating authors"""
        author_data = {
            "name": "Jane",
            "surname": "Smith", 
            "birthyear": 1985,
            "books": []
        }
        client.post("/author/", json=author_data)
        client.post("/author/", json=author_data)
        
        response = client.get("/author/")
        assert response.status_code == 200
        assert response.json() == 2

    def test_get_author_by_id(self, client):
        """Test GET /author/{author_id}"""
        author_data = {
            "name": "Alice",
            "surname": "Johnson",
            "birthyear": 1990,
            "books": []
        }
        create_response = client.post("/author/", json=author_data)
        author_id = create_response.json()
        
        response = client.get(f"/author/{author_id}")
        assert response.status_code == 200
        returned_author = response.json()
        assert returned_author["name"] == "Alice"
        assert returned_author["surname"] == "Johnson"
        assert returned_author["birthyear"] == 1990
        assert returned_author["books"] == []

    def test_get_author_not_found(self, client):
        """Test GET /author/{author_id} with non-existent ID"""
        response = client.get("/author/nonexistent-id")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_update_author(self, client):
        """Test PUT /author/{author_id}"""
        original_data = {
            "name": "Bob",
            "surname": "Wilson",
            "birthyear": 1975,
            "books": []
        }
        create_response = client.post("/author/", json=original_data)
        author_id = create_response.json()
        
        updated_data = {
            "name": "Robert",
            "surname": "Wilson",
            "birthyear": 1976,
            "books": []
        }
        response = client.put(f"/author/{author_id}", json=updated_data)
        assert response.status_code == 200
        
        # Verify the update
        get_response = client.get(f"/author/{author_id}")
        updated_author = get_response.json()
        assert updated_author["name"] == "Robert"
        assert updated_author["birthyear"] == 1976

    def test_update_author_not_found(self, client):
        """Test PUT /author/{author_id} with non-existent ID"""
        author_data = {
            "name": "Test",
            "surname": "User",
            "birthyear": 2000,
            "books": []
        }
        response = client.put("/author/nonexistent-id", json=author_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_delete_author(self, client):
        """Test DELETE /author/{author_id}"""
        author_data = {
            "name": "Charlie",
            "surname": "Brown",
            "birthyear": 1980,
            "books": []
        }
        create_response = client.post("/author/", json=author_data)
        author_id = create_response.json()
        
        response = client.delete(f"/author/{author_id}")
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(f"/author/{author_id}")
        assert get_response.status_code == 400

    def test_delete_author_not_found(self, client):
        """Test DELETE /author/{author_id} with non-existent ID"""
        response = client.delete("/author/nonexistent-id")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_delete_author_with_books_conflict(self, client):
        """Test DELETE /author/{author_id} when author has books"""
        # Create author
        author_data = {
            "name": "Diana",
            "surname": "Prince",
            "birthyear": 1985,
            "books": []
        }
        author_response = client.post("/author/", json=author_data)
        author_id = author_response.json()
        
        # Create book with this author
        book_data = {
            "title": "Test Book",
            "author_list": [author_id],
            "publisher": "Test Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        client.post("/book/", json=book_data)
        
        # Try to delete author
        response = client.delete(f"/author/{author_id}")
        assert response.status_code == 409
        assert "Cannot delete author" in response.json()["detail"]


class TestBookEndpoints:
    def test_get_books_summary_empty(self, client):
        """Test GET /book/ with empty database"""
        response = client.get("/book/")
        assert response.status_code == 200
        assert response.json() == 0

    def test_create_book_without_authors(self, client):
        """Test POST /book/ with empty author list"""
        book_data = {
            "title": "Solo Book",
            "author_list": [],
            "publisher": "Solo Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        assert response.status_code == 200
        book_id = response.json()
        assert isinstance(book_id, str)
        assert len(book_id) > 0

    def test_create_book_with_authors(self, client):
        """Test POST /book/ with valid authors"""
        # Create authors first
        author_data = {
            "name": "Author",
            "surname": "One",
            "birthyear": 1970,
            "books": []
        }
        author_response = client.post("/author/", json=author_data)
        author_id = author_response.json()
        
        book_data = {
            "title": "Collaborative Book",
            "author_list": [author_id],
            "publisher": "Collab Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        assert response.status_code == 200
        book_id = response.json()
        assert isinstance(book_id, str)

    def test_create_book_with_invalid_author(self, client):
        """Test POST /book/ with non-existent author"""
        book_data = {
            "title": "Invalid Book",
            "author_list": ["nonexistent-author-id"],
            "publisher": "Test Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.post("/book/", json=book_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_get_books_summary_with_data(self, client):
        """Test GET /book/ after creating books"""
        book_data = {
            "title": "Test Book",
            "author_list": [],
            "publisher": "Test Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        client.post("/book/", json=book_data)
        client.post("/book/", json=book_data)
        
        response = client.get("/book/")
        assert response.status_code == 200
        assert response.json() == 2

    def test_get_book_by_id(self, client):
        """Test GET /book/{book_id}"""
        book_data = {
            "title": "Specific Book",
            "author_list": [],
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
        assert returned_book["author_list"] == []

    def test_get_book_not_found(self, client):
        """Test GET /book/{book_id} with non-existent ID"""
        response = client.get("/book/nonexistent-id")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_update_book(self, client):
        """Test PUT /book/{book_id}"""
        original_data = {
            "title": "Original Title",
            "author_list": [],
            "publisher": "Original Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        create_response = client.post("/book/", json=original_data)
        book_id = create_response.json()
        
        updated_data = {
            "title": "Updated Title",
            "author_list": [],
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

    def test_update_book_not_found(self, client):
        """Test PUT /book/{book_id} with non-existent ID"""
        book_data = {
            "title": "Test Book",
            "author_list": [],
            "publisher": "Test Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        response = client.put("/book/nonexistent-id", json=book_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_delete_book(self, client):
        """Test DELETE /book/{book_id}"""
        book_data = {
            "title": "Book to Delete",
            "author_list": [],
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

    def test_delete_book_not_found(self, client):
        """Test DELETE /book/{book_id} with non-existent ID"""
        response = client.delete("/book/nonexistent-id")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]


class TestIntegrationScenarios:
    def test_full_workflow(self, client):
        """Test complete workflow: create author, create book, update, delete"""
        # Create author
        author_data = {
            "name": "Integration",
            "surname": "Test",
            "birthyear": 1990,
            "books": []
        }
        author_response = client.post("/author/", json=author_data)
        author_id = author_response.json()
        
        # Create book with author
        book_data = {
            "title": "Integration Book",
            "author_list": [author_id],
            "publisher": "Integration Publisher",
            "edition": 1,
            "published_date": "2023-01-01"
        }
        book_response = client.post("/book/", json=book_data)
        book_id = book_response.json()
        
        # Verify author has book in their list
        author_get_response = client.get(f"/author/{author_id}")
        author_info = author_get_response.json()
        assert book_id in author_info["books"]
        
        # Update book
        updated_book_data = {
            "title": "Updated Integration Book",
            "author_list": [author_id],
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
