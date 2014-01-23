from zope.interface import implements, Interface

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from collective.stats import statsMessageFactory as _
from StringIO import StringIO
from collective.stats import util
from collective.stats.adapters.collectionstats import IStatisticProvider
import csv

import datetime

#FIXME: the datasource context processing code should be refactored to an adapter
         
class ITimeplotDataSourceView(Interface):
    """
    TimeplotDataSource view interface
    """


class TimeplotDataSourceView(BrowserView):
    """
    TimeplotDataSource browser view
    """
    implements(ITimeplotDataSourceView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def render(self):
        out = StringIO()
        stats = IStatisticProvider(self.context)
        keys = stats.data.keys()
        keys.sort()

        fields = ['DateTime'] + stats.columns()
        writer = csv.DictWriter(out,fields,0)

        # write header
        out.write("#\n# %s \n#\n\n" % self.context.Title())
        headrow = dict([(i,i) for i in fields])
        headrow['DateTime'] = '# DateTime'
        writer.writerow(headrow)
        # write data
        for row in stats.rows():
            writer.writerow(row)

        self.request.response.setHeader('Content-Type','text/plain')
        self.request.RESPONSE.setHeader('Content-Length',len(out.getvalue()))
        return out.getvalue()

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    __call__ = render
