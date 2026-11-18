def format_phone(number):
    if number is None:
        return None
    digits = "".join(c for c in number if c.isdigit())
    if digits is None:
        return None
    return "+" + digits


def _old_format_phone(number):
    return "+" + number.replace("-", "")


def send_email(to, body):
    if not to:
        return None
    return {"channel": "email", "to": to, "body": body}


def send_sms(to, body):
    return {"channel": "sms", "to": format_phone(to), "body": body}


def send_sms_legacy(to, body):
    return {"channel": "sms", "to": format_phone(to), "body": body[:160]}


def _notify(user, message):
    if user.get("email"):
        return send_email(user["email"], message)
    return send_sms(user["phone"], message)


def notify_user(user, message):
    return _notify(user, message)
