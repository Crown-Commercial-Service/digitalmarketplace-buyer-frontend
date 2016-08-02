from app.helpers import shared_helpers


def test_chunk_string():
    assert list(shared_helpers.chunk_string("123456", 3)) == ["123", "456"]
    assert list(shared_helpers.chunk_string("1234567", 3)) == ["123", "456", "7"]
    assert list(shared_helpers.chunk_string("12345678910", 4)) == ["1234", "5678", "910"]
    assert list(shared_helpers.chunk_string("123456789101", 4)) == ["1234", "5678", "9101"]
