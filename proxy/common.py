class IP(object):
    """Summary of class here.

    Longer class information....
    Longer class information....

    Attributes:
        proxy: str '{ip}:{port}'
        score: int quality of proxy,0 for useless
    """

    def __init__(self, proxy, score=1):
        self.proxy = proxy
        self.score = score
