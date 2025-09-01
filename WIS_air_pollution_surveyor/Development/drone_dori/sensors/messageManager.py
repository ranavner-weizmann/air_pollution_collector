class MessageManager():
    initialString = "^^"
    endingString=";;"
    @staticmethod
    def create_message(operationNumber: int, additionalParameters: list) -> str:
        additionalParametersStrings = [str(parameter) for parameter in additionalParameters]
        return f"{MessageManager.initialString}{operationNumber}|{','.join(additionalParametersStrings)}{MessageManager.endingString}\n"
    @staticmethod
    def message_valid(message: str) -> bool:
        return message[:2] == MessageManager.initialString and message[-2:] == MessageManager.endingString