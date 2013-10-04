import time


class TestPlayer():
    def __init__(self):
        self.scenes = [3, 2, 1, 3, 4]
        self.sceneTot = sum(self.scenes)

    def run(self):
        currentTime = 3299923.9
        startTime = currentTime - 3.2

        speed = 1.0
        steps = 5.0

        while True:
            timeAfterStart = currentTime - startTime
            sceneTime = round(timeAfterStart % self.sceneTot, 2)

            self.update(sceneTime)

            currentTime += speed / steps
            time.sleep(speed / steps)

    def update(self, sceneTime):
        print sceneTime


if __name__ == "__main__":
    player = TestPlayer()
    player.run()