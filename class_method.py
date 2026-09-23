class User:

    def __init__(self, name):
        self._name = name

    # Instance method
    def get_name(self):
        return self._name

    # Class method
    @classmethod
    def from_string(cls, data):
        '''
        Create a User instance from a string containing the user's name.
        Args:
            data (str): A string containing the user's name.
        Returns:
            User: A new User instance created from the provided string.
        '''
        return cls(data)

    # Static method
    @staticmethod
    def validate_name(name):
        return bool(name.strip())

    # property
    @property
    def name(self):
        return self._name

obj = User("Alice")
print(obj.get_name())
print(User.validate_name("Alice"))
print(User.from_string("Bob").get_name())
print(obj.name)
