# Reference data (not part of the GTFS feed)

## paraderos_rurales_somos.csv

Rural bus stops ("Estaciones buses" layer) from the SOMOS Movilidad map on
<https://somosmovilidad.gov.co/sistema-de-bicicletas-bicirio/> (map script
`somos-mapa/leaflet-routing-machine-3.2.12/examples/index.js`), retrieved 2026-11-01.

`rapido_route` is a manual match against the municipal routes on
<https://www.rapidomedellin.com/rutas/municipales/27>, with a confidence level.
Stops without a match are probably served by other operators.

Rápido publishes only distance and travel time for its municipal routes
(no timetables), so these routes are not in the feed yet.
