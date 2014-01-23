from zope.interface import implements
from zope.component import adapts
from Products.ATContentTypes.interface.topic import IATTopic
from interfaces import IStatisticProvider
from Products.CMFCore.utils import getToolByName
from collective.stats import util

class CollectionStats(object):
    implements(IStatisticProvider)
    adapts(IATTopic)

    def __init__(self,context,summation=False):
        self.context = context
        self.summation = summation
        self.update()

    def items(self,attr,dateattr='created',dateformat=None,filter={}):
        query = self.context.buildQuery()
        query.update(filter)
        catalog = getToolByName(self.context,'portal_catalog')
        for item in catalog(query):
               value = getattr(item,attr,
                              getattr(item.getObject(),attr,None))

               if callable(value):
                  value = attr()

               date = getattr(item,dateattr,
                              getattr(item.getObject(),dateattr,None))
               if callable(date):
                  date = date()

               if dateformat:
                  date = date.strftime(dateformat)
               else:
                  date = date.ISO8601()

               if value:
                  if type(value) == str:
                       yield (date,value)

                  elif getattr(value,'strftime',None):
                       yield (date,value.ISO8601())

                  elif iter(value):
                     for i in value:
                         yield (date,i)


    def update(self):
        data = {}
        # FIXME: this MUST be configurable
        # attr field should give selection of available indexes
        # filter field should give selection to filter by result data, or take from REQUEST
        # datefield need to be configurable too
        for key,val in self.items('youthnet_theme',dateformat="%Y-%m"):
            if data.get(key,None):
               data[key].append(val)
            else:
               data[key] = [val]

        self.data = data


    def columns(self):
        retval = []
        for i in self.data.values():
            for j in i:
                if not (j in retval):
                   retval.append(j)
        retval.sort()
        return retval

    def rows(self):
        keys = self.data.keys()
        data = self.data
        keys.sort()
        if self.summation:
           sum = {}
           for d in keys:
               datadict = dict(util.mostcommon(data[d]))
               for c in self.columns():
                   sum[c] = sum.get(c,0) + datadict.get(c,0)
                   datadict[c] = sum[c]
               datadict['DateTime'] = d
               yield datadict
        else:
           for d in keys:
               datadict = dict(util.mostcommon(data[d]))
               datadict['DateTime'] = d
               yield datadict


