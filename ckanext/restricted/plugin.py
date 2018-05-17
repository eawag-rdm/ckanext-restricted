import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckanext.restricted import helpers
from ckanext.restricted import logic
from ckanext.restricted import auth
from ckanext.restricted import action
# from json import dumps, loads

from logging import getLogger
log = getLogger(__name__)

_get_or_bust = tk.get_or_bust

def restricted_get_user_id():
    return tk.c.user

class RestrictedPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic', 'restricted')

    # IActions
    def get_actions(self):
        return {'resource_view_list': action.restricted_resource_view_list,
                'package_show': action.restricted_package_show,
                'resource_search': action.restricted_resource_search,
                'package_search': action.restricted_package_search}

    # ITemplateHelpers
    def get_helpers(self):
        return { 'restricted_get_user_id': restricted_get_user_id}

    # IAuthFunctions
    def get_auth_functions(self):
        return { 'resource_show': auth.restricted_resource_show,
                 'resource_view_show': auth.restricted_resource_show
               }
    # IRoutes
    def before_map(self, map_):
        map_.connect(
            'restricted_request_access',
            '/dataset/{package_id}/restricted_request_access/{resource_id}',
            controller='ckanext.restricted.controller:RestrictedController',
            action = 'restricted_request_access_form'
        )
        return map_

    # IResourceController
    def before_update(self, context, current, resource):
        if tk.asbool(
                tk.config.get(
                    'ckanext.restricted.notify_allowed_users', 'False')):
            context['__restricted_previous_value'] = current.get('allowed_users')

    def after_update(self, context, resource):
        if tk.asbool(
                tk.config.get(
                    'ckanext.restricted.notify_allowed_users', 'False')):
            previous_value = context.get('__restricted_previous_value')
            resource['package_name'] = context.get('package').name
            logic.restricted_notify_allowed_users(previous_value, resource)

