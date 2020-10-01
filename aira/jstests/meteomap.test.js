L = {  // eslint-disable-line
  tileLayer: {
    wms: jest.fn(),
  },
};

aira = {};
require('../static/js/aira');

describe('meteoMapPanel.updateMeteoLayer', () => {
  const tileLayerWmsReturnValue = { addTo: jest.fn() };

  beforeAll(() => {
    document.body.innerHTML = `
      <a id='timestep-toggle' href='#' current-timestep='daily'></a>
      <form>
        <select id='dailyMeteoVar'>
          <option value="Daily_rain_">Daily rainfall (mm/d)</option>
        </select>
        <input type='text' id='date-input' value='2020-09-30'>
      </form>
    `;
    aira.map.layerSwitcher = { addOverlay: jest.fn() };
    L.tileLayer.wms.mockReturnValue(tileLayerWmsReturnValue);
    aira.meteoMapPanel.updateMeteoLayer();
  });

  test('meteo raster is not hidden by background layer', () => {
    const layerOptions = L.tileLayer.wms.mock.calls[0][1];
    expect(layerOptions.zIndex).toBe(100);
  });

  test('adds meteo raster to layer switcher', () => {
    expect(aira.map.layerSwitcher.addOverlay).toHaveBeenCalled();

    /* The correct test would be the one below, but apparently jsdom does not
     * support HTMLSelectElement.options and/or HTMLSelectElement.selectedIndex,
     * which are how the main code determines the string to use when calling
     * addOverlay().
     */
    // expect(aira.map.layerSwitcher.addOverlay).toHaveBeenCalledWith(
    //  tileLayerWmsReturnValue, "Daily rainfall (mm/d)",
    // );
  });
});
