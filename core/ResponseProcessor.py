class ResponseProcessor:
    TRIPWIRE_TERMS = [
        'fraggle'
    ]

    def __init__(self, response):
        self.response = response
        self.tripwire_thrown = False
        if self.response is None or self.response == '':
            return
        self.setCleanResponse()
        self.testTripWire()

    def testTripWire(self):
        self.tripwire_thrown = False
        for term in self.TRIPWIRE_TERMS:
            if term in self.response:
                self.tripwire_thrown = True

    def setCleanResponse(self):
        self.response = self.response.strip()

    def tripWireThrown(self):
        return self.tripwire_thrown

    def getResponse(self):
        return self.response
