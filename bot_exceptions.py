class IncorrectModeError(Exception):
    """Raised when the user inputs an invalid mode."""
    def __str__(self):
        return f"User inputted an invalid mode."