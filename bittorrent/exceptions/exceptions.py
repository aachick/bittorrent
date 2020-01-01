class InvalidTorrentFileBencoding(Exception):

    def __init__(self, message):
        super().__init__(message)


class InvalidBencodeDataType(Exception):

    def __init__(self, message):
        super().__init__(message)


class InvalidMessageStructure(Exception):

    def __init__(self, message):
        super().__init__(message)


class IncorrectInfoHash(Exception):

    def __init__(self, message):
        super().__init__(message)


class InvalidBitfieldLength(Exception):

    def __init__(self, message):
        super().__init__(message)


if __name__ == "__main__":
    pass
