import pytest
from project import app as flask_app, db as flask_db
from project.books.models import Book

@pytest.fixture(scope="module")
def app():
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    with flask_app.app_context():
        yield flask_app


@pytest.fixture(scope="function")
def session(app):
    flask_db.create_all()
    yield flask_db.session
    flask_db.session.remove()
    flask_db.drop_all()


def test_create_book_valid_default_status(session):
    book = Book(
        name="Sample Book",
        author="John Doe",
        year_published=2020,
        book_type="Fiction",
    )
    session.add(book)
    session.commit()

    stored = Book.query.filter_by(name="Sample Book").first()
    assert stored is not None
    assert stored.author == "John Doe"
    assert stored.year_published == 2020
    assert stored.book_type == "Fiction"
    assert stored.status == "available"


def test_create_book_valid_given_status(session):
    book = Book(
        name="Status Book",
        author="John Doe",
        year_published=2020,
        book_type="Fiction",
        status="unavailable",
    )
    session.add(book)
    session.commit()

    stored = Book.query.filter_by(name="Status Book").first()
    assert stored is not None
    assert stored.status == "unavailable"


def test_create_book_missing_name(session):
    with pytest.raises(Exception):
        book = Book(
            name=None,
            author="John Doe",
            year_published=2020,
            book_type="Fiction",
        )
        session.add(book)
        session.commit()


def test_create_book_invalid_year(session):
    with pytest.raises(Exception):
        book = Book(
            name="Invalid Year Book",
            author="Jane Doe",
            year_published="abcd",
            book_type="Fiction",
        )
        session.add(book)
        session.commit()


def test_create_book_name_too_long(session):
    with pytest.raises(Exception):
        book = Book(
            name="a" * 65,
            author="Jane Doe",
            year_published=2024,
            book_type="Fiction",
        )
        session.add(book)
        session.commit()


def test_create_book_author_too_long(session):
    with pytest.raises(Exception):
        book = Book(
            name="Sample Book",
            author="a" * 65,
            year_published=2024,
            book_type="Fiction",
        )
        session.add(book)
        session.commit()


def test_create_book_book_type_too_long(session):
    with pytest.raises(Exception):
        book = Book(
            name="Sample Book",
            author="Jane Doe",
            year_published=2024,
            book_type="a" * 21,
        )
        session.add(book)
        session.commit()


def test_create_book_status_too_long(session):
    with pytest.raises(Exception):
        book = Book(
            name="Sample Book",
            author="Jane Doe",
            year_published=2024,
            book_type="Fiction",
            status="a" * 21,
        )
        session.add(book)
        session.commit()


def test_create_book_name_not_unique(session):
    first = Book(
        name="Sample Book",
        author="John Doe",
        year_published=2020,
        book_type="Fiction",
    )
    second = Book(
        name="Sample Book",
        author="John Doe2",
        year_published=2022,
        book_type="Fiction",
    )
    with pytest.raises(Exception):
        session.add(first)
        session.add(second)
        session.commit()


def test_sql_injection_like_input(session):
    suspicious_name = "Book'); DROP TABLE books;--"
    book = Book(
        name=suspicious_name,
        author="Hacker",
        year_published=2023,
        book_type="Fiction",
    )
    with pytest.raises(Exception):
        session.add(book)
        session.commit()


def test_javascript_injection_like_input(session):
    suspicious_name = "<script>alert('Hacked!');</script>"
    book = Book(
        name=suspicious_name,
        author="Hacker",
        year_published=2023,
        book_type="Fiction",
    )
    with pytest.raises(Exception):
        session.add(book)
        session.commit()


def test_extremely_long_input(session):
    long_value = "a" * 10000
    attrs_to_check = ["name", "author", "book_type", "status"]

    for attr in attrs_to_check:
        base_data = {
            "name": "Normal Name",
            "author": "Normal Author",
            "year_published": 2023,
            "book_type": "Fiction",
            "status": "available",
        }

        base_data[attr] = long_value

        book = Book(**base_data)
        session.add(book)
        session.commit()

        stored = Book.query.filter_by(**{attr: long_value}).first()
        assert stored is not None
        assert getattr(stored, attr) == long_value
        assert len(getattr(stored, attr)) == 10000

        session.delete(stored)
        session.commit()


def test_negative_year(session):
    book = Book(
        name="Boundary Year Book",
        author="Author",
        year_published=-2,
        book_type="Non-Fiction",
    )
    with pytest.raises(Exception):
        session.add(book)
        session.commit()


def test_create_book_missing_author(session):
    with pytest.raises(Exception):
        book = Book(
            name="No Author Book",
            author=None,
            year_published=2021,
            book_type="Fiction",
        )
        session.add(book)
        session.commit()


def test_create_book_empty_status_defaults_to_available(session):
    book = Book(
        name="Empty Status Book",
        author="Author",
        year_published=2021,
        book_type="Fiction",
        status=None,
    )
    session.add(book)
    session.commit()

    stored = Book.query.filter_by(name="Empty Status Book").first()
    assert stored is not None
    assert stored.status == "available"
