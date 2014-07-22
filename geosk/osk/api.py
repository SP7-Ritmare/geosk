import sys
import os
import json
import requests
from lxml import etree
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe
from urlparse import urlsplit
from geosk.skregistration.views import get_key
from geonode.utils import http_client, _get_basic_auth_info, json_response
from django.core.urlresolvers import reverse

from geosk.osk.models import Sensor

def lastediml(request):
    s = Sensor.objects.order_by('-id').all()[0]
    return HttpResponse(s.ediml, mimetype='application/xml')

def lastsensorml(request):
    s = Sensor.objects.order_by('-id').all()[0]
    return HttpResponse(s.sensorml, mimetype='application/xml')

def sensormleditor(request):
    queryStringValues = {
        'template': 'SensorML2',
        'version': '2.00',
        'parameters': "{}"
        }    

    # fileid = layer.mdextension.fileid
    pars = {}

    
    js_pars = json.dumps(pars, cls=DjangoJSONEncoder)

    queryStringValues['parameters'] = json.dumps(pars, cls=DjangoJSONEncoder)
    
    js_queryStringValues = json.dumps(queryStringValues)
    return render_to_response(
        'osk/osk_registration.html',
        RequestContext(request, {
                'queryStringValues': mark_safe(js_queryStringValues)
                })
        )

def _get_register_sensor(xml):
    service = settings.RITMARE['MDSERVICE'] + 'sos/registerSensor'
    headers = {
        'api_key': get_key(), 
        'Content-Type': 'application/xml'
        }
    r = requests.post(service, data=xml,  headers=headers, verify=False)
    if r.status_code == 200:
        return r.text
    return None
    

def sensormlproxy(request):
    service = settings.RITMARE['MDSERVICE'] + 'postMetadata'
    headers = {
        'api_key': get_key(), 
        'Content-Type': 'application/xml'
        }

    r = requests.post(service, data=request.raw_post_data,  headers=headers, verify=False)
    if r.status_code == 200:
        sensorml = r.text

        # get fileid
        ediml = etree.fromstring(request.raw_post_data)
        fileid = ediml.find('fileId').text

        # save sensorml & edi xml
        sensor = Sensor(fileid=fileid)
    
        sensor.sensorml = sensorml
        sensor.ediml = request.raw_post_data
        sensor.save()
        return json_response(body={'success':True,'redirect': reverse('osk_browse')})

    return json_response(errors='Cannot create SensorML', 
                         status=500)

