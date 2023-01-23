from howlongtobeatpy import HowLongToBeat

class hltb_hunter():

    FORMAT_GAME_ATTR = {
        'game_name': 'Name',
        'game_type': 'Type',
        'game_web_link': 'HLTB Link',
        'review_score': 'Score',
        'profile_dev': 'Developer',
        'release_world': 'Release Year',
        'main_story': 'Main Story',
        'main_extra': 'Main + Extra',
        'completionist': 'Completionist',
        'all_styles': 'All Styles'
    }

    # Constructor for reddit_hunter
    # Inputs: None
    # Outputs: None
    # Exceptions: None
    def __init__(self) -> None:
        self.hltbClient = HowLongToBeat()

    # Note: Ref for HTLB Entry: https://github.com/ScrappyCocco/HowLongToBeat-PythonAPI/blob/master/howlongtobeatpy/howlongtobeatpy/HowLongToBeatEntry.py
    def search(self, query: str) -> HowLongToBeat:
        results = self.hltbClient.search(query)
        if results is not None and len(results) > 0:
            best_match: HowLongToBeat = max(results, key=lambda element: element.similarity)
            # TODO: Sort attr to populate results for making a thread
            best_match_attr = best_match.__dict__.keys()
            # TODO: Doing dict comprehension wrong need to fix this
            result: dict[str, str] = [[self.FORMAT_GAME_ATTR[key], best_match.key] for key in best_match_attr if key in self.FORMAT_GAME_ATTR]
            print(result)
            return result
        return None