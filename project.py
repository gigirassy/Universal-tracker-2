from threading import Timer
import json
import os

import item_manager
import leaderboard


class Project:
    """Keep track of items for a project"""

    def __init__(self, config_file):
        self.items = item_manager.Items()                # Create items object
        self.leaderboard = leaderboard.Leaderboard()     # Create leaderboard object
        self.config_path = config_file

        with open(config_file, 'r') as jf:               # Open project config file
            configfile = json.loads(jf.read())           # Load project config
            self.meta = configfile['project-meta']
            self.status = configfile['project-status']
            self.automation = configfile['automation']

        # Get item files
        self.items_folder = os.path.join('projects', self.meta['items-folder'])
        self.item_files = []
        for file in os.listdir(self.items_folder):
            if file.endswith('.txt'):
                self.item_files.append(file)
        self.item_files.sort()

        if not self.status['paused']:
            self.queue_next_items()

        # Check if there is a leaderboard json file
        leaderboard_json_file = os.path.join(
            'projects', f"{self.meta['name']}-leaderboard.json"
        )
        if os.path.isdir(leaderboard_json_file):
            # Load leaderboard stats from file
            self.leaderboard.loadfile(leaderboard_json_file)

        Timer(30, self.saveproject).start()  # Start saving project every 30s

    def saveproject(self):
        """Save project files every 30 seconds"""
        if not self.status['paused']:
            # Save queue state
            with open(os.path.join(self.items_folder, '.queue-save.txt'), 'w') as f:
                f.write(self.items.dumpfile())
            # Save leaderboard
            with open(os.path.join(
                    'projects', f"{self.meta['name']}-leaderboard.json"
                 ), 'w') as ljf:
                ljf.write(self.leaderboard.get_leaderboard())
        Timer(30, self.saveproject).start()

    def update_config_file(self):
        """Write changed config back to the config file"""
        configfile = {
            'project-meta': self.meta,
            'project-status': self.status,
            'automation': self.automation
        }
        with open(self.config_path, 'w') as jf:
            jf.write(json.dumps(configfile))

    def queue_next_items(self):
        """Get next items file, and load it into queue"""
        try:
            items_file = os.path.join(
                'projects',
                self.meta['items-folder'],
                self.item_files.pop(0)
            )
            self.items.loadfile(items_file)
            print(f'Added {os.path.basename(items_file)} to the queue.')
        except IndexError:
            pass
        os.remove(items_file)

    # Wrappers for various tasks

    def get_item(self, username, ip):
        if len(self.items.queue_items) == 0:
            self.queue_next_items()
        if not self.status['paused']:
            return self.items.getitem(username, ip)
        else:
            return "ProjectNotActive"

    def heartbeat(self, id, ip):
        return self.items.heartbeat(id, ip)

    def finish_item(self, id, itemsize, ip):
        # ← modified: pass size before ip
        done_stat = self.items.finishitem(id, itemsize, ip)
        if done_stat not in ['IpDoesNotMatch', 'InvalidID']:
            # done_stat == ('Success', username)
            username = done_stat[1]
            self.leaderboard.additem(username, itemsize)
            return done_stat[0]
        else:
            return done_stat

    def get_leaderboard(self):
        return self.leaderboard.get_leaderboard()

    def get_user_stats(self, username):            # ← added
        """Delegate per-user stats lookup to item manager."""
        return self.items.get_user_stats(username)
