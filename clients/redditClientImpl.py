import praw
import os 
import traceback 
import pprint

from datetime import datetime
from prawcore import NotFound

# Storing API keys for Reddit
rClientId = os.environ.get('R_CLIENT_ID')
rClientSecret = os.environ.get('R_CLIENT_SECRET')
rUserAgent = os.environ.get('R_USER_AGENT')

# Class to encapsulate interaction with the Reddit client (PRAW)
class reddit_hunter:

    # Reddit client object
    dealFinder = praw.Reddit(client_id=rClientId,
                             client_secret=rClientSecret,
                             user_agent=rUserAgent)

    # Constructor for reddit_hunter
    # Inputs: None
    # Outputs: None
    # Exceptions: None
    def __init__(self) -> None:
        self.channelToSub: dict[str, self.subreddit_hunter] = {}
        self.NSFW_SUBS: set(str) = set()

    # Function to check if a subreddit exists before invoking add_or_get_sub
    # Inputs: subreddit (str) to search for
    # Outputs: True/False
    # Exceptions: NotFound (expected when subreddit is not found)
    def sub_exists(self, subreddit):
        if subreddit in self.NSFW_SUBS: 
            return False
        exists = True
        try:
            self.dealFinder.subreddits.search_by_name(subreddit, exact=True)
            if self.dealFinder.subreddit(subreddit).over18:
                self.NSFW_SUBS.add(subreddit)
                return False
        except NotFound:
            exists = False
        return exists

    # Function to pull a subreddit_hunter for the given discord channel
    # Inputs: Channel (str) - Discord Channel Id, Subreddit (str) - Subreddit name
    # Outputs: Subreddit Hunter (subreddit_hunter)
    # Exceptions: None 
    def add_or_get_sub(self, channel: str, subreddit: str):
        if subreddit != '':
            self.channelToSub[channel] = self.subreddit_hunter(subreddit, self.dealFinder)
        return self.channelToSub.setdefault(channel, self.subreddit_hunter('GameDeals', self.dealFinder))

    # Function to provide detailed information on a specific Reddit submission 
    # Inputs: id (str) for a reddit submission
    # Outputs: Submission details (dict)
    # Exceptions: None (an invalid id will return an empty result)
    def get_post_details_from_id(self, id: str) -> str:
        try: 
            submission = self.dealFinder.submission(id=id)
            # To get available attributes of a submission,
            # see https://praw.readthedocs.io/en/latest/getting_started/quick_start.html#determine-available-attributes-of-an-object
            # print(submission.title)
            # pprint.pprint(vars(submission))
        except:
            traceback.print_exc()
            return None
        # Datetime conversion seems to slow down this func proc time
        return {'Title': f'{str(submission.title)}', 
                'Spoiler': f'{str(submission.spoiler)}',
                'Upvote Ratio': f'{str(submission.upvote_ratio * 100)}%', 
                'Flair': f'{str(submission.link_flair_text)}',
                'OP': f'{str(submission.author)}', 
                'Total Awards': f'{str(submission.total_awards_received)}',
                'Created on (UTC)': f'{str(datetime.fromtimestamp(submission.created))}'
                }

    # Child class to encpasulate specific subreddit operations
    class subreddit_hunter():

        # Constructor for subreddit_hunter
        # Inputs: subreddit (str), dealFinder (praw.Reddit)
        # Outputs: None
        # Excpetions: None
        def __init__(self, subreddit, dealFinder) -> None:
            self.subreddit = subreddit
            try:
                self.sub: praw.models.Subreddit = dealFinder.subreddit(subreddit)
            except:
                traceback.print_exc()
            self.commandToCall = {
                "hotdeals": self._get_game_deals_func(self.sub.hot),
                "risingdeals": self._get_game_deals_func(self.sub.rising),
                "topdeals": self._get_game_deals_func(self.sub.top),
                "controversialdeals": self._get_game_deals_func(self.sub.controversial)
            }

        # Function for creating refs of posts + post links
        # Inputs: count (int) -- for # of results, method (praw.models.Subreddit)
        # Outputs: result (dict) of posts + post links
        # Exceptions: None
        def _get_game_deals(self, count: int, method) -> dict[str, str]:
            try: 
                result = [(f"[{submission.id}]{submission.title}", f"https://www.reddit.com{submission.permalink}")
                        for submission in method(limit=count)]
            except: 
                traceback.print_exc()
            return dict(result)

        # Function to trigger _get_game_deals()
        # Inputs: method (praw.models.Subreddit)
        # Outputs: Invocation result of _get_game_deals
        # Exceptions: None
        def _get_game_deals_func(self, method):
            return lambda count : self._get_game_deals(count, method)

        # Function to check if input is a valid subreddit action 
        # Inputs: action (str) - being checked
        # Outputs: True/False (boolean)
        # Excpetions: None 
        def is_valid_action(self, action: str):
            return action in self.commandToCall.keys()

        # Function to search a subreddit based on a given query + time range
        # Inputs: time (str) - time range, query (str) - query to search 
        # Outputs: Reference of posts + post links
        # Exceptions: TBD
        # TODO : Want to see if I can factor this so it can follow call
        # pattern for the dict/lambda invocation
        def search_sub(self, time: str, query: str): 
            try:
                result = [(f"[{submission.id}]{submission.title}", f"https://www.reddit.com{submission.permalink}")
                        for submission in self.sub.search(query=query, time_filter=time, limit=5)]
            except ValueError:
                traceback.print_exc()
                return None
            return dict(result)