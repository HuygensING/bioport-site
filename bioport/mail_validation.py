from formencode.validators import Email
from formencode.api import Invalid

def check_email(email):
    try:
        Email().to_python(email)
        return True
    except Invalid, error:
        return False
