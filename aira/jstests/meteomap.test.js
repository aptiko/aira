L = {  // eslint-disable-line
  tileLayer: {
    wms: jest.fn(),
  },
};
L.tileLayer.wms.mockReturnValue({
  addTo: jest.fn(),
});

aira = {};
require('../static/js/aira');

describe('meteoMapPanel', () => {
  beforeAll(() => {
    document.body.innerHTML = `
      <a id='timestep-toggle' href='#' current-timestep='daily'></a>
      <form>
        <input type='text' id='dailyMeteoVar' value='irrelevant'>
        <input type='text' id='date-input' value='2020-09-30'>
      </form>
    `;
  });

  test('meteo raster is not hidden by background layer', () => {
    aira.meteoMapPanel.updateMeteoLayer();
    const layerOptions = L.tileLayer.wms.mock.calls[0][1];
    expect(layerOptions.zIndex).toBe(100);
  });
});
