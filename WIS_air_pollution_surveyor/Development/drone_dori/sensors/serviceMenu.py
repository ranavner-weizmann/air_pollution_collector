import sys
import select
from abc import ABC, abstractmethod
from messageManager import MessageManager

class MenuCommand(ABC):
    def __init__(self, name: str, deviceName: str) -> None:
        self._name = name
        self._deviceName = deviceName
    
    @abstractmethod
    def create_message(self) -> str:
        ...
    def get_name(self) -> str:
        return self._name
    def get_device_name(self) -> str:
        return self._deviceName

class ArduinoCommand(MenuCommand):
    def __init__(self, name: str, arduinoCommandNumber: int) -> None:
        super().__init__(name, "mceasArduino")
        self._arduinoCommandNumber = arduinoCommandNumber


class TECSetTemperatureMenuCommand(ArduinoCommand):
    def __init__(self) ->None:
        super().__init__("TEC - Change temperature 🌡️", 1)

    def create_message(self) -> str:
        while True:
            try:
                tecInstance = int(input("What tec instance do you want to change?"))
                break
            except ValueError as error:
                print("please enter int value.")
                continue
        while True:
            try:
                newTemperature = float(input("What should be the new temperature?"))
                break
            except ValueError as error:
                print("please enter float value.")
                continue
        

        return MessageManager.create_message(self._arduinoCommandNumber, [newTemperature, tecInstance])
    
class PWRSetTemperatureMenuCommand(ArduinoCommand):
    def __init__(self) ->None:
        super().__init__("PWR - Change temperature 🌡️", 2)

    def create_message(self) -> str:
        while True:
            try:
                newTemperature = float(input("What should be the new temperature?"))
                break
            except ValueError as error:
                print("please enter float value.")
                continue
        

        return MessageManager.create_message(self._arduinoCommandNumber, [newTemperature])

class ServiceMenu():
    def __init__(self) -> None:
        self._commandsList = []
        self._commandsList.append(TECSetTemperatureMenuCommand())
        self._commandsList.append(PWRSetTemperatureMenuCommand())


    def should_start(self) -> bool:
        ready, _, _ = select.select([sys.stdin], [], [], 0.0)
        if ready:
            _= sys.stdin.readline().strip()
            return True
        else:
            return False
    def start(self) -> "tuple[str]":
        self.print_menu()
        chosenOption = int(input("Please enter your choice or 0 to cancel"))
        if chosenOption == 0:
            return
        command = self._commandsList[chosenOption - 1]
        arduinoString = command.create_message()
        processName = command.get_device_name()
        return (processName, arduinoString)

    def print_menu(self) -> None:
        print("================================================")
        print("🛠️  🛠️  🛠️  ========SERVICE MENU======== 🛠️  🛠️  🛠️")
        print("================================================")
        for i, action in enumerate(self._commandsList):
            print(f"{i + 1}. {action._name}.")
        
        