import yaml

class Params:
    def __init__(self):
        self.params = None
        # with open('D:\\MOCAP\\Scripts\\TakeRecorderUE\\version2\\configMageGuy.yaml', 'r') as file:
        with open('D:\\MOCAP\\Scripts\\TakeRecorderUE\\version2\\config.yaml', 'r') as file:
        # with open('D:\\MOCAP\\Scripts\\TakeRecorderUE\\version2\\configWitch.yaml', 'r') as file:
            self.params = yaml.safe_load(file)

    def get(self):
        return self.params
