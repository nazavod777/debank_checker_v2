import re

from eth_account import Account
from eth_utils.exceptions import ValidationError
from loguru import logger
from web3.auto import w3

from custom_types import FormattedAccount
from data import config
from data.constants import predefined_words
from utils.misc import chunks

Account.enable_unaudited_hdwallet_features()


def format_account(account_data: str) -> list[FormattedAccount]:
    founded_accounts: list[FormattedAccount] = []
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
            for i in range(config.ACCOUNT_PATH_INDEX):
                account = Account.from_mnemonic(mnemonic=current_target_mnemonic,
                                                account_path=f"m/44'/60'/0'/0/{i}")

                founded_account: FormattedAccount = FormattedAccount(address=account.address,
                                                                     mnemonic=current_target_mnemonic,
                                                                     private_key=account.key.hex())

                for current_account in founded_accounts:
                    if current_account.address.lower() == founded_account.address.lower():
                        break

                else:
                    founded_accounts.append(founded_account)


        except (ValueError, ValidationError):
            pass

    for current_target_private_key in split_words:
        try:
            account = Account.from_key(private_key=current_target_private_key)
            founded_account: FormattedAccount = FormattedAccount(address=account.address,
                                                                 private_key=account.key.hex())

            for current_account in founded_accounts:
                if current_account.address.lower() == founded_account.address.lower():
                    break

            else:
                founded_accounts.append(founded_account)
        except (ValueError, ValidationError):
            pass

    for current_target_address in split_words:
        try:
            address = w3.to_checksum_address(current_target_address)
            founded_account: FormattedAccount = FormattedAccount(address=address)

            for current_account in founded_accounts:
                if current_account.address.lower() == founded_account.address.lower():
                    break

            else:
                founded_accounts.append(founded_account)

        except (ValueError, ValidationError):
            pass

    if not founded_accounts:
        logger.error(f'{account_data} | Invalid Address/Mnemonic/Key')

    return founded_accounts
