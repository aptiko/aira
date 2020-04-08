aira.agrifield_edit_document_ready = function () {
    document.getElementById("id_use_custom_parameters").onclick = function () {
        var custom_par = document.getElementById("custom_par");
        custom_par.style.display = (
            custom_par.style.display === "none" ? "block" : "none"
        );
    };

    /* The following should be set directly in the HTML, with the "step"
     * attribute. However, we are generating this through django-bootstrap3's
     * {% bootstrap_field %}; it isn't clear if and how this can be configured.
     */
    document.getElementById("id_custom_efficiency").step = 0.05;
    document.getElementById("id_custom_irrigation_optimizer").step = 0.01;
    document.getElementById("id_custom_root_depth_max").step = 0.1;
    document.getElementById("id_custom_root_depth_min").step = 0.1;
    document.getElementById("id_custom_max_allowed_depletion").step = 0.01;
    document.getElementById("id_custom_field_capacity").step = 0.01;
    document.getElementById("id_custom_wilting_point").step = 0.01;
    document.getElementById("id_custom_thetaS").step = 0.01;
};

aira.setupDateTimePickerForAppliedIrrigation = function () {
    $("#id_time").datetimepicker({
        format: "yyyy-mm-dd hh:ii",
        autoclose: true,
        todayBtn: true,
        pickerPosition: "bottom-left"
    });
    $(document).ready(function() {
        var label_inner = $("label[for='id_volume']").html()
        $("label[for='id_volume']").html(label_inner + " (m³)")
    });
};

aira.mapModule = (function namespace() {
    'use strict';

    var selectTimestampView = function () {
        // Select between daily or monthly View
        var timestamp = $('#timestampSelectorBtn').attr('toggle-timestamp');
        if (timestamp === 'daily') {
            $('#meteo-' + timestamp).show();
            $('#timestampSelectorBtn').attr('raster-timestamp', 'daily');
            $('#mapLegend').html(aira.transToggleTimestampMap.mapLegendDaily);
            calendarSelector('daily');
            selectRasterMap();
            nextTimeStampConfig('monthly');
        }
        if (timestamp === 'monthly') {
            $('#meteo-' + timestamp).show();
            $('#timestampSelectorBtn').attr('raster-timestamp', 'monthly');
            $('#mapLegend').html(aira.transToggleTimestampMap.mapLegendMonthly);
            calendarSelector('monthly');
            selectRasterMap();
            nextTimeStampConfig('daily');
        }
    };

    var nextTimeStampConfig = function nextTimeStampConfig(timestamp) {
        // Prepare toggle btn for the next toggle.
        // For instance, if current selection is daily
        // then next toggle is monthly.
        // Need to fix translation issue.
        $('#timestampSelectorBtn').attr('toggle-timestamp', timestamp);
        if (timestamp === 'daily') {
            $('#timestampSelectorBtn').html(aira.transToggleTimestampMap.toggleDaily);
        }
        if (timestamp === 'monthly') {
            $('#timestampSelectorBtn').html(aira.transToggleTimestampMap.toggleMonthly);
        }
        $('#meteo-' + timestamp).hide();
    };

    var calendarSelector = function (timestamp) {
        // Config calendar based of user selection.
        // Options are: daily or monthly
        $('#calendar').datetimepicker('remove');
        switch (timestamp) {
            case 'daily':
                $('#calendar').datetimepicker('remove');
                $('#calendar').datetimepicker({
                  format: 'yyyy-mm-dd',
                  startDate: '2015-01-01',
                  initialDate: aira.yesterday,
                  endDate: aira.yesterday,
                  autoclose: true,
                  pickerPosition: 'bottom-left',
                  minView: 2,
                  startView: 2,
                  todayHighlight: false,
                  linkField: 'datetimepickerMirrorField'});
                break;
            case 'monthly':
                $('#calendar').datetimepicker({
                  format: 'yyyy-mm',
                  startDate: '2015-01',
                  autoclose: true,
                  pickerPosition: 'bottom-left',
                  minView: 3,
                  startView: 3,
                  linkField: 'datetimepickerMirrorField',
                  linkFormat: 'yyyy-mm'});
                break;
        }
    };

    var selectRasterMap = function () {
        // Config map creation
        // Service url are defined here.
        var timestamp = $('#timestampSelectorBtn').attr('raster-timestamp');
        var date = $('#datetimepickerMirrorField').val();
        var meteoVar;
        var url;
        var dateFormat;
        switch (timestamp) {
            case 'daily':
                meteoVar = $('#dailyMeteoVar').val();
                url = aira.mapserver_base_url + 'historical/';
                dateFormat = 'YYYY-MM-DD';
                if (moment(date, 'YYYY-MM', true).isValid()) {
                    date = window.keepLastDailyValue;
                }
                createRasterMap(moment(date, dateFormat).format(dateFormat), meteoVar, url, dateFormat, timestamp);
                break;
            case 'monthly':
                meteoVar = $('#monthlyMeteoVar').val();
                url = aira.mapserver_base_url + 'historical/monthly/';
                dateFormat = 'YYYY-MM';
                createRasterMap(moment(date, dateFormat).format(dateFormat), meteoVar, url, dateFormat, timestamp);
                break;
        }
    };


    var getMap = function(id) {
        var map = new OpenLayers.Map(id,
                {units: 'm',
                 displayProjection: 'EPSG:4326',
                 controls: [new OpenLayers.Control.LayerSwitcher(),
                            new OpenLayers.Control.Navigation(),
                            new OpenLayers.Control.Zoom(),
                            new OpenLayers.Control.MousePosition(),
                            new OpenLayers.Control.ScaleLine()]
                 });
        addBaseLayers(map);
        map.setCenter(
            new OpenLayers.LonLat(...aira.map_default_center).transform('EPSG:4326', 'EPSG:3857'),
            aira.map_default_zoom
        );
        return map;
    };


    var addBaseLayers = function(map) {
        addOpenCycleMapBaseLayer(map);
        addHellenicCadastreBaseLayer(map);
        addGoogleSatelliteBaseLayer(map);
    };


    var addOpenCycleMapBaseLayer = function(map) {
        var openCycleMap = new OpenLayers.Layer.OSM(
                  "Open Cycle Map",
                  ["https://a.tile.thunderforest.com/cycle/${z}/${x}/${y}.png?" + aira.thunderforestApiKeyQueryElement,
                   "https://b.tile.thunderforest.com/cycle/${z}/${x}/${y}.png?" + aira.thunderforestApiKeyQueryElement,
                   "https://c.tile.thunderforest.com/cycle/${z}/${x}/${y}.png?" + aira.thunderforestApiKeyQueryElement],
                  {isBaseLayer: true,
                   projection: 'EPSG:3857'});
        map.addLayer(openCycleMap);
    };


    var addHellenicCadastreBaseLayer = function(map) {
        var ktimatologioMap = new OpenLayers.Layer.WMS("Hellenic Cadastre",
                   "http://gis.ktimanet.gr/wms/wmsopen/wmsserver.aspx",
                     {   layers: 'KTBASEMAP', transparent: false},
                     {   isBaseLayer: true,
                         projection: new OpenLayers.Projection("EPSG:900913"),
                         iformat: 'image/png'});
        map.addLayer(ktimatologioMap);
    };


    var addGoogleSatelliteBaseLayer = function(map) {
        var googleMaps = new OpenLayers.Layer.Google(
            "Google Satellite", {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22}
        );
        map.addLayer(googleMaps);
    };


    var addCoveredAreaLayer = function(map, kml_url) {
        var kml = new OpenLayers.Layer.Vector("Covered area",
                  {strategies: [new OpenLayers.Strategy.Fixed()],
                    visibility: true,
                  protocol: new OpenLayers.Protocol.HTTP(
                          {url: kml_url,
                          format: new OpenLayers.Format.KML()})})
        map.addLayer(kml);
    };


    var createRasterMap = function (date, meteoVar, url, dateFormat, timestamp) {
        $('#wms_map').html('');
        $('#datetimepickerMirrorField').val(date);
        $('#datepickerInputSelector').val(date);
        betweenDatesBtns(date, timestamp, dateFormat);
        var urlToRequest;
        var layersToRequest;
        if (timestamp === 'daily') {
            window.keepLastDailyValue = date;
            urlToRequest = url + date + "/";
            layersToRequest = meteoVar + date;
        }
        if (timestamp === 'monthly') {
            urlToRequest = url;
            layersToRequest = meteoVar + date;
        }
        // Keep this for debugging
        // console.log("date:" + date + ';' + 'meteoVar:' + meteoVar + ';' + 'url:' + url);

        // Map object
        var map = getMap('wms_map');

        // Meteo layer
        var meteoVarWMS = new OpenLayers.Layer.WMS(
                  meteoVar + date,
                  urlToRequest,
                  {layers: layersToRequest,
                   format: 'image/png'},
                  {isBaseLayer: false,
                   projection: 'EPSG:3857',
                   opacity: 0.65});

        map.addLayer(meteoVarWMS);

        //if (timestamp === 'daily') {
        // When clicking on the map, show popup with values of variables
        OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {
              defaultHandlerOptions: {
                  'single': true,
                  'double': false,
                  'pixelTolerance': 0,
                  'stopSingle': false,
                  'stopDouble': false
              },
              initialize: function (options) {
                  this.handlerOptions = OpenLayers.Util.extend(
                      {}, this.defaultHandlerOptions
                  );
                  OpenLayers.Control.prototype.initialize.apply(
                      this, arguments
                  );
                  this.handler = new OpenLayers.Handler.Click(
                      this, {
                          'click': this.trigger
                      }, this.handlerOptions
                  );
              },
              trigger: function (e) {
                  var lonlat = map.getLonLatFromPixel(e.xy);
                  var xhr = new XMLHttpRequest();
                  // Create a small bbox such that the point is at the bottom left of the box
                  var xlow = lonlat.lon;
                  var xhigh = lonlat.lon + 50;
                  var ylow = lonlat.lat;
                  var yhigh = lonlat.lat + 50;
                  var bbox = xlow + ',' + ylow + ',' + xhigh + ',' + yhigh;

                  // Determine layers
                  if (timestamp === 'daily')  {
                      var layers = '';
                      ['temperature', 'humidity', 'wind_speed', 'rain', 'evaporation',
                       'solar_radiation'].forEach(function (s) {
                        if (layers !== '') {
                            layers = layers + ',';
                        }
                        layers = layers + 'Daily_' + s + '_' + date;
                    });
                      urlPoint = url + date + '/';
                  }
                  if (timestamp === 'monthly')  {
                      var layers = '';
                      // forEach is used because in near future more monthly
                      // meteorogical variables will be added.
                      ['evaporation'].forEach(function (s) {
                        if (layers !== '') {
                            layers = layers + ',';
                        }
                        layers = layers + 'Monthly_' + s + '_' + date;
                    });
                      var urlPoint = url;
                  }
                  console.log(urlPoint);
                  // Assemble URL
                  urlPoint = urlPoint + '?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&SRS=EPSG:3857&info_format=text/html';
                  urlPoint = urlPoint + '&BBOX=' + bbox + '&WIDTH=2&HEIGHT=2&X=0&Y=0';
                  urlPoint = urlPoint + '&LAYERS=' + layers + '&QUERY_LAYERS=' + layers;

                  xhr.open('GET', urlPoint, false);
                  xhr.send();
                  /* The test "length < 250" below is an ugly hack for not showing
                   * popups at a masked area. The masked area has the value nodata,
                   * which displays as a large negative number with very many digits.
                   */
                  if (xhr.readyState === 4  &&  xhr.responseText.length < 250) {
                      map.addPopup(new OpenLayers.Popup.FramedCloud(
                                   null, lonlat, null,
                                   xhr.responseText,
                                   null, true));
                  }
              }
          });
        var click = new OpenLayers.Control.Click();
        map.addControl(click);
        click.activate();

        // Add control and center
        map.setCenter (new OpenLayers.LonLat(20.98, 39.15).transform('EPSG:4326', 'EPSG:3857'), 10);
    };

    var initTimestampView = function () {
        $('#datetimepickerMirrorField').val(aira.yesterday);
        $('#datepickerInputSelector').val(aira.yesterday);
        window.keepLastDailyValue = aira.yesterday;
        selectTimestampView();
        selectRasterMap();
    };

    var betweenDatesBtns = function (date, timestamp, dateFormat) {
        var addTimestamp;
        if (dateFormat === "YYYY-MM-DD") {
            addTimestamp = 'days';
        } else {
            addTimestamp = 'month';
        }
        $('#current').html(moment(date, dateFormat).format(dateFormat));
        var plusOneDate = moment(date, dateFormat).add(1, addTimestamp);
        var minusOneDate = moment(date, dateFormat).subtract(1, addTimestamp);
        $('#next').html(plusOneDate.format(dateFormat) + "&nbsp;<i class='fa fa-chevron-right'></i>&nbsp;");
        $('#next').val(plusOneDate.format(dateFormat));
        if (plusOneDate.isAfter(aira.yesterday)) {
            $('#next').hide();
        } else {
            $('#next').show();
        }
        $('#previous').html("&nbsp;<i class='fa fa-chevron-left'></i>&nbsp;" + minusOneDate.format(dateFormat));
        $('#previous').val(minusOneDate.format(dateFormat));
        if (minusOneDate.isBefore("2015-01-01")) {
            $('#previous').hide();
        } else {
            $('#previous').show();
        }
    };

    var createNextRasterMap = function () {
        var timestamp = $('#timestampSelectorBtn').attr('raster-timestamp');
        if (timestamp === 'daily') {
            createRasterMap($('#next').val(),
                            $('#dailyMeteoVar').val(),
                            aira.mapserver_base_url + 'historical/',
                            'YYYY-MM-DD',
                            'daily');
        }
        if (timestamp === 'monthly') {
            createRasterMap($('#next').val(),
                            $('#monthlyMeteoVar').val(),
                            aira.mapserver_base_url + 'historical/monthly/',
                            'YYYY-MM',
                            'monthly');
        }
    };

    var createPreviousRasterMap = function () {
        var timestamp = $('#timestampSelectorBtn').attr('raster-timestamp');
        if (timestamp === 'daily') {
            createRasterMap($('#previous').val(),
                            $('#dailyMeteoVar').val(),
                            aira.mapserver_base_url + 'historical/',
                            'YYYY-MM-DD',
                            'daily');
        }
        if (timestamp === 'monthly') {
            createRasterMap($('#previous').val(),
                            $('#monthlyMeteoVar').val(),
                            aira.mapserver_base_url + 'historical/monthly/',
                            'YYYY-MM',
                            'monthly');
        }
    };

    var addAgrifieldsToMap = function (map, agrifields, layerName) {
        var layer = new OpenLayers.Layer.Vector(layerName);
        agrifields.forEach(item => {
            var geometry = new OpenLayers.Geometry.Point(...item.coords)
                .transform('EPSG:4326', 'EPSG:3857');
            var attributes = {
                description: '<a href="' + item.url + '">' + item.name + '</a>',
            };
            var style = {
                externalGraphic: 'https://cdnjs.cloudflare.com/ajax/libs/openlayers/2.12/img/marker.png',
                graphicHeight: 25,
                graphicWidth: 21,
                graphicXOffset:-12,
                graphicYOffset:-25,
            };
            var feature = new OpenLayers.Feature.Vector(geometry, attributes, style);
            layer.addFeatures(feature);
        });
        map.addLayer(layer);

        // Center map if only one field
        if (agrifields.length == 1) {
            map.setCenter(
                new OpenLayers.LonLat(...agrifields[0].coords)
                    .transform('EPSG:4326', 'EPSG:3857'),
                18,
            );
        }

        // Popup
        var selector = new OpenLayers.Control.SelectFeature(
            layer, { onSelect: createPopup, onUnselect: destroyPopup }
        );
        function createPopup(feature) {
          feature.popup = new OpenLayers.Popup.FramedCloud("pop",
              feature.geometry.getBounds().getCenterLonLat(),
              null,
              '<div class="markerContent">'+feature.attributes.description+'</div>',
              null,
              true,
              function() { selector.unselectAll(); }
          );
          map.addPopup(feature.popup);
        }
        function destroyPopup(feature) {
          feature.popup.destroy();
          feature.popup = null;
        }
        map.addControl(selector);
        selector.activate();

        return layer;
    };

    var registerClickEvent = function(map, layer) {
        map.events.register("click", map , function(e){
            var coords = map.getLonLatFromPixel(e.xy) ;
            var geometry = new OpenLayers.Geometry.Point(coords.lon, coords.lat);
            var attributes = { description: "" };
            var style = {
                externalGraphic: 'https://cdnjs.cloudflare.com/ajax/libs/openlayers/2.12/img/marker.png',
                graphicHeight: 25,
                graphicWidth: 21,
                graphicXOffset:-12,
                graphicYOffset:-25,
            };
            var feature = new OpenLayers.Feature.Vector(geometry, attributes, style);
            layer.removeAllFeatures();
            layer.addFeatures(feature);
            var lonlat = coords.transform('EPSG:3857', 'EPSG:4326');
            document.getElementById("id_location_1").value = lonlat.lat.toFixed(5);
            document.getElementById("id_location_0").value = lonlat.lon.toFixed(5);
        });
    };

    return {
        selectRasterMap: selectRasterMap,
        selectTimestampView: selectTimestampView,
        createRasterMap: createRasterMap,
        createNextRasterMap: createNextRasterMap,
        createPreviousRasterMap: createPreviousRasterMap,
        initTimestampView: initTimestampView,
        getMap: getMap,
        addCoveredAreaLayer: addCoveredAreaLayer,
        addAgrifieldsToMap: addAgrifieldsToMap,
        registerClickEvent: registerClickEvent,
    };
}());
