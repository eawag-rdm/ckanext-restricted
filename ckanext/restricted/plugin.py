import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckanext.restricted import logic
from ckanext.restricted import auth
from ckanext.restricted import action
import ckanext.restricted.blueprints as blueprints
# from json import dumps, loads

from flask import Blueprint, request, render_template

from logging import getLogger
log = getLogger(__name__)

_get_or_bust = tk.get_or_bust

def restricted_get_user_id():
    return tk.c.user

def restricted_request_access_form(self, package_id, resource_id, data={},
                                   errors={}, error_summary={}):
    '''
    SRD 20220519 copied from controller.py for IBlueprint compliance
    '''
    user_id = toolkit.c.user

    if not user_id:
        toolkit.abort(401, _('Access request form is available to'
                                 ' logged in users only.'))

    if ('save' in request.params) and data and (not errors):
        return self._send_request(resource_id)
    print('\nrestricted_access_form data: {}\n'.format(data))
    if not data:
        user = toolkit.get_action('user_show')(None, {'id': user_id})
        try:
            data['pkg_dict'] = toolkit.get_action(
                'package_show')(None, {'id': package_id})
        except toolkit.ObjectNotFound:
            toolkit.abort(404, _('Dataset not found'))
        except Exception as e:
            log.warn('Exception Request Form: ' + repr(e))
            toolkit.abort(404, _('Exception retrieving dataset ('
                                 + str(e) + ')'))

        data['package_id'] = package_id
        data['resource_id'] = resource_id
        data['user_id'] = user_id
        data['user_name'] = user.get('display_name', user_id)
        data['user_email'] = user.get('email', '')
        data['package_name'] = data['pkg_dict'].get('name')
        data['resource_name'] = ''

        for resource in data['pkg_dict'].get('resources', []):
            if resource['id'] == resource_id:
                data['resource_name'] = resource['name']
                break
        else:
            toolkit.abort(404, 'Dataset resource not found')

        contact_details = self._get_contact_details(data['pkg_dict'])
        data['maintainer_email'] = contact_details.get('contact_email', '')
        data['maintainer_name'] = contact_details.get('contact_name', '')

    else:
        pass

    extra_vars = {'pkg_dict': data['pkg_dict'], 'data': data,
                  'errors':errors, 'error_summary': error_summary}
    return render('restricted/restricted_request_access_form.html',
                  extra_vars=extra_vars)







class RestrictedPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('assets', 'restricted')

    # IActions
    def get_actions(self):
        return {'resource_view_list': action.restricted_resource_view_list,
                'package_show': action.restricted_package_show,
                'resource_search': action.restricted_resource_search}
                # 'package_search': action.restricted_package_search}

    # ITemplateHelpers
    def get_helpers(self):
        return { 'restricted_get_user_id': restricted_get_user_id}

    # IAuthFunctions
    def get_auth_functions(self):
        return { 'resource_show': auth.restricted_resource_show,
                 'resource_view_show': auth.restricted_resource_show
               }
<<<<<<< HEAD
#    # IRoutes   #no longer used - 2cleanup
#    def before_map(self, map_):
#        map_.connect(
#            'restricted_request_access',
#            '/dataset/{package_id}/restricted_request_access/{resource_id}',
#            controller='ckanext.restricted.controller:RestrictedController',
#            action = 'restricted_request_access_form'
#        )
#        return map_

    # IBlueprint
    def get_blueprint(self):
        blueprint = Blueprint(self, self.__module__)
        blueprint.add_url_rule(
            '/dataset/{package_id}/restricted_request_access/{resource_id}',
            'restricted_request_access',restricted_request_access_form
        )

        return blueprint
=======

    # IBlueprint
    def get_blueprint(self):
        return blueprints.get_blueprints(self.name, self.__module__)
        
>>>>>>> int_rel2_hvw

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

