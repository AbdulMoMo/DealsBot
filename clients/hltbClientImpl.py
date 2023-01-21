from howlongtobeatpy import HowLongToBeat

class hltb_hunter():

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
        return None