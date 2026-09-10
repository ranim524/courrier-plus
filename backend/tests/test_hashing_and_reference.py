import hashlib
import re

from app.utils.hashing import sha256_of_bytes
from app.utils.reference import generate_candidate_reference


def test_sha256_matches_known_value():
    data = b"Courrier+ test document content"
    expected = hashlib.sha256(data).hexdigest()
    assert sha256_of_bytes(data) == expected


def test_reference_format():
    reference = generate_candidate_reference()
    assert re.match(r"^TN-\d{4}-\d{7}$", reference)


def test_reference_uniqueness_high_probability():
    references = {generate_candidate_reference() for _ in range(200)}
    assert len(references) == 200
