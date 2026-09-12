class User:

    def __init__(self, name):
        self.name = name

    # Instance method
    def get_name(self):
        return self.name

    # Class method
    @classmethod
    def from_string(cls, data):
        return cls(data)

    # Static method
    @staticmethod
    def validate_name(name):
        return bool(name.strip())

obj = User("Alice")
print(obj.get_name())
print(User.validate_name("Alice"))
print(User.from_string("Bob").get_name())