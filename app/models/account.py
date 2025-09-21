from typing import Any

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, synonym

from app.core.crypto import decrypt_dict, encrypt_dict

from app.db.base_class import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String, nullable=False)
    _credentials = Column("credentials", Text, nullable=False)

    owner = relationship("User", back_populates="accounts")
    sites = relationship("Site", back_populates="account")

    def _get_credentials(self) -> dict[str, Any]:
        raw = self._credentials
        if raw is None:
            return {}
        if isinstance(raw, str):
            return decrypt_dict(raw)
        return raw

    def _set_credentials(self, value: dict[str, Any] | str | None) -> None:
        if value is None:
            raise ValueError("Credentials cannot be null")
        if isinstance(value, str):
            self._credentials = value
        else:
            self._credentials = encrypt_dict(value)

    credentials = synonym("_credentials", descriptor=property(_get_credentials, _set_credentials))
