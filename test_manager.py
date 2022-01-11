import json

class classic_mcq:
    def get_test_metadata(test_id):
        data_path="data/test_db/classic_mcq/"
        with open(data_path+'test_data/metadata.json') as f:
            data = json.loads(f.read())
        try:
            test_metadata = data[test_id]
            return test_metadata
        except KeyError:
            return False

if __name__ == '__main__':
    print(classic_mcq.get_test_metadata("fd794f"))
