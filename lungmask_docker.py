
class Lungmask:

    def apply(self, *args, **kwargs):

        print("### lungmask.apply called with args {} and kwargs {}".format(args, kwargs))

    def get_model(self, *args, **kwargs):
        print("### lungmask.get_model called with args {} and kwars{}".format(args, kwargs))

class Utils:
    def get_input_image(self, *args, **kwargs):
        print("### utils.get_input_image called with args {} and kwargs {}".format(args, kwargs))


lungmask = Lungmask()
utils = Utils()