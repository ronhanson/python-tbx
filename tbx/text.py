#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Text Utils
:author: Ronan Delacroix
"""
import json
import datetime

import os
import lxml.etree as etree
import re
import smtplib
import unicodedata
import six
import uuid as UUID
import base64

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

if six.PY3:
    import html
else:
    import cgi as html


def normalize_text(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')


def slugify(text, delim='-'):
    """Generates an slightly worse ASCII-only slug."""
    punctuation_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.:]+')

    result = []
    for word in punctuation_re.split(text.lower()):
        word = normalize_text(word)
        if word:
            result.append(word)
    return delim.join(result)


def slugify_bytes(b):
    return base64.urlsafe_b64encode(b).decode('utf-8').strip('=')


def uuid_to_slug(uuid):
    if isinstance(uuid, str):
        b = UUID.UUID(uuid)
    elif isinstance(uuid, UUID.UUID):
        b = uuid.bytes
    elif isinstance(uuid, bytes):
        b = uuid
    else:
        b = bytes(uuid)
    return slugify_bytes(b)


def random_slug():
    return uuid_to_slug(UUID.uuid4().bytes)


def random_short_slug():
    return uuid_to_slug(UUID.uuid4().bytes[0:8])


def javascript_escape(s, quote_double_quotes=True):
    """
    Escape characters for javascript strings.
    """
    ustring_re = re.compile(u"([\u0080-\uffff])")

    def fix(match):
        return r"\u%04x" % ord(match.group(1))

    if type(s) == str:
        s = s.decode('utf-8')
    elif type(s) != six.text_type:
        raise TypeError(s)
    s = s.replace('\\', '\\\\')
    s = s.replace('\r', '\\r')
    s = s.replace('\n', '\\n')
    s = s.replace('\t', '\\t')
    s = s.replace("'", "\\'")
    if quote_double_quotes:
        s = s.replace('"', '&quot;')
    return str(ustring_re.sub(fix, s))


def send_mail(send_from, send_to, subject, text, server, mime='plain', files=None):
    """
    Send an email with attachments.
    :param send_from: from email adress
    :param send_to: to email adress
    :param subject: email subject
    :param text: text of the email in html
    :param server: SMTP server
    :param files: files to attach
    :return: None
    """
    if not files:
        files = []

    assert type(send_to) == list
    assert type(files) == list

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text, mime))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        fp = open(f, "rb")
        file_content = fp.read()
        part.set_payload(file_content)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()
    return


def hms_to_seconds(time_string):
    """
    Converts string 'hh:mm:ss.ssssss' as a float
    """
    s = time_string.split(':')
    hours = int(s[0])
    minutes = int(s[1])
    secs = float(s[2])
    return hours * 3600 + minutes * 60 + secs

    
def seconds_to_hms_verbose(t):
    """
    Converts seconds float to 'H hours 8 minutes, 30 seconds' format
    """
    hours = int((t / 3600))
    mins = int((t / 60) % 60)
    secs = int(t % 60)
    return ' '.join([
        (hours + ' hour'+('s' if hours > 1 else '')) if hours > 0 else '',
        (mins + ' minute'+('s' if mins > 1 else '')) if mins > 0 else '',
        (secs + ' second'+('s' if secs > 1 else '')) if secs > 0 else ''
    ])


def seconds_to_hms(seconds):
    """
    Converts seconds float to 'hh:mm:ss.ssssss' format.
    """
    hours = int(seconds / 3600.0)
    minutes = int((seconds / 60.0) % 60.0)
    secs = float(seconds % 60.0)
    return "{0:02d}:{1:02d}:{2:02.6f}".format(hours, minutes, secs)


def str_to_bool(v):
    return str(v).lower() in ("yes", "on", "true", "y", "t", "1")


datetime_handler = lambda obj: obj.isoformat(sep=' ') if isinstance(obj, datetime.datetime) else None

render_xml = lambda _dict: dict_to_xml_string("xml", _dict)
render_json = lambda _dict: json.dumps(_dict, sort_keys=False, indent=4, default=datetime_handler)
render_html = lambda _dict: dict_to_html(_dict)
render_txt = lambda _dict: dict_to_plaintext(_dict)

mime_rendering_dict = {
    'text/html': render_html,
    'application/html': render_html,
    'application/xml': render_xml,
    'application/json': render_json,
    'text/plain': render_txt
}


def render_dict_from_mimetype(d, mimetype):
    return mime_rendering_dict.get(mimetype, render_json)(d)


def pretty_render(data, format='text', indent=0):
    """
    Render a dict based on a format
    """
    if format == 'json':
        return render_json(data)
    elif format == 'html':
        return render_html(data)
    elif format == 'xml':
        return render_xml(data)
    else:
        return dict_to_plaintext(data, indent=indent)


# DICT TO XML FUNCTION
def _dict_to_xml_recurse(parent, dictitem):
    if isinstance(dictitem, list):
        dictitem = {'item' : dictitem}
    if isinstance(dictitem, dict):
        for (tag, child) in dictitem.items():
            if str(tag) == '_text':
                parent.text = str(child)
            elif type(child) is type([]):
                # iterate through the array and convert
                for listchild in child:
                    elem = etree.Element(tag)
                    parent.append(elem)
                    _dict_to_xml_recurse(elem, listchild)
            elif len(tag)==36 and tag[8]=='-' and tag[13]=='-': #if uuid is name of the element we try to cook up something nice to display in xml
                uuid = tag
                tag = parent.tag.replace('_list', '').replace('_dict', '')
                elem = etree.Element(tag, uuid=uuid)
                parent.append(elem)
                _dict_to_xml_recurse(elem, child)
            else:
                try:
                    elem = etree.Element(tag)
                except ValueError:
                    elem = etree.Element("element", unrecognized=tag)
                parent.append(elem)
                _dict_to_xml_recurse(elem, child)
    else:
        parent.text = str(dictitem)


def dict_to_xml(xml_dict):
    """
    Converts a dictionary to an XML ElementTree Element
    """
    root_tag = list(xml_dict.keys())[0]
    root = etree.Element(root_tag)
    _dict_to_xml_recurse(root, xml_dict[root_tag])
    return root


def dict_to_xml_string(root_name, _dict):
    _dict = {root_name: _dict}
    xml_root = dict_to_xml(_dict)
    return etree.tostring(xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True)


# DICT TO TEXT FUNCTION
def dict_to_plaintext(_dict, indent=0, result=''):
    if isinstance(_dict, list):
        i = 0
        if not _dict:
            result += '\t' * indent + "<empty>\n"
        for value in _dict:
            i += 1
            if isinstance(value, dict) :
                result += '\t' * indent + "["+str(i)+"]={DICT}\n" + dict_to_plaintext(value, indent+1)
            elif isinstance(value, list) :
                result += '\t' * indent + "["+str(i)+"]=<LIST>\n" + dict_to_plaintext(value, indent+1) + "\n"
            else:
                result += '\t' * indent + "["+str(i)+"]=\"" + str(value) + "\"\n"
        return result
    elif isinstance(_dict, dict):
        for key, value in _dict.items():
            if isinstance(value, dict):
                result += '\t' * indent + "{" + str(key) + "}\n" + dict_to_plaintext(value, indent+1)
            elif isinstance(value, list):
                result += '\t' * indent + "<" + str(key) + '>\n' + dict_to_plaintext(value, indent+1)
            else:
                if "\n" in str(value):
                    value = ' '.join([line.strip() for line in str(value).replace("\"", "'").split("\n")])
                result += '\t' * indent + str(key) + '=' + "\"" + str(value) + "\"\n"
        return result
    else:
        return "\"" + str(_dict) + "\""


# DICT TO HTML FUNCTION
def _dict_to_html_recurse(_dict, indent=0, result=''):
    if isinstance(_dict, list):
        i = 0
        result += '    ' * indent + "<ul>\n"
        for value in _dict:
            i += 1
            if isinstance(value, dict):
                result += '    ' * (indent+1) + "<li class='row"+str(i % 2)+"'>\n" + _dict_to_html_recurse(value, indent + 2) + '    ' * (indent + 1) + "</li>\n"
            elif isinstance(value, list):
                result += '    ' * (indent+1) + "<li class='row"+str(i % 2)+"'>\n" + _dict_to_html_recurse(value, indent + 2) + '    ' * (indent + 1) + "</li>\n"
            else:
                result += '    ' * (indent+1) + "<li class='row"+str(i % 2)+"'><pre>" + html.escape(str(value)) + "</pre></li>\n"
        result += '    ' * indent + "</ul>\n"
        return result
    elif isinstance(_dict, dict):
        result += '    ' * indent + "<table>\n"
        i=0
        for key, value in _dict.items():
            i+=1
            if isinstance(value, dict) or isinstance(value, list):
                result += '    ' * (indent + 1) + "<tr class='row"+str(i % 2)+"'>\n"
                result += '    ' * (indent + 2) + "<td>" + str(key) + "</td>\n"
                result += '    ' * (indent + 2) + "<td>\n" + _dict_to_html_recurse(value, indent+3)
                result += '    ' * (indent + 2) + "</td>\n"
                result += '    ' * (indent + 1) + "</tr>\n"
            else:
                value = html.escape(str(value))
                result += '    ' * (indent + 1) + "<tr class='row"+str(i % 2)+"'><td>" + str(key) + "</td><td><pre>" + str(value) + "</pre></td></tr>\n"
        result += '    ' * indent + "</table>\n"
        return result
    else:
        return "<pre>" + html.escape(str(_dict)) + "</pre>"


def dict_to_html(_dict, title="Result"):
    return """
<html>
    <head>
        <style>
            body { font-family: monospace; }
            table { display : inline-block; border-spacing: 0px; border-collapse: collapse; }
            td { border : 1px solid grey; padding:3px 10px; }
            li { border : 1px solid grey; padding:0px 10px 0px 10px; margin: 0px 0px 0px 5px; list-style-type : circle; }
            ul { display : inline-block; padding:0px 0px 0px 10px; margin:0px;}
            pre { margin:0 ; }
            .row0 { background-color:#EAEAFF; }
            .row1 { background-color:#FFFFFF; }
        </style>
        <title>"""+title+"""</title>
    </head>
    <body>
""" + _dict_to_html_recurse(_dict, 2) + "    </body>\n</html>"


def test_page(title="Result"):
    result = "<table>"
    docu = {}
    i=0
    for func_name, doc in docu.items():
        result += "<tr class='row" + str(i) + "'><td>" + doc['friendly_name'] + "</td>"
        if 'parameters' in doc:
            result += "<td><form action='" + func_name + "' method='"+doc['method_type']+"' enctype='multipart/form-data'>"
            result += "<table width='100%'>"
            if 'required' in doc['parameters']:
                result += "<tr><th colspan='2'>Required</th></tr>"
                for param in doc['parameters']['required']:
                    if param == 'asset_file':
                        result += "<tr><td>" + str(param) + "</td><td><input type='file' name='" + str(param) + "' value=''/></td><tr/>"
                    else:
                        result += "<tr><td>" + str(param) + "</td><td><input type='text' name='" + str(param) + "' value=''/></td><tr/>"

            if 'optionnal' in doc['parameters']:
                result += "<tr><th colspan='2'>Optionnal</th></tr>"
                for param, value in doc['parameters']['optionnal'].items():
                    if value==None:
                        value=''
                    result += "<tr><td>" + str(param) + "</td><td><input type='text' name='" + str(param) + "' value='" + str(value) + "'/></td><tr/>"
            result += "<tr><th colspan='2'><input type='submit'/></th></tr>"
            result += "</table>"
            result += "</form></td>"
        else:
            result += "<td><a href='" + func_name + "'>" + func_name + "</a></td>"
        result += "</tr>"
        i += 1
        i = i%2

    result += "</table>"
    return """
<html>
    <head>
        <style>
            body {font-family: monospace;}
            table {display : inline-block; border-spacing: 0px; border-collapse: collapse;}
            td {border: 1px solid grey; padding: 3px 10px;}
            li {border: 1px solid grey; padding: 0px 10px 0px 10px; margin: 0px 0px 0px 5px; list-style-type: circle;}
            ul {display: inline-block; padding: 0px 0px 0px 10px; margin:0px;}
            pre {margin: 0;}
            .row0 {background-color:#EAEAFF;}
            .row1 {background-color:#FFFFFF;}
        </style>
        <title>"""+title+"""</title>
    </head>
    <body>
""" + result + """
    </body>
</html>"""


def uni(text):
    """
    Tries to force to convert to unicode a text.
    REALLY DIRTY HACK TO TRY TO DETECT ENCODINGS...
    :param text: text to convert
    :return: unicode text
    """
    if type(text) == six.text_type:
        for encoding in ['latin_1', 'ascii', 'utf-8']:
            try:
                strtext = text.encode(encoding)
            except:
                pass
            else:
                break
        text = strtext

    unitext = text
    for encoding in ['utf-8', 'ascii', 'latin_1']:
        try:
            unitext = text.decode(encoding)
        except:
            pass
        else:
            break
    return unitext


def xml_get_tag(xml, tag, parent_tag=None, multi_line=False):
    """
    Returns the tag data for the first instance of the named tag, or for all instances if multi is true.
    If a parent tag is specified, then that will be required before the tag.
    """
    expr_str = '[<:]'+tag+'.*?>(?P<matched_text>.+?)<'
    if parent_tag:
        expr_str = '[<:]'+parent_tag+'.*?>.*?' + expr_str
    expr = re.compile(expr_str, re.DOTALL | re.IGNORECASE)
    if multi_line:
        return expr.findall(xml)
    else:
        if expr.search(xml):
            return expr.search(xml).group('matched_text').strip()
        else:
            return None