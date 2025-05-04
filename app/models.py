
class user:
    def __init__(self, email, password):
        self.email = email
        self.password = password

    #to store in sessions must be of a primitive form
    def to_dict(self):
        return {
            'email': self.email,
            'password': self.password,
        }
