from zope.interface import Interface
from zope.interface import implements

from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from zope import schema
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from collective.stats import statsMessageFactory as _

from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget
from Products.ATContentTypes.interface import IATTopic
from plone.memoize.instance import memoize
from plone.memoize import ram
from persistent.dict import PersistentDict

from zope.interface import alsoProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary,SimpleTerm


from zope.component import getMultiAdapter
from Products.CMFCore.utils import getToolByName
from collective.stats import util
from time import time
from Acquisition import aq_base

import Missing

def IndexesVocabulary(context):
    portal_catalog = getToolByName(context,'portal_catalog')
    terms = [SimpleVocabulary.createTerm(i) for i in portal_catalog.indexes()]
    return SimpleVocabulary(terms)

alsoProvides(IndexesVocabulary,IVocabularyFactory)


class ISimpleKeywordStatisticPortlet(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    # TODO: Add any zope.schema fields here to capture portlet configuration
    # information. Alternatively, if there are no settings, leave this as an
    # empty interface - see also notes around the add form and edit form
    # below.

    # some_field = schema.TextLine(title=_(u"Some field"),
    #                              description=_(u"A field to use"),
    #                              required=True)
    header = schema.TextLine(title=_(u"Portlet header"),
                             description=_(u"Title of the rendered portlet"),
                             required=True)

    target_collection = schema.Choice(title=_(u"Target collection"),
                                  description=_(u"Find the collection which provides the items to list"),
                                  required=True,
                                  source=SearchableTextSourceBinder({'object_provides' : IATTopic.__identifier__},
                                                                    default_query='path:'))

    # FIXME: this should be a choice field
    attr = schema.Choice(title=_(u"Index Name"),
                               description=_(u"Field would you want to do produce statistic on"),
                               required=True,
                               vocabulary="collective.stats.IndexesVocabulary")


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(ISimpleKeywordStatisticPortlet)

    # TODO: Set default values for the configurable parameters here

    # some_field = u""

    # TODO: Add keyword parameters for configurable parameters here
    # def __init__(self, some_field=u"):
    #    self.some_field = some_field

    def __init__(self,header,target_collection,attr):
        self.header = header
        self.target_collection = target_collection
        self.attr = attr

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return self.header

# 24hrs:1900UTC
cacheperiod = lambda *args: (time() + (60 * 60 * 5)) // (60*60*24) 

def renderer_cache(assignment, funcname, func):
    key = '.'.join([assignment.target_collection, 
                    assignment.attr,
                    funcname])
    instance = aq_base(assignment)
    if getattr(instance, '_statscache', None) is None:
        instance._statscache = PersistentDict()
    CACHE = instance._statscache
    CACHE.setdefault(key, PersistentDict({'time':0,'value':None}))
    time = cacheperiod()
    if CACHE[key]['time'] == time:
        return CACHE[key]['value']

    result = func()
    CACHE[key]['time'] = time
    CACHE[key]['value'] = result
    return result
        

class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('simplekeywordstatisticportlet.pt')

    def top(self):
        return renderer_cache(self.data, 'top', self._top)

    def _top(self):
        result = []
        for i in util.mostcommon(self.items()):
            result.append({'elem':i[0],'count':i[1]})
        return result

    def items(self):
        return renderer_cache(self.data, 'items', self._items)

    def _items(self):
        result = []
        collection = self.collection()
        if collection:
            for item in collection.queryCatalog():
   
                attr = getattr(item, self.data.attr, None)

                if attr == None or attr == Missing.Value:
                    indexdata = self.context.portal_catalog.getIndexDataForRID(
                                        item.getRID())
                    attr = indexdata.get(self.data.attr, None)

                if attr == None:
                    attr = getattr(
                        item.getObject(), 
                        self.data.attr,
                        None
                    )

                if callable(attr):
                    attr = attr()

                if attr:
                    if type(attr) == str:
                        result.append(attr)

                    elif iter(attr):
                        for i in attr: 
                            result.append(i)
        return result
   

    @memoize
    def collection(self):
        """ get the collection the portlet is pointing to"""

        # taken from plone.portlet.collection

        collection_path = self.data.target_collection
        if not collection_path:
            return None

        if collection_path.startswith('/'):
            collection_path = collection_path[1:]

        if not collection_path:
            return None

        portal_state = getMultiAdapter((self.context, self.request), name=u'plone_portal_state')
        portal = portal_state.portal()
        return portal.restrictedTraverse(collection_path, default=None)


# NOTE: If this portlet does not have any configurable parameters, you can
# inherit from NullAddForm and remove the form_fields variable.

class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """

    form_fields = form.Fields(ISimpleKeywordStatisticPortlet)
    form_fields['target_collection'].custom_widget = UberSelectionWidget

    def create(self, data):
        return Assignment(**data)


# NOTE: IF this portlet does not have any configurable parameters, you can
# remove this class definition and delete the editview attribute from the
# <plone:portlet /> registration in configure.zcml

class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """

    form_fields = form.Fields(ISimpleKeywordStatisticPortlet)
    form_fields['target_collection'].custom_widget = UberSelectionWidget

