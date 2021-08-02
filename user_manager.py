import json
import auth_db_manager
import index_db_manager
import getch

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
    print(auth_db_manager.new_user(username, password, name, email, tags))
    print(index_db_manager.new_user(username, "NOT_SIGNED_IN_YET", email, tags))

# def get(username):
#     return

if __name__ == '__main__':
    while 1:
        mode = input('Command? [create/get/del/list/edit]: ')
        if mode == 'create':
            username = input('Username: ')
            password = input('Password: ')
            name = input('Name: ')
            tags = input("Tags: ")
            tags = tags.replace(' ', '').split(',')
            email = input("Email: ").strip()
            if are_you_sure():
                create(username, password, name, tags, email)
            else:
                print('Not modified.')
        elif mode == 'del':
            username = input('Username: ')
            if are_you_sure():
                if index_db_manager.del_user(username) == False:
                    print('username not found')
                if auth_db_manager.del_user(username) == False:
                    print('username not found')
            else:
                print('Not modified.')
        # elif mode == 'get':
        #     username = input('Username: ')
        #     data = db_get('auth', username)
        #     print(data)
        print()
