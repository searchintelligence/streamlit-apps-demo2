from enum import auto, Enum
import json
import os
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import sys
import time

import requests

import pandas as pd

from  unidecode import unidecode

class ServiceProvider(Enum):
    GEOCODEMAPS = auto()

class Geocoder:
    '''
    Geocoder class for geocoding address data

    Data is supplied via a csv file
    '''

    DEFAULT_ADDRESS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'addresses.csv')
    DEFAULT_ADDRESS_FILE_COLUMN_NAME = 'address'

    DEFAULT_MAX_THREADS = mp.cpu_count()

    DEFAULT_SAVE_COUNT = 15

    DEFAULT_WAIT_TIME_MEDIUM_SECONDS = 3
    DEFAULT_WAIT_TIME_SHORT_SECONDS = 1

    BASE_URLS = {
        ServiceProvider.GEOCODEMAPS: 'https://geocode.maps.co/search?q={}'
    }

    def __init__(self, location_hint:str = None, service_provider: ServiceProvider = ServiceProvider.GEOCODEMAPS, address_file_path: str = None, address_file_column_name: str = None, save_count: int = None, max_threads: int = None, wait_time: int = None):
        if location_hint is None:
            self.location_hint = ''
        else:
            self.location_hint = f', {location_hint}'
        self.service_provider = service_provider
        self.base_url = self.BASE_URLS[self.service_provider]

        if address_file_path is None:
            self.address_file_path = self.DEFAULT_ADDRESS_FILE_PATH
        else:
            self.address_file_path = address_file_path

        if address_file_column_name is None:
            self.address_file_column_name = self.DEFAULT_ADDRESS_FILE_COLUMN_NAME
        else:
            self.address_file_column_name = address_file_column_name

        self.addresses = self.load_address_data(self.address_file_path, self.address_file_column_name)

        if save_count is None:
            self.save_count = self.DEFAULT_SAVE_COUNT
        else:
            self.save_count = save_count

        if max_threads is None:
            self.max_threads = self.DEFAULT_MAX_THREADS
        else:
            self.max_threads = max_threads

        if wait_time is None:
            self.wait_time = self.DEFAULT_WAIT_TIME_SHORT_SECONDS
        else:
            self.wait_time = wait_time

        print(f'Geocoder initialised with location hint: {self.location_hint}, max threads: {self.max_threads}, wait time: {self.wait_time} second(s).')

    def load_address_data(self, file_path: str, column_name: str) -> list[str]:
        '''
        load address data as a data frame
        
        args:
            file_path (str): path to address data file
            column_name (str): name of column containing data
        '''

        print(f'loading addresses from {file_path}, using column "{column_name}".')

        address_df = pd.read_csv(file_path)
        addresses = list(set(address_df[column_name].values))
        
        return addresses
    
    def geocode_single_address_geocode_maps(self, address: str) -> dict:
        '''
        Geocode a single address string

        args:            
            address (str): address text
        '''
        
        url = self.base_url.format(address)
        response = requests.get(url)
        if response.status_code != 200:
            result = {}
        else:
            json_data  = response.json()
            result = [
                {
                    'address': address.replace('%20', ' '),
                    'place_id': row['place_id'],
                    'osm_id': row['osm_id'],
                    'lat': row['lat'],
                    'long': row['lon'],
                    'display_name': row['display_name'],
                    'class': row['class'],
                    'type': row['type'],
                } for row in json_data
            ]

        return result

    
    def geocode_multi_thread_worker(self, address: str) -> dict:
        '''
        Geocode a single address string

        args:            
            address (str): address text
        '''

        # add location hint to address        
        augmented_address = f'{address}{self.location_hint}'

        # clean address string
        address_clean = unidecode(augmented_address).lower().strip().replace(' ', '%20')

        if self.service_provider == ServiceProvider.GEOCODEMAPS:
            result = self.geocode_single_address_geocode_maps(address_clean)
        else:
            raise ValueError(f'Unsupported service provider used ({self.service_provider}).')
        
        time.sleep(self.wait_time)
        
        return result
    
    def geocode_addresses(self) -> pd.DataFrame:
        # multi-threaded geocoding
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            results = executor.map(self.geocode_multi_thread_worker, self.addresses)

        all_results = []
        for result in results:
            all_results.extend(result)            
        
        self.df = pd.DataFrame(all_results)

    def save_data(self, file_path: str):
        '''
        Save results dataframe to disk

        args:
            file_path (str): path of saved file
        '''
        self.df.to_csv(file_path, index=False)

def process_args(args: list) -> tuple[str, int, int]:
    '''
    process command line arguments used to call the module

    args:
        args (list): command line arguments list from sys.argv
    '''

    USAGE = 'python geocoder.py [-h|--hint] location_hint [-t|--t] max_threads [-w|--wait] wait_time'

    location_hint = None
    max_threads = None
    wait_time = None
    
    if len(sys.argv) > 1:
        args = sys.argv[1:]    
    
    while True:        
        if (args[0] == '-h') or (args[0] == '--hint'):
            location_hint = args[1]            
        elif (args[0] == '-t') or (args[0] == '-threads'):
            try:
                max_threads = int(args[1])
            except ValueError:
                print(f'unable to process argument value "{args[1]}" for thead count.')
                print(USAGE)
                print('Exiting.')
                sys.exit(1)
        elif (args[0] == '-w') or (args[0] == '--wait'):
            try:
                wait_time = int(args[1])
            except ValueError:
                print(f'unable to process argument value "{args[1]}" for wait time.')
                print(USAGE)
                print('Exiting.')
                sys.exit(1)

        args = args[2:]

        if len(args) == 0:
            break

    #print('l', location_hint)
    #print('t', max_threads)
    #print('w', wait_time)

    return location_hint, max_threads, wait_time

if __name__ == '__main__':

    location_hint, max_threads, wait_time = process_args(sys.argv)

    gc = Geocoder(location_hint=location_hint, max_threads=max_threads, wait_time=wait_time)
    gc.geocode_addresses()
    gc.save_data(os.path.join(os.path.dirname(__file__), 'geocoded_addresses.csv'))
