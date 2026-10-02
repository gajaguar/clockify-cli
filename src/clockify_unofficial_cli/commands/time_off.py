from typing import Final

import typer

from clockify_unofficial_cli.commands import time_off_balance
from clockify_unofficial_cli.commands import time_off_policy
from clockify_unofficial_cli.commands import time_off_request

APP: Final = typer.Typer(help="Time off policies, requests and balances.", no_args_is_help=True)
APP.add_typer(time_off_policy.APP, name="policy")
APP.add_typer(time_off_request.APP, name="request")
APP.add_typer(time_off_balance.APP, name="balance")
