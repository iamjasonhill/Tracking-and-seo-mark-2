from app import crud
from app.models.account import Account
from app.schemas.account import AccountCreate
from app.schemas.user import UserCreate


def test_account_credentials_are_encrypted(db_session):
    user = crud.user.create(
        db_session,
        obj_in=UserCreate(email="secure@example.com", password="secret"),
    )

    account = crud.account.create(
        db_session,
        obj_in=AccountCreate(
            user_id=user.id,
            provider="google",
            credentials={"token": "top-secret-token"},
        ),
    )

    stored = (
        db_session.query(Account)
        .filter(Account.id == account.id)
        .one()
    )

    ciphertext = stored._credentials
    assert isinstance(ciphertext, str)
    assert ciphertext
    assert ciphertext != '{"token":"top-secret-token"}'

    # The public accessor should transparently decrypt the payload.
    assert stored.credentials == {"token": "top-secret-token"}
