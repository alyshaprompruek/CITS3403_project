
class user:
    def __init__(self, email, studentBoolean, password):
        self.email = email
        self.student = studentBoolean
        self.password = password

    #to store in sessions must be of a primitive form
    def to_dict(self):
        return {
            'email': self.email,
            'student': self.student,
            'password': self.password,
        }
