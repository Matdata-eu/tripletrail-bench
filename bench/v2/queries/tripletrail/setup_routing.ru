PREFIX pgr: <http://w3id.org/tripletrail/pgr#>
PREFIX bench: <http://example.org/bench/>
# Two named networks. bench:micro is profiles/era-micro.rq unchanged; bench:microc adds the gauge
# and electrification of the track of the element entered as ?c_* columns for pgr:constraint.
# The graphs are built (and cached) on the first query that uses them. The track lookup is
# repeated inside each UNION branch: written once after the UNION, the tripletrail planner evaluated
# the UNION once per track (a lateral join) and the edge query ran for minutes.
DELETE WHERE { bench:micro pgr:edgeQuery ?q1 } ;
DELETE WHERE { bench:microc pgr:edgeQuery ?q2 } ;
INSERT DATA {
bench:micro a pgr:Network ; pgr:edgeQuery """
PREFIX era: <http://data.europa.eu/949/>
PREFIX nav: <http://data.europa.eu/949/concepts/navigabilities/>
SELECT ?id ?source ?target ?cost WHERE {
  {
    ?r a era:NetRelation ; era:elementA ?a ; era:elementB ?b ;
       era:isOnOriginOfElementA ?oa ; era:isOnOriginOfElementB ?ob ; era:navigability ?nav .
    FILTER(?nav IN (nav:AB, nav:Both))
    ?b era:lengthOfNetLinearElement ?cost .
    BIND(CONCAT(STR(?a), IF(?oa, "#bwd", "#fwd")) AS ?source)
    BIND(CONCAT(STR(?b), IF(?ob, "#fwd", "#bwd")) AS ?target)
    BIND(CONCAT(STR(?r), "#ab") AS ?id)
  } UNION {
    ?r a era:NetRelation ; era:elementA ?a ; era:elementB ?b ;
       era:isOnOriginOfElementA ?oa ; era:isOnOriginOfElementB ?ob ; era:navigability ?nav .
    FILTER(?nav IN (nav:BA, nav:Both))
    ?a era:lengthOfNetLinearElement ?cost .
    BIND(CONCAT(STR(?b), IF(?ob, "#bwd", "#fwd")) AS ?source)
    BIND(CONCAT(STR(?a), IF(?oa, "#fwd", "#bwd")) AS ?target)
    BIND(CONCAT(STR(?r), "#ba") AS ?id)
  }
}""" .
bench:microc a pgr:Network ; pgr:edgeQuery """
PREFIX era: <http://data.europa.eu/949/>
PREFIX nav: <http://data.europa.eu/949/concepts/navigabilities/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?id ?source ?target ?cost ?c_gauge ?c_electrified WHERE {
  {
    ?r a era:NetRelation ; era:elementA ?a ; era:elementB ?b ;
       era:isOnOriginOfElementA ?oa ; era:isOnOriginOfElementB ?ob ; era:navigability ?nav .
    FILTER(?nav IN (nav:AB, nav:Both))
    ?b era:lengthOfNetLinearElement ?cost ; era:isPartOf ?t .
    ?t era:wheelSetGauge ?g ; era:contactLineSystem ?cls .
    BIND(CONCAT(STR(?a), IF(?oa, "#bwd", "#fwd")) AS ?source)
    BIND(CONCAT(STR(?b), IF(?ob, "#fwd", "#bwd")) AS ?target)
    BIND(CONCAT(STR(?r), "#ab") AS ?id)
  } UNION {
    ?r a era:NetRelation ; era:elementA ?a ; era:elementB ?b ;
       era:isOnOriginOfElementA ?oa ; era:isOnOriginOfElementB ?ob ; era:navigability ?nav .
    FILTER(?nav IN (nav:BA, nav:Both))
    ?a era:lengthOfNetLinearElement ?cost ; era:isPartOf ?t .
    ?t era:wheelSetGauge ?g ; era:contactLineSystem ?cls .
    BIND(CONCAT(STR(?b), IF(?ob, "#bwd", "#fwd")) AS ?source)
    BIND(CONCAT(STR(?a), IF(?oa, "#fwd", "#bwd")) AS ?target)
    BIND(CONCAT(STR(?r), "#ba") AS ?id)
  }
  BIND(xsd:integer(STRAFTER(STR(?g), "nominal-track-gauges/")) AS ?c_gauge)
  BIND(?cls != <http://data.europa.eu/949/concepts/contact-line-systems/NotElectrified> AS ?c_electrified)
}""" .
}
