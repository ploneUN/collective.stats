from zope.interface import implements, Interface

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from collective.stats import statsMessageFactory as _

def isStringType(data):
    return isinstance(data, str) or isinstance(data, unicode)

class ITimelineView(Interface):
    """
    Timeline view interface
    """

    def test():
        """ test method"""


class TimelineView(BrowserView):
    """
    Timeline browser view
    """
    implements(ITimelineView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def attrvals(self,items,attr):
        for item in items:
            val = getattr(item,attr,
                           getattr(item.getObject(),attr,None))
            if callable(val):
               val = val()

            if val:
               if type(val) == str:
                  yield val

               elif iter(val):
                  for i in val:
                      yield i

    def filterResults(self,**filters):
        query = self.context.buildQuery()
        query.update(filters)
        catalog = getToolByName(self.context,'portal_catalog')
        return catalog(query)
