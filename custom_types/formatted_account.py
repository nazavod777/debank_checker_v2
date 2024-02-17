class FormattedAccount:
    def __init__(self,
                 address: str,
                 mnemonic: str | None = None,
                 private_key: str | None = None) -> None:
        self.address: str = address
        self.mnemonic: str | None = mnemonic
        self.private_key: str | None = private_key
