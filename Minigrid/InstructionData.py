import json
import os
from datetime import datetime



class JsonArrayStorage:
    def __init__(self, filename):
        self.filename = filename
        self.initialize_json_file()

    def initialize_json_file(self):
        """ Initialize a JSON file with an empty dictionary if it doesn't exist. """
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump({}, f)

    def save_array(self, array):
        """ Save the given array to the JSON file with a unique timestamp key. """
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump({}, f)
        key = datetime.now().strftime('%Y%m%d%H%M%S%f')
        try:
            with open(self.filename, 'r+') as f:
                data = json.load(f)
                data[key] = array
                f.seek(0)
                json.dump(data, f, indent=4)
        except json.JSONDecodeError:
            # Handle case where file is not a valid JSON (shouldn't happen normally)
            with open(self.filename, 'w') as f:
                json.dump({key: array}, f, indent=4)

        return key

    def retrieve_array(self, key):
        """ Retrieve an array by its unique key. """
        with open(self.filename, 'r') as f:
            data = json.load(f)
            return data.get(key, None)
