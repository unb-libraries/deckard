class ResponseProcessor:
    TRIPWIRE_TERMS = [
        'fraggle'
    ]

    def __init__(self, response: str) -> None:
        self.response = response
        self.tripwire_thrown = False
        if self.response is None or self.response == '':
            return
        self.setCleanResponse()
        self.testTripWire()

    def testTripWire(self) -> None:
        self.tripwire_thrown = False
        for term in self.TRIPWIRE_TERMS:
            if term in self.response:
                self.tripwire_thrown = True

    def setCleanResponse(self) -> None:
        self.response = self.response.strip()

    def tripWireThrown(self) -> bool:
        return self.tripwire_thrown

    def getResponse(self) -> str:
        return self.response
