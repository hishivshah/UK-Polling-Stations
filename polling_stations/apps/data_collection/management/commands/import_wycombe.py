from django.contrib.gis.geos import Point
from data_collection.management.commands import BaseCsvStationsShpDistrictsImporter
from data_finder.helpers import geocode_point_only, PostcodeError

class Command(BaseCsvStationsShpDistrictsImporter):
    srid = 27700
    council_id = 'E07000007'
    districts_name = 'Polling Districts_region'
    stations_name = 'polling-stations.csv'
    elections = ['local.buckinghamshire.2017-05-04']

    def district_record_to_dict(self, record):
        return {
            'internal_council_id': str(record[0]).strip(),
            'name': str(record[4]).strip(),
        }

    def format_address(self, address):
        address_parts = address.split(',')
        postcode = address_parts[-1].strip()
        del(address_parts[-1])
        address_text = "\n".join([a.strip() for a in address_parts])
        return (address_text, postcode)

    def station_record_to_dict(self, record):
        codes = record.polling_district.split(', ')
        address, postcode = self.format_address(record.polling_place)

        try:
            point = geocode_point_only(postcode)
            location = Point(point['wgs84_lon'], point['wgs84_lat'], srid=4326)
        except PostcodeError:
            location = None

        stations = []
        for code in codes:
            stations.append({
                'internal_council_id': code,
                'address' : address,
                'postcode': postcode,
                'polling_district_id': code,
                'location': location,
            })
        return stations
