"""

Author:    John Cleaver <cleaver.john.k@gmail.com>
Copyright: 2017 John Cleaver
License:   MIT (See LICENSE file)
"""

import os
from datetime import datetime

from cassiopeia import riotapi
from cassiopeia.type.core.common import Queue
from cassiopeia.type.api.store import SQLAlchemyDB
from cassiopeia.type.api.exception import APIError

riotapi.set_region("NA")
riotapi.print_calls(True)
key = key = os.environ["DEV_KEY"]
riotapi.set_api_key(key)

current_patch_start = datetime(2017, 3, 22)

queue = Queue.flex_threes

def auto_retry(api_call_method):
    """ A decorator to automatically retry 500s (Service Unavailable) and skip 400s (Bad Request) or 404s (Not Found). """
    def call_wrapper(*args, **kwargs):
        try:
            return api_call_method(*args, **kwargs)
        except APIError as error:
            # Try Again Once
            if error.error_code in [500]:
                try:
                    print("Got a 500, trying again...")
                    return api_call_method(*args, **kwargs)
                except APIError as another_error:
                    if another_error.error_code in [500, 400, 404]:
                        pass
                    else:
                        raise another_error

            # Skip
            elif error.error_code in [400, 404]:
                print("Got a 400 or 404")
                pass

            # Fatal
            else:
                raise error
    return call_wrapper

riotapi.get_match = auto_retry(riotapi.get_match)

def get_summoners():
    summoners = [entry.summoner for entry in riotapi.get_master(queue)]
    summoners.extend([entry.summoner for entry in riotapi.get_challenger(queue)])

    return summoners


def get_matches(summoners):
    for summoner in summoners:
        for match_reference in summoner.match_list(begin_time=current_patch_start, ranked_queues=Queue.ranked_premade_threes):
            match = riotapi.get_match(match_reference)


def main():
    db = SQLAlchemyDB("sqlite", "", "matches.db", "", "")
    get_matches(get_summoners())
    db.close()


if __name__ == '__main__':
    main()
