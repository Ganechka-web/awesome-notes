from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.services.security import SecurityPasswordService


@pytest.mark.parametrize(
    ("bare_password", "bare_password_2", "expectation"),
    (
        ("some_password", "some_password", True), 
        ("some_password", "some_password_1", False),
        ("Some_1234_password##@", "Some_1234_password##@", True),
        ("Some_1234_password#@", "Some_1234_password##@", False),
    ),
)
def test_verify_password_hash(
    bare_password: str,
    bare_password_2: str,
    expectation: bool,
    get_password_service: "SecurityPasswordService",
):
    bare_password_hash = get_password_service.generate_password_hash(bare_password)
    result = get_password_service.verify_password_hash(bare_password_2, bare_password_hash)
    assert result == expectation
