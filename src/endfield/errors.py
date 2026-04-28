class EndfieldError(Exception):
    """Base exception for all Endfield library errors."""


class APIError(EndfieldError):
    """Raised when the Enka Network API returns a non-200 response."""

    def __init__(self, status: int, url: str, message: str = "") -> None:
        self.status = status
        self.url = url
        self.message = message
        super().__init__(f"API error {status} at {url}: {message}")


class DecodeError(EndfieldError):
    """Raised when the reference-index __data.json cannot be decoded."""


class AssetError(EndfieldError):
    """Raised when a static asset cannot be found locally or fetched remotely."""

    def __init__(self, asset_type: str, asset_id: str, message: str = "") -> None:
        self.asset_type = asset_type
        self.asset_id = asset_id
        super().__init__(
            f"{asset_type} asset not found: '{asset_id}'. {message}".strip()
        )


class CharacterNotFoundError(AssetError):
    def __init__(self, char_id: str | int) -> None:
        super().__init__("Character", str(char_id))


class WeaponNotFoundError(AssetError):
    def __init__(self, weapon_id: str | int) -> None:
        super().__init__("Weapon", str(weapon_id))


class EquipmentNotFoundError(AssetError):
    def __init__(self, equip_id: str | int) -> None:
        super().__init__("Equipment", str(equip_id))


class SuitNotFoundError(AssetError):
    def __init__(self, suit_id: str) -> None:
        super().__init__("Suit", suit_id)
