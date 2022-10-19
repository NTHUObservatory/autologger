import astropy.io.fits as pyfits
import os
import re
from itertools import groupby
from pprint import pprint
from datetime import datetime as dt

FILTER_MAP = {'Luminance': 'L',
              'Red': 'R',
              'Green': 'G',
              'Blue': 'B',
              'Ha': 'Ha',
              'OIII': 'OIII',
              'SII': 'SII'}

def walk(rootpath):
    fp_list = []
    for pwd, _, files in os.walk(rootpath):
        for file in files:
            if os.path.splitext(file)[1] in ['.fit', '.fits']:
                fp_list.append(os.path.join(pwd, file))
    return fp_list

def get_meta(filepath):
    filename = os.path.basename(filepath)
    raw_meta = os.path.splitext(filename)[0].split('_')
    meta = {}

    try:
        with open(filepath, 'rb') as f:
            fits = pyfits.open(f)[0]
            fits_header = fits.header
    except (FileNotFoundError, OSError):
        fits_header = None

    if fits_header:
        meta['filename'] = filename
        meta['time'] = dt.strptime(fits_header['DATE-LOC'], '%Y-%m-%dT%H:%M:%S.%f')
        meta['type'] = fits_header.get('IMAGETYP') or ''
        meta['target'] = fits_header.get('OBJECT') or meta['type']
        meta['filter'] = fits_header.get('FILTER') or ''
        meta['gain'] = str(fits_header['GAIN'] if 'GAIN' in fits_header else '')
        meta['exposure'] = str(fits_header['EXPOSURE'] if 'EXPOSURE' in fits_header else '')
        meta['sensortemp'] = str(fits_header['CCD-TEMP'] if 'CCD-TEMP' in fits_header else '')
        meta['binning'] = f'{fits_header.get("XBINNING")}x{fits_header.get("YBINNING")}'
        meta['software'] = fits_header.get('SWCREATE') or ''
        meta['number'] = raw_meta[8]
    else:
        meta['filename'] = filename
        meta['time'] = dt.strptime('_'.join(raw_meta[0:2]), '%Y-%m-%d_%H-%M-%S')
        meta['type'] = raw_meta[2]
        meta['target'] = raw_meta[3] or meta['type']
        meta['filter'] = raw_meta[4]
        meta['gain'] = ''
        meta['exposure'] = raw_meta[5].strip('s')
        meta['sensortemp'] = raw_meta[6].strip('C')
        meta['binning'] = raw_meta[7]
        meta['software'] = 'N.I.N.A.'
        meta['number'] = raw_meta[8]

    return meta

# A abstract class to represent a single image
class Image():
    def __init__(self, filepath):
        self.meta = get_meta(filepath)
        self.filepath = filepath
        self.filename = self.meta['filename']
        for k, v in self.meta.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Image {self.filename}>'

    @property
    def sortkey(self):
        return (self.target, self.filter, self.binning, self.exposure, self.time)

    @property
    def groupkey(self):
        return (self.target, self.filter, self.binning, self.exposure)

# A group of images that has the same target + filter + binning + exposure values.
class ImageGroup(tuple):
    def __new__(self, key, images, observer=''):
        return super(ImageGroup, self).__new__(self, tuple(key) + (len(images),) )

    def __init__(self, key, images, observer=''):
        self.time = images[0].time
        self.images = images
        self.observer = observer
        self.target = key[0]
        self.filter = key[1]
        self.binning = key[2]
        self.exposure = key[3]
        self.count = len(images)

    @property
    def groupkey(self):
        return (self.target, self.binning)

# A group of ImageGroups that is going to appear as a single line in the observation log
# This represents the images that has the same target + binning values.
# eg. In most cases, L with bin 1 and R, G, B with bin 2 would be represented by 2 separate ObsGroups.
class ObsGroup(list):
    def __init__(self, image_groups):
        self.image_groups = image_groups
        self.images = sum((x.images for x in image_groups), [])
        self.time = image_groups[0].time
        self.observer = image_groups[0].observer
        self.target = image_groups[0].target
        self.filters = ', '.join(FILTER_MAP[x.filter] for x in image_groups)
        self.binning = image_groups[0].binning
        self.exposure = ', '.join(str(x.exposure) for x in image_groups)
        self.total = sum(x.count for x in image_groups)
        counts = {str(x.count) for x in image_groups}
        self.count = (', '.join(counts) if len(image_groups) == 1 or len(counts) > 1
                      else ''.join(counts) + ' each')

        if len(image_groups) > 1:
            for x in (self.target, f'"{self.filters}"', self.binning, f'"{self.exposure}"', f'"{self.count}"'):
                self.append(x)
        else:
            for x in (self.target, self.filters, self.binning, self.exposure, self.count):
                self.append(x)

    def __repr__(self):
        return f'({", ".join(str(x) for x in self)})'

    @property
    def entry(self):
        return {'Date': self.time.date(),
                'Observer': self.observer,
                'Starting Time': self.time.strftime('%H:%M:%S'),
                'Target': self.target,
                'Filter': self.filters,
                'Binning': re.match(r'(\d)x\d', self.binning).group(1),
                'Gain': ', '.join({x.meta['gain'] for x in self.images}),
                'Exp. Time (s)': self.exposure,
                '# of Exp.': self.count,
                'Camera Temp.': ', '.join({x.meta['sensortemp']
                                           for x in self.images}),
                'Capture Software': ', '.join({('sftN' if x.meta['software'][:8] == 'N.I.N.A.' else
                                                x.meta['software'])
                                               for x in self.images})}

# A full sequence of observations in a day
class Sequence(list):
    def __init__(self, fp_list, observer=''):
        self.raw = fp_list
        self.orig = [Image(x) for x in fp_list]
        self.time_sorted = sorted(self.orig, key=lambda x: x.time)

        # Grouping a day's observations into different targets
        target_groups = []
        targets = []
        for k, g in groupby(self.time_sorted, key=lambda x: x.target):
            target_groups.append(list(g))
            targets.append(k)

        # Grouping each target's observations into different ImageGroup
        self.image_groups = []
        for group in target_groups:
            data = sorted(group, key=lambda x: x.sortkey)
            for k, g in groupby(data, key=lambda x: x.groupkey):
                images = list(g)
                self.image_groups.append(ImageGroup(k, images, observer))
        self.image_groups.sort(key=lambda x: x.time)

        # Grouping multiple ImageGroups into ObsGroups
        for k, g in groupby(self.image_groups, key=lambda x: x.groupkey):
            image_groups = list(g)
            self.append(ObsGroup(image_groups))
