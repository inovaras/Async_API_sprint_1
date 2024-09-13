"""SOLID
S - SRP - принцип единой ответственности.
O - OCP - принцип открытости для расширения и закрытости для изменения.
L - LSP - принцип подстановки Барбары Лисков.
I - ISP - принцип разделения интерфейсов.
D - DIP - вышестоящие и нижестоящие классы должны зависеть от интерфейсов/абстракций.
"""

from abc import ABC, abstractmethod
from msilib.schema import PublishComponent


# SRP
class Auto():
    def drive():
        pass

    # нарушение SRP
    def print():
        pass

# OCP
class Auto():
    # удалить drive нельзя, это изменение
    def drive():
        pass

    # добавить новый метод можно, это расширение
    def driveFast():
        pass

# LSP
class File():
    def write():
        # print to console.
        pass

class PdfFile(File):
    def write():
        # print to pdf.
        pass

# ISP - это миксины в python
class SwimMixin():
    def swim():
        pass

class RunMixin():
    def run():
        pass

class DoorWorker():
    def open():
        pass
    def close():
        pass
    def ring():
        pass

class Life(SwimMixin, RunMixin):
    def create(obj):
        obj.run()
        obj.swim()

# DIP - псевдокод
class Weapon(ABC):
    @abstractmethod
    def shoot(self):
        pass

class Laser(Weapon):
    def shoot(self):
        print("piu piu")

class Bazuka(Weapon):
    def shoot(self):
        print("bada boom")

class Hero(Bazuka):
    def fight(self):
        self.shoot()

if __name__ == "__main__":
    hero1 = Hero()
    hero1.fight()

