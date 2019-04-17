class Hello(object):

    def __init__(self, text):
        self.text = text

    def print(self):
        print('Hi {}'.format(self.text))
