from zope.interface import Interface

class IStatisticProvider(Interface):
    def columns(): pass
    def items(): pass
    def update(): pass
    def rows(): pass
