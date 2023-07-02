class IncorrectModeError(Exception):
    """Raised when the user inputs an invalid mode."""
    def __str__(self):
        return "User inputted an invalid mode."
