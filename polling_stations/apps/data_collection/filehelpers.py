import csv
import json
import shapefile
import tempfile
import zipfile

from collections import namedtuple

from django.contrib.gis.gdal import DataSource, GDALException


"""
Helper class for reading data from CSV files
"""
class CsvHelper:

    def __init__(self, filepath, encoding='utf-8', delimiter=','):
        self.filepath = filepath
        self.encoding = encoding
        self.delimiter = delimiter

    def get_features(self):
        file = open(self.filepath, 'rt', encoding=self.encoding)
        reader = csv.reader(file, delimiter=self.delimiter)
        header = next(reader)

        # mimic the data structure generated by ffs so existing import
        # scripts don't break
        replace = {
            ' ': '_',
            '-': '_',
            '.': '_',
            '(': '',
            ')': '',
        }
        clean = []
        for s in header:
            s = s.strip().lower()
            for k, v in replace.items():
                s = s.replace(k, v)
            while '__' in s:
                s = s.replace('__', '_')
            clean.append(s)
        RowKlass = namedtuple('RowKlass', clean)

        data = []
        for row in map(RowKlass._make, reader):
            data.append(row)

        file.close()
        return data


"""
Helper class for reading geographic data from ESRI SHP files
"""
class ShpHelper:

    def __init__(self, filepath):
        self.filepath = filepath

    def get_features(self):
        sf = shapefile.Reader(self.filepath)
        return sf.shapeRecords()


"""
Helper class for reading geographic data from GeoJSON files
"""
class GeoJsonHelper:

    def __init__(self, filepath):
        self.filepath = filepath

    def get_features(self):
        geometries = json.load(open(self.filepath))
        return geometries['features']


"""
Helper class for reading data from JSON files
"""
class JsonHelper:

    def __init__(self, filepath):
        self.filepath = filepath

    def get_features(self):
        return json.load(open(self.filepath))


"""
Helper class for reading geographic data from KML/KMZ files
"""
class KmlHelper:

    def __init__(self, filepath):
        self.filepath = filepath

    def parse_features(self, kml):
        try:
            ds = DataSource(kml)
        except GDALException:
            # This is very strange – sometimes the above will fail the first
            # time, but not the second. Seen on OS X with GDAL 2.2.0
            ds = DataSource(kml)
        return ds[0]

    def get_features(self):
        if not self.filepath.endswith('.kmz'):
            return self.parse_features(self.filepath)

        # It's a .kmz file
        # Because the C lib that the Django DataSource is wrapping
        # expects a file on disk, let's extract the KML to a tmpfile
        kmz = zipfile.ZipFile(self.filepath, 'r')
        kmlfile = kmz.open('doc.kml', 'r')

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(kmlfile.read())
            data = self.parse_features(tmp.name)
            tmp.close()
            return data


"""
Factory class for creating file helper objects.

If we add helper classes for more file types,
add an extra case to create()
"""
class FileHelperFactory():

    @staticmethod
    def create(filetype, filepath, options):
        if (filetype == 'shp'):
            return ShpHelper(filepath)
        elif (filetype == 'kml'):
            return KmlHelper(filepath)
        elif (filetype == 'geojson'):
            return GeoJsonHelper(filepath)
        elif filetype == 'json':
            return JsonHelper(filepath)
        elif (filetype == 'csv'):
            return CsvHelper(filepath, options['encoding'], options['delimiter'])
