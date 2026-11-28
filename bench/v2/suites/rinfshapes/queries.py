"""The RINF query-shape suite's queries (tripletrail-bench #64), grouped by shape.

Each query has a rows form (the answer as a client gets it) and a count form (the same solutions,
counted on the server), so a report can tell the cost of the join from the cost of writing rows.
The count form is the rows form's pattern under `SELECT (COUNT(*) AS ?solutions)`; when the
rows form has a DISTINCT, GROUP BY, ORDER BY or LIMIT, the rows form goes in a subquery instead,
so both count the same solutions. An ablation control (`control_of`) is a top-k, facet or
valid-day query with patterns taken out: it shows which part of the query the time goes to.

The queries come from the research spike of tripletrail #297 and #298 (59 M triples of RINF), and
read the classes and properties of ERA's vocabulary as the RINF graphs use them.
"""

PREFIXES = """PREFIX era: <http://data.europa.eu/949/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX time: <http://www.w3.org/2006/time#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""
DEU = "<http://publications.europa.eu/resource/authority/country/DEU>"

SHAPES = {
    "facet": "Facet over a big class",
    "topk": "Top-k over a star",
    "star": "Star with combined filters",
    "chain": "Chain",
    "wide": "Wide table with OPTIONALs",
    "anti": "Anti-join",
    "valid": "Valid on a day",
    "control": "Ablation controls",
}


class Query:
    def __init__(self, id, shape, title, select, where, tail="", control_of=None):
        self.id, self.shape, self.title, self.control_of = id, shape, title, control_of
        self.select, self.where, self.tail = select, " ".join(where.split()), tail

    @property
    def rows(self):
        tail = f" {self.tail}" if self.tail else ""
        return f"{PREFIXES}SELECT {self.select} WHERE {{ {self.where} }}{tail}"

    @property
    def count(self):
        if self.tail or self.select.startswith("DISTINCT"):
            inner = f"SELECT {self.select} WHERE {{ {self.where} }} {self.tail}"
            return f"{PREFIXES}SELECT (COUNT(*) AS ?solutions) WHERE {{ {{ {inner} }} }}"
        return f"{PREFIXES}SELECT (COUNT(*) AS ?solutions) WHERE {{ {self.where} }}"


TRACK_DEU_GAUGING = f"?t a era:RunningTrack ; era:inCountry {DEU} ; era:gaugingProfile ?g ."
# "Valid on a day" as a client writes it today, without temporal support in the engine (tripletrail
# #311, the baseline of #303): an entity's era:validity is an interval whose beginning and end are
# instants with an xsd:date or an xsd:dateTimeStamp (Bane NOR writes the latter). An open end has no
# time:hasEnd. A date is read as midnight UTC, so dates and date-times compare as xsd:dateTime; the
# end day is still valid. An entity with several writings is valid when one of them is.
DAY = '"2026-11-28T00:00:00Z"^^xsd:dateTime'
INSTANT = "(time:inXSDDate|time:inXSDDateTimeStamp)"


def as_datetime(var):
    return (f'IF(DATATYPE(?{var}) = xsd:date, xsd:dateTime(CONCAT(STR(?{var}), "T00:00:00Z")), '
            f'xsd:dateTime(STR(?{var})))')


VALIDITY = f"""?e era:validity ?v . ?v time:hasBeginning/{INSTANT} ?b .
    OPTIONAL {{ ?v time:hasEnd/{INSTANT} ?end }}"""
VALID_ON_DAY = f"""{VALIDITY} BIND({as_datetime("b")} AS ?from) BIND({as_datetime("end")} AS ?to)
    FILTER(?from <= {DAY} && (!BOUND(?end) || ?to >= {DAY}))"""
SOL_LENGTH = "?sol a era:SectionOfLine ; era:inCountry ?c ; era:lengthOfSectionOfLine ?len ."

QUERIES = [
    Query("facet-gauging-deu", "facet", "German tracks per gauging profile",
          "?g (COUNT(?t) AS ?n)", TRACK_DEU_GAUGING, "GROUP BY ?g"),
    Query("facet-sol-length", "facet", "Sections of line per country, with the SUM of their length",
          "?c (SUM(?len) AS ?total) (COUNT(?sol) AS ?n)", SOL_LENGTH, "GROUP BY ?c"),
    Query("topk-speed-label", "topk", "The 20 fastest tracks, with their label",
          "?t ?v ?label", "?t a era:RunningTrack ; era:maximumPermittedSpeed ?v ; rdfs:label ?label .",
          "ORDER BY DESC(?v) LIMIT 20"),
    Query("topk-cant-speed", "topk", "The 20 tracks with the most cant deficiency, ordered on speed next",
          "?t ?cant ?v", "?t a era:RunningTrack ; era:cantDeficiency ?cant ; era:maximumPermittedSpeed ?v .",
          "ORDER BY DESC(?cant) DESC(?v) LIMIT 20"),
    Query("star-speed-cant-deu", "star", "German tracks with speed >= 160 and cant deficiency >= 150",
          "?t ?v", f"""?t a era:RunningTrack ; era:inCountry {DEU} ; era:maximumPermittedSpeed ?v ;
          era:cantDeficiency ?c . FILTER(?v >= 160 && ?c >= 150)"""),
    Query("star-bool-range", "star", "Tracks with speed >= 160, no level crossings, TSI magnetic fields",
          "?t ?v", """?t a era:RunningTrack ; era:maximumPermittedSpeed ?v ; era:hasLevelCrossings false ;
          era:tsiMagneticFields true . FILTER(?v >= 160)"""),
    Query("chain-track-op", "chain", "Track, section of line, start operational point, its name",
          "?t ?v ?sol ?len ?opname", """?t a era:RunningTrack ; era:maximumPermittedSpeed ?v ; era:isPartOf ?sol .
          ?sol era:lengthOfSectionOfLine ?len ; era:opStart ?op . ?op era:opName ?opname . FILTER(?v >= 160)"""),
    Query("chain-op-wkt", "chain", "Operational point, net reference, geometry, WKT",
          "?op ?name ?wkt", """?op a era:OperationalPoint ; rdfs:label ?name ; era:netReference ?nr .
          ?nr geo:hasGeometry ?g . ?g geo:asWKT ?wkt ."""),
    Query("wide-track-optional", "wide", "Tracks with label and 3 OPTIONAL properties",
          "?t ?label ?v ?cant ?dir", """?t a era:RunningTrack ; rdfs:label ?label .
          OPTIONAL { ?t era:maximumPermittedSpeed ?v } OPTIONAL { ?t era:cantDeficiency ?cant }
          OPTIONAL { ?t era:trackDirection ?dir }"""),
    Query("wide-op", "wide", "Operational points with label, country, location and OPTIONAL id",
          "?op ?name ?c ?pl ?u", """?op a era:OperationalPoint ; rdfs:label ?name ; era:inCountry ?c ;
          era:primaryLocation ?pl . OPTIONAL { ?op era:uopid ?u }"""),
    Query("anti-track-no-speed", "anti", "Tracks without a speed (NOT EXISTS)",
          "?t", "?t a era:RunningTrack . FILTER NOT EXISTS { ?t era:maximumPermittedSpeed ?v }"),
    Query("valid-day-sol", "valid", "Sections of line valid on 2026-11-28",
          "DISTINCT ?e", f"?e a era:SectionOfLine . {VALID_ON_DAY}"),
    Query("valid-day-op", "valid", "Operational points valid on 2026-11-28",
          "DISTINCT ?e", f"?e a era:OperationalPoint . {VALID_ON_DAY}"),
    Query("valid-day-track", "valid", "Running tracks valid on 2026-11-28",
          "DISTINCT ?e", f"?e a era:RunningTrack . {VALID_ON_DAY}"),
    Query("valid-day-any", "valid", "Anything valid on 2026-11-28, without a class",
          "DISTINCT ?e", VALID_ON_DAY),
    Query("control-topk-speed", "control", "Sort on the speed predicate alone",
          "?t ?v", "?t era:maximumPermittedSpeed ?v .", "ORDER BY DESC(?v) LIMIT 20",
          control_of="topk-speed-label"),
    Query("control-topk-cant", "control", "Sort on the cant deficiency predicate alone",
          "?t ?cant", "?t era:cantDeficiency ?cant .", "ORDER BY DESC(?cant) LIMIT 20",
          control_of="topk-cant-speed"),
    Query("control-facet-gauging-join", "control", "The German gauging join without GROUP BY",
          "?t ?g", TRACK_DEU_GAUGING, control_of="facet-gauging-deu"),
    Query("control-facet-gauging-noclass", "control", "The German gauging facet without the class",
          "?g (COUNT(?t) AS ?n)", f"?t era:inCountry {DEU} ; era:gaugingProfile ?g .", "GROUP BY ?g",
          control_of="facet-gauging-deu"),
    Query("control-valid-track-join", "control", "The tracks' validity join without the day filter",
          "DISTINCT ?e", f"?e a era:RunningTrack . {VALIDITY}", control_of="valid-day-track"),
    Query("control-facet-sol-join", "control", "The section-of-line join without GROUP BY",
          "?sol ?c ?len", SOL_LENGTH, control_of="facet-sol-length"),
]

BY_ID = {q.id: q for q in QUERIES}
assert len(BY_ID) == len(QUERIES), "query ids must be unique"
