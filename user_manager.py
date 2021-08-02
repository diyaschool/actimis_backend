from db_manager import *
import json
import getch
import hashlib
import base64

def are_you_sure():
    while 1:
        print('Are you sure? [y/n] ')
        sure = getch.getch().lower()
        if sure == 'y':
            return True
        elif sure == 'n':
            return False
        else:
            print('Input unrecognized.\n')

def create(username, password, name, tags, email):
    password = base64.b64encode(hashlib.sha256(password.encode()).digest()).decode()
    db_put('auth', username, {'password': password, 'tags': tags, 'email': email})

def get(username):
    return db_get("auth", username)

if __name__ == '__main__':
    while 1:
        mode = input('Command? [put/get/del/list]: ')
        if mode == 'put':
            username = input('Username: ')
            password = input('Password: ')
            name = input('Name: ')
            tags = input("Tags: ")
            tags = tags.replace(' ', '').split(',')
            email = input("Email: ").strip()
            if are_you_sure():
                create(username, password, name, tags, email)
                print('Done.')
            else:
                print('Not modified.')
        elif mode == 'get':
            username = input('Username: ')
            data = db_get('auth', username)
            print(data)
        elif mode == 'del':
            username = input('Username: ')
            if are_you_sure():
                data = db_del('auth', username)
                print('Done.')
            else:
                print('Not modified.')
        elif mode == 'list':
            print(db_list('auth'))
        else:
            print('Not recognized.')
        print()
