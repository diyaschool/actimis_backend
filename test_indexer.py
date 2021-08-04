import json

def read_db():
    try:
        with open('data/test_db/index.db') as f:
            data = f.read()
        return json.loads(data)
    except FileNotFoundError:
        return []

def get_by_id(test_id):
    data = read_db()
    for test in data:
        if test[0].lower() == test_id.lower():
            return {"test_id": user[0], 'tags': user[1]}
    return False

def write_by_id(test_id, data):
    old_data = get_by_id(test_id)
    for key in data:
        old_data[key] = data[key]
    all_data = read_db()
    for test in all_data:
        if test[0].lower() == test_id.lower():
            test[0] = old_data['test_id']
            test[1] = old_data['tags']
    with open('data/test_db/index.db', 'w') as f:
        f.write(json.dumps(all_data))

def list_data():
    output_data = []
    data = read_db()
    for test in data:
        output_data.append({'test_id': test[0], 'tags': test[1]})
    return output_data

def new_test(test_id, tags):
    if get_by_id(test_id) != False:
        return (False, "test_id already exists")
    all_data = read_db()
    all_data.append([test_id, tags])
    with open('data/test_db/index.db', 'w') as f:
        f.write(json.dumps(all_data))
    return (True, all_data)

def del_test(test_id):
    if get_by_id(test_id) == False:
        return False
    all_data = read_db()
    for i, test in enumerate(all_data):
        if test[0].lower() == test_id:
            all_data.pop(i)
            break
    with open('data/test_db/index.db', 'w') as f:
        f.write(json.dumps(all_data))
