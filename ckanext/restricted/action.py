from ckan.lib.base import render_jinja2
from ckan.lib.mailer import mail_recipient
from ckan.lib.mailer import MailerException
import ckan.logic
from ckan.logic.action.create import user_create
from ckan.logic import side_effect_free, check_access
from ckan.logic.action.get import package_show, resource_show, resource_view_list, resource_search, package_search
import ckan.logic.auth as logic_auth
import ckan.authz as authz
from ckanext.restricted import helpers
from ckanext.restricted import logic
from ckanext.restricted import auth

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

from logging import getLogger
log = getLogger(__name__)

NotFound = ckan.logic.NotFound

_get_or_bust = ckan.logic.get_or_bust

@side_effect_free
def restricted_resource_view_list(context, data_dict):
    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    resource = model.Resource.get(id)
    if not resource:
        raise NotFound
    authorized = auth.restricted_resource_show(context, {'id':resource.get('id'), 'resource':resource }).get('success', False)
    if not authorized:
        return []
    else:
        return resource_view_list(context, data_dict)

@side_effect_free
def restricted_package_show(context, data_dict):

    package_metadata = package_show(context, data_dict)

    # Ensure user who can edit can see the resource
    if authz.is_authorized('package_update', context, package_metadata).get('success', False):
        return package_metadata

    # Custom authorization
    if (type(package_metadata) == type(dict())):
        restricted_package_metadata = dict(package_metadata)
    else:
        restricted_package_metadata = dict(package_metadata.for_json())

    restricted_package_metadata['resources'] = _restricted_resource_list_url(context, restricted_package_metadata.get('resources',[]))

    return (restricted_package_metadata)


@side_effect_free
def restricted_resource_search(context, data_dict):
    resource_search_result = resource_search(context, data_dict)

    restricted_resource_search_result = {}

    for key,value in resource_search_result.items():
        if key == 'results':
            restricted_resource_search_result[key] = _restricted_resource_list_url(context, value)
        else:
            restricted_resource_search_result[key] = value

    return restricted_resource_search_result

@side_effect_free
def restricted_package_search(context, data_dict):
    package_search_result = package_search(context, data_dict)

    restricted_package_search_result = {}

    for key,value in package_search_result.items():
        if key == 'results':
            restricted_package_search_result_list = []
            for package in value:
                restricted_package_search_result_list += [restricted_package_show(context,{'id':package.get('id')})]
            restricted_package_search_result[key] = restricted_package_search_result_list
        else:
            restricted_package_search_result[key] = value

    return restricted_package_search_result

def _restricted_resource_list_url(context, resource_list):
    restricted_resources_list = []
    for resource in resource_list:
        authorized = auth.restricted_resource_show(context, {'id':resource.get('id'), 'resource':resource}).get('success', False)
        restricted_resource = dict(resource)
        if not authorized:
            restricted_resource['url'] = 'Not Authorized'
        restricted_resources_list += [restricted_resource]
    return restricted_resources_list
