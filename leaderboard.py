# leaderboard.py

import time
import json

class Items:
    """Manage and keep track of items"""

    def __init__(self):
        self.queue_items = {}
        self.inprogress_items = {}
        self.done_items = 0

        # New: per-user statistics
        # username -> {'count': int, 'bytes': int}
        self.user_stats = {}  # ← added

        # Assign only one id per item
        self.current_id = 0

    def loadfile(self, file):
        """Open a csv file, and create one item per line"""

        with open(file, 'r') as jf:
            for line in jf.readlines():

                # Remove newline character from line
                line = line.replace('\n', '')

                # If line is not a comment, or empty
                if line.startswith('#') == False and line != '':

                    # Create item
                    self.queue_items[self.current_id] = {
                        'id': self.current_id,
                        'values': line.split(',')
                    }

                    self.current_id += 1  # Add one to the current id

    def dumpfile(self):
        """Save the current queue"""

        values = []
        value_str = ''

        # Extract values
        for key in self.queue_items:
            values.append(self.queue_items[key]['values'])

        for key in self.inprogress_items:
            values.append(self.inprogress_items[key]['values'])

        # Parse values into file
        for value in values:
            for arg in value:
                value_str += f'{arg},'  # Add value to line

            value_str = value_str.rstrip(',')  # Remove trailing ','
            value_str += '\n'  # Add newline

        return value_str

    def getitem(self, username, ip):
        """Gets an item, and moves it to inprogress_items"""

        try:
            # Get item with the lowest id from queue_items
            id = min(self.queue_items, key=int)
            item = self.queue_items.pop(id)

            # Add item to inprogress_items
            item['username'] = username  # Log username
            item['ip'] = ip              # Log ip
            item['times'] = {
                'starttime': int(time.time())
            }
            self.inprogress_items[id] = item

            print(f'giving id {id} to {username}')

            # Return json of item
            return json.dumps({'id': item['id'], 'values': item['values']})

        except ValueError:  # No items left
            return 'NoItemsLeft'

    def heartbeat(self, id, ip):
        """Logs heartbeat for item"""
        try:
            id = int(id)
            item = self.inprogress_items[id]

            if item['ip'] == ip:
                self.inprogress_items[id]['times']['heartbeat'] = int(time.time())
                return 'Success'
            else:
                return 'IpDoesNotMatch'

        except KeyError:
            return 'InvalidID'

    def finishitem(self, id, size, ip):  # ← modified: accept size as second parameter
        """Removes item from inprogress_items and records stats"""
        try:
            id = int(id)
            item = self.inprogress_items[id]

            if item['ip'] != ip:
                return 'IpDoesNotMatch'

            # Remove the item
            self.inprogress_items.pop(id)
            self.done_items += 1

            username = item['username']
            # Update per-user stats
            stats = self.user_stats.setdefault(username, {'count': 0, 'bytes': 0})
            stats['count'] += 1
            stats['bytes'] += size

            print(f"{username} finished {id} (size={size})")
            # Return success plus username for backward compatibility
            return ('Success', username)

        except KeyError:
            return 'InvalidID'

    def get_leaderboard(self):
        """Example existing leaderboard output (e.g. top finishers)"""
        # This is your existing implementation; no change required here
        pass

    def get_user_stats(self, username):  # ← added
        """Return JSON of stats for a given username"""
        stats = self.user_stats.get(username)
        if stats is None:
            return json.dumps({'error': 'No data for user'})
        return json.dumps({
            'username': username,
            'count': stats['count'],
            'bytes': stats['bytes']
        })
