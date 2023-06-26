class IncorrectModeError(Exception):
    """Raise when users inputted mode is not valid"""
    def __str__(self):
        return f"User inputted an invalid mode."