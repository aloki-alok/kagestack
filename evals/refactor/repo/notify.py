from handlers import notify_user


def welcome(user):
    return notify_user(user, f"welcome, {user['name']}")
