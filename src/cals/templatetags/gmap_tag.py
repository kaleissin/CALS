from __future__ import absolute_import
from __future__ import unicode_literals

from django import template
from django.template import Library
from django.template import RequestContext
from django.template import resolve_variable

GOOGLE_MAPS_API_KEY = {
    'cals': 'ABQIAAAA3l8AIG_4m32NOSjtfKVp3xQZmzhEy08TjSB7X9Gobsoh1Cu18hQl8di61W2RFoEnGnVplXrfXVu4TA',
}
CURRENT_SITE = "cals"

register = Library()

INCLUDE_TEMPLATE = """
<script src="http://maps.google.com/maps?file=api&amp;v=2&amp;key=%s" type="text/javascript"></script>
""" % (GOOGLE_MAPS_API_KEY [ CURRENT_SITE ] , )

BASIC_TEMPLATE = """
<div id="map_%(name)s" style="width:%(width)spx;height:%(height)spx;"></div>
<script>
function create_map_%(name)s() {
   if (GBrowserIsCompatible()) {
    var map = new GMap2(document.getElementById("map_%(name)s"));
    map.enableDoubleClickZoom();
    map.enableContinuousZoom();
    map.addControl(new GSmallMapControl());
    map.addControl(new GMapTypeControl());
    map.setCenter(new GLatLng(%(latitude)s,%(longitude)s), %(zoom)s, map.getMapTypes()[%(view)d]);

    var point = map.getCenter();
    var m = new GMarker(point);
    GEvent.addListener(m, "click", function() {
       m.openInfoWindowHtml("%(message)s");
    });
    map.addOverlay(m);
    return map;
   }
}
</script>
"""
# {% gmap name:mimapa width:300 height:300 latitude:x longitude:y zoom:20 view:hybrid %} Message for a marker at that point {% endgmap %}

class GMapNode (template.Node):
    def __init__(self, params, nodelist):
        self.params = params
        self.nodelist = nodelist
        
    def render (self, context):
        for k,v in self.params.items():
            try:
                self.params[k] = resolve_variable(v, context)
            except:
                pass
            if k == "view":
                if v=="satellite": 
                    v = 1
                elif v=="map":
                    v = 0
                else:
                    v = 2
                self.params[k] = v
        self.params["message"] = self.nodelist.render(context).replace("\n", "<br />")
        return BASIC_TEMPLATE % self.params

def do_gmap(parser, token):
    items = token.split_contents()

    nodelist = parser.parse(('endgmap',))
    parser.delete_first_token()
    
    #Default values 
    parameters={
            'name'      : "default",
            'width'     : "300",
            'height'    : "300",
            'latitude'  : "33",
            'longitude' : "-3",
            'zoom'      : "15",
            'view'      : "hybrid", # map, satellite, hybrid
            'message'   : "No message",
    }
    for item in items[1:]:
        param, value = item.split(":")
        param = param.strip()
        value = value.strip()
        
        if param in parameters:
            if value[0]=="\"":
                value = value[1:-1]
            parameters[param] = value
        
    return GMapNode(parameters, nodelist)

class GMapScriptNode (template.Node):
    def __init__(self):
        pass        
    def render (self, context):
        return INCLUDE_TEMPLATE

def do_gmap_script(parser, token):
    try:
        tag_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("La etiqueta no requiere argumentos" % token.contents[0])
    return GMapScriptNode()

register.tag('gmap', do_gmap)
register.tag('gmap-script', do_gmap_script)

