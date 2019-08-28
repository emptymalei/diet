import logging
from urllib.parse import unquote as _unquote
from .data import ELF_CODE as _ELF_CODE

logging.basicConfig()
logger = logging.getLogger('texts.wrangling.companies')


def clean_company_name(
    company_name, remove_chars=None, remove_legal_form=None
    ):
    """Clean company name by removing unnecessary strings.

    1. Remove some special characters.
    2. Strip the whitespaces.
    3. Remove legal forms such as gmbh, e.v.
    """
    if not isinstance(company_name, str):
        logger.warning(
            'clean_company_name:: input company is not string: {}'.format(
                company_name
            )
            )
    logger.debug(f'clean_company_name:: company_name is {company_name}')
    if remove_legal_form is None:
        remove_legal_form = _ELF_CODE

    if remove_chars is None:
        remove_chars = [
            '"', "'", '(', ')', '[', ']'
            ]

    # unquote name to make sure the string do not have url encodings
    logger.debug(f'clean_company_name:: unquoting {company_name}')
    company_name = _unquote(company_name)

    company_name = company_name.strip()

    logger.debug(f'clean_company_name:: legalform for {company_name}')
    for elf in remove_legal_form:
        spaced_elf = ' ' + elf
        if company_name.endswith(spaced_elf):
            logger.debug(f'Removing {elf} from company name {company_name}')
            company_name = company_name[:-len(spaced_elf)]

    company_name = company_name.strip()

    # remove special characters from company name
    for char in remove_chars:
        company_name = company_name.replace(char, '')

    # convert to lower case
    company_name = company_name.lower()

    logger.debug(f'clean_company_name:: company_name_enforcement for {company_name}')
    # Rename companies using a pre-defined map
    company_name_map = {}
    logger.debug(
        'company_data::looked through company name enforcement: {}'.format(
            company_name_map
            )
        )
    if company_name_map:
        company_name = company_name_map.get('company')
        logger.debug(f'company_data::company_name_map exists: {company_name}')

    return company_name