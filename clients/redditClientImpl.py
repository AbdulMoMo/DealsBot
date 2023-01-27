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
    """Class to encaspulate Reddit (PRAW) client implementation
    """

    # Reddit client object
    dealFinder = praw.Reddit(client_id=rClientId,
                             client_secret=rClientSecret,
                             user_agent=rUserAgent)

    def __init__(self) -> None:
        """Constructor for `reddit_hunter`

        Args:
            None
        Exceptions:
            None
        """
        self.channelToSub: dict[str, self.subreddit_hunter] = {}
        self.NSFW_SUBS: set(str) = set()

    def sub_exists(self, subreddit):
        """Function to check if a subreddit exists before invoking `add_or_get_sub`

        Args:
            subreddit (str): to search for
        Outputs:
            Boolean 
        Exceptions:
            NotFound (expected when subreddit is not found)
        """
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

    def add_or_get_sub(self, channel: str, subreddit: str):
        """Function to pull a subreddit_hunter for the given discord channel

        Args:
            Channel (str): Discord Channel Id, Subreddit (str): Subreddit name
        Outputs:
            Subreddit Hunter (subreddit_hunter) 
        Exceptions:
            None
        """
        if subreddit != '':
            self.channelToSub[channel] = self.subreddit_hunter(subreddit, self.dealFinder)
        return self.channelToSub.setdefault(channel, self.subreddit_hunter('GameDeals', self.dealFinder))

    def get_post_details_from_id(self, id: str) -> str:
        """Function to provide detailed information on a specific Reddit submission 

        Args:
            id (str): for a reddit submission
        Outputs:
            Submission details (dict)
        Exceptions:
            None (an invalid id will return an empty result)
        """
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
        """Class to encaspulate Subreddit specific logic for Reddit (PRAW) client implementation
        """

        def __init__(self, subreddit: str, dealFinder) -> None:
            """Constructor for `subreddit_hunter` 

            Args:
                subreddit (str): for a reddit submission, dealFinder (praw.Reddit)
            Exceptions:
                None
            """
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

        def _get_game_deals(self, count: int, method) -> dict[str, str]:
            """Function for creating refs of posts + post links

            Args:
                count (int):  for # of results, method (praw.models.Subreddit): method ref for PRAW Subreddit instance
            Output: 
                result (dict): of posts + post links
            Exceptions:
                None 
            """
            try: 
                result = [(f"[{submission.id}]{submission.title}", f"https://www.reddit.com{submission.permalink}")
                        for submission in method(limit=count)]
            except: 
                traceback.print_exc()
            return dict(result)

        def _get_game_deals_func(self, method):
            """Function to trigger _get_game_deals()

            Args:
                method (praw.models.Subreddit): method ref for PRAW Subreddit instance
            Output: 
                Invocation result of _get_game_deals
            Exceptions:
                None 
            """
            return lambda count : self._get_game_deals(count, method)

        def is_valid_action(self, action: str):
            """Function to check if input is a valid subreddit action 

            Args:
                action (str): action being checked
            Output: 
                Boolean
            Exceptions:
                None 
            """
            return action in self.commandToCall.keys()

        def search_sub(self, time: str, query: str): 
            """Function to search a subreddit based on a given query + time range 

            Args:
                time (str): time range, query (str):  query to search
            Output: 
                Reference of posts + post links
            Exceptions:
                TBD 
                
            TODO : Want to see if I can factor this so it can follow call
            pattern for the dict/lambda invocation
            """
            try:
                result = [(f"[{submission.id}]{submission.title}", f"https://www.reddit.com{submission.permalink}")
                        for submission in self.sub.search(query=query, time_filter=time, limit=5)]
            except ValueError:
                traceback.print_exc()
                return None
            return dict(result)