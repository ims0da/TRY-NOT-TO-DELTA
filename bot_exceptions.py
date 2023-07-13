class IncorrectModeError(Exception):
    """Raised when the user inputs an invalid mode."""
    def __str__(self):
        return "User inputted an invalid mode."


class PlayerNotFoundError(Exception):
    """Raised when player is not in the database."""
    def __str__(self) -> str:
        return "Player not found in database."


class ModsDontMatchError(Exception):
    """Raised when mods dont match (idk)"""
    def __str__(self) -> str:
        return "Mods don't match."
