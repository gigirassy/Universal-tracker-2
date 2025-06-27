import json

class Leaderboard:
    """Stores how much data, and how many items a user has completed"""

    def __init__(self):
        self.usernames = {}

    def additem(self, username, itemsize):
        """Adds an item, and it's size to the downloader's leaderboard entry"""

        try:
            # Add one item to leaderboard entry
            self.usernames[username]['items'] += 1

        except KeyError: # Username does not exist in leaderboard
            self.usernames[username] = {} # Create entry for username
            self.usernames[username]['items'] = 1
            self.usernames[username]['data'] = 0

            # Add size of completed item to leaderboard entry
        self.usernames[username]['data'] += itemsize

    def get_leaderboard(self):
        """return the entire leaderboard"""

        return json.dumps(self.usernames)

    def get_user_stats(redis_conn, downloader_name):
    """
    Return dict with total items, total bytes, and time-series chart data for a given downloader.
    """
    items = redis_conn.hget("downloader_count", downloader_name) or 0
    bytes_ = redis_conn.hget("downloader_bytes", downloader_name) or 0
    chart = redis_conn.lrange(f"downloader_chartdata:{downloader_name}", 0, -1)
    # parse chart entries ("[timestamp,bytes]")
    chart_data = [json.loads(x) for x in chart]
    return {
        "downloader": downloader_name,
        "items": int(items),
        "bytes": int(bytes_),
        "chart": chart_data
    }


    def loadfile(filepath):
        """Get leaderboard stats from save file"""

        with open(filepath, 'r') as ljf:
            self.usernames = json.loads(ljf.read)
