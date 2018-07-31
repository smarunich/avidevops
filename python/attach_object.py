#!/usr/bin/python
import argparse
import json
import os
import sys
import re
import requests
requests.packages.urllib3.disable_warnings()

from avi.sdk.avi_api import ApiSession

DEFAULT_API_VERSION = '17.2.9'
FORCE_YES_FOR_USER_PROMPT = False
API_OBJECT_TO_REF_TRANSLATIONS = {
    'wafpolicy': 'waf_policy_ref',
    'serviceenginegroup': 'se_group_ref',
    'errorpageprofile': 'error_page_profile_ref',
    'applicationprofile': 'application_profile_ref',
    'networksecuritypolicy': 'network_security_policy_ref'
}

def ask_ok(prompt, retries=4, complaint='yes or no, please!'):
    while True:
        if FORCE_YES_FOR_USER_PROMPT:
            return True
        else:
            prompt = prompt + ' (yes/no) '
            ok = raw_input(prompt)
            if ok in ('y', 'ye', 'yes'):
                return True
            elif ok in ('n', 'no', 'nop', 'nope'):
                return False
        retries = retries - 1
        if retries < 0:
            raise IOError('uncooperative user')
        print(complaint)

# Define as class

def attach_object(session, cloud, object_to_be_referred_type, object_to_be_referred_name, target_object_type, target_object_name):
    object_to_be_referred_type = re.sub(
        '[^A-Za-z]', '', object_to_be_referred_type)
    obj = session.get_object_by_name(
        object_to_be_referred_type, object_to_be_referred_name)
    obj_ref = session.get_obj_ref(obj)
    if object_to_be_referred_type in API_OBJECT_TO_REF_TRANSLATIONS.keys():
        obj_type_ref = API_OBJECT_TO_REF_TRANSLATIONS[object_to_be_referred_type]
    else:
        obj_type_ref = object_to_be_referred_type + "_ref"
    target_obj = session.get_object_by_name(target_object_type, target_object_name, params={
                                            'include_name': '', 'include_refs': ''})
    cloud_ref = "/api/cloud?name=" + cloud
    obj_to_data = {
        "add":
        {
        "cloud_ref": cloud_ref,
        obj_type_ref: obj_ref
        }
    }
    target_obj_existing_ref = None
    if target_obj:
        obj_to_ref = target_object_type + '/' + target_obj['uuid']
        obj_cloud_ref = target_obj['cloud_ref']
        try:
            target_obj_existing_ref = target_obj[obj_type_ref][target_obj[obj_type_ref].find("#") + 1:]
            target_cloud_name = obj_cloud_ref[obj_cloud_ref.find("#") + 1:]
        except:
            pass
        if not obj:
            print("Source object or object to be attached not found: " +
                object_to_be_referred_type + "/" + object_to_be_referred_name)
        elif obj['name'] != target_obj_existing_ref and target_obj and cloud == target_cloud_name:
            if ask_ok("Current allocation for " + target_object_type + "/" + target_object_name + ' is ' + object_to_be_referred_type + '/' +
                        str(target_obj_existing_ref) + " override it to " + object_to_be_referred_type + "/" + object_to_be_referred_name):
                resp = session.patch(
                    obj_to_ref, data=obj_to_data, verify=False)
                if resp.status_code == 200:
                        print("Successfully attached " + object_to_be_referred_type + "/" +
                            object_to_be_referred_name + " to " + target_object_type + "/" + target_object_name)
                else:
                        print("Error " + str(resp.status_code) + " attaching source object " + object_to_be_referred_type + "/" +
                            object_to_be_referred_name + " to target object " + target_object_type + "/" + target_object_name)
        elif cloud != target_cloud_name:
            print("Target object " + target_object_type +
                  "/" + target_object_name + " is part of a different cloud " + target_cloud_name)
        else:
            print("No changes to apply, configuration exists already: " + object_to_be_referred_type + "/" +
                object_to_be_referred_name + " to " + target_object_type + "/" + target_object_name)
    else:
        print("Target object or attach to-obj not found: " + target_object_type + "/" + target_object_name)

    #print(resp.status_code, resp.json())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='controller user',
                        default='admin')
    parser.add_argument('-p', '--password', help='controller user password',
                        default='AviNetworks123!')
    parser.add_argument('-t', '--tenant', help='tenant name',
                        default=None)
    parser.add_argument('--api_version', help='API version',
                        default=DEFAULT_API_VERSION)
    parser.add_argument('--cloud', help='API version',
                        default='Default-Cloud')
    parser.add_argument('--attach-obj-type', help='Object type to attach. List of supported types: pool, segrp, httppolicyset, wafpolicy, datascript',
                        default=None)
    parser.add_argument('--attach-obj-name',
                        help='Objects name list to attach', default=None)
    parser.add_argument('--attach-to-obj-type', help='Target object type for attachment. List of supported types: virtualservice',
                        default='virtualservice')
    parser.add_argument('--attach-to-obj-name',
                        help='Targets name list for attachment',default=None)
    parser.add_argument('--force', help='Dont ask user to acknowledge action, force yes for all actions',
                        dest="FORCE_YES_FOR_USER_PROMPT", action='store_true')
    parser.add_argument('-c', '--controller', help='controller address')
    args = parser.parse_args()

    session = ApiSession.get_session(args.controller, args.user,
                                args.password, tenant=args.tenant, api_version=args.api_version)
    if args.FORCE_YES_FOR_USER_PROMPT:
        FORCE_YES_FOR_USER_PROMPT = args.FORCE_YES_FOR_USER_PROMPT

    attach_obj_name_list = args.attach_obj_name.split(',')
    attach_to_obj_name_list = args.attach_to_obj_name.split(',')
    if ask_ok("Do you want to proceed with object attachment? ",2):
        for attach_obj_name in attach_obj_name_list:
            for attach_to_obj_name in attach_to_obj_name_list:
                attach_object(session, args.cloud, args.attach_obj_type, attach_obj_name,
                        args.attach_to_obj_type, attach_to_obj_name)

#base class to read schema
#define class itself
#


    ''' tests
    attach_object(session, args.cloud, "pool", "test-default-cloud-pool",
            "virtualservice", "test-default-cloud")
    attach_object(session, args.cloud, "wafpolicy", "System-WAF-Policy",
            "virtualservice", "test-default-cloud")
    '''
