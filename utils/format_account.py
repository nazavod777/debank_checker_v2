import re

from eth_account import Account
from eth_utils.exceptions import ValidationError
from loguru import logger
from web3.auto import w3

from custom_types import FormattedAccount
from data.constants import predefined_words
from utils.misc import chunks

Account.enable_unaudited_hdwallet_features()


def format_account(account_data: str) -> FormattedAccount | None:
    split_words = re.split(r'[,.\-_;:\\/| \s]\s*', account_data)
    account_data_words = re.findall(r'\b\w+\b', account_data)
    account_data_sorted_mnemonic_words = [word for word in account_data_words if word in predefined_words]

    target_mnemonics: list[str] = []
    for current_mnemonic_length in [12, 18, 24]:
        for target_mnemonics_chunk in chunks(account_data_sorted_mnemonic_words, current_mnemonic_length):
            if len(target_mnemonics_chunk) == current_mnemonic_length:
                target_mnemonics.append(' '.join(target_mnemonics_chunk))

    for current_target_mnemonic in target_mnemonics:
        try:
            address = Account.from_mnemonic(mnemonic=current_target_mnemonic).address

            return FormattedAccount(address=address,
                                    mnemonic=current_target_mnemonic)

        except (ValueError, ValidationError):
            pass

    for current_target_private_key in split_words:
        try:
            address = Account.from_key(private_key=current_target_private_key).address

            return FormattedAccount(address=address, private_key=current_target_private_key)
        except (ValueError, ValidationError):
            pass

    for current_target_address in split_words:
        try:
            address = w3.to_checksum_address(current_target_address)

            return FormattedAccount(address=address)
        except (ValueError, ValidationError):
            pass

    logger.error(f'{account_data} | Invalid Address/Mnemonic/Key')

    return None
