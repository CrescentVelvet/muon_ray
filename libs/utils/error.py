class Error:
    def __init__(self, function, content):
        print("Function: ", function, "Contents:", content)
        self.function = function
        self.content = content