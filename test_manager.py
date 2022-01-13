import json

class classic_mcq:
    def get_test_metadata(test_id):
        try:
            with open("data/test_db/classic_mcq/test_data/metadata.json") as f:
                data = json.loads(f.read())
        except FileNotFoundError:
            return None
        try:
            test_metadata = data[test_id]
            return test_metadata
        except KeyError:
            return False
    def get_user_session(session_id):
        try:
            with open(f"data/test_db/classic_mcq/user_sessions/{session_id}.json") as f:
                data = json.loads(f.read())
        except FileNotFoundError:
            return False
        return data
    def write_user_session(session_id, data):
        try:
            with open(f"data/test_db/classic_mcq/user_sessions/{session_id}.json", "w") as f:
                f.write(json.dumps(data))
        except FileNotFoundError:
            return False

if __name__ == '__main__':
    print(classic_mcq.get_test_metadata("fd794f"))
