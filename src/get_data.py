from dataclasses import dataclass

import splusdata
from tqdm import tqdm

import numpy as np
from astropy.io import fits

from src.auxiliar import *
import os

from src.log import control

def get_dataset_fieldimagequery(
    query : str = """
            SELECT 
            TOP 2000
            det.id, det.ra, det.dec, det.field, det.B, det.A, det.flux_radius_50, det.theta, det.fwhm,
            
            r.r_auto
            FROM "idr4_dual"."idr4_detection_image" AS det 
            
            LEFT OUTER JOIN "idr4_dual"."idr4_dual_r" AS r ON r.id = det.id
            
            WHERE 1 = CONTAINS( POINT('ICRS', det.ra, det.dec), 
                    CIRCLE('ICRS', 0.5, 0.4, 1) ) 
                    AND r.r_auto < 21
                    AND det.field = 'STRIPE82-0001'
    """,
    field_name: str = "STRIPE82-0001",
    fits_folder : str = "data/",
    arrays_folder : bool = None
):  
    
    if not os.path.exists(fits_folder):
        os.makedirs(fits_folder)
    if arrays_folder and not os.path.exists(arrays_folder):
        os.makedirs(arrays_folder)
    
    control.info("Insert splus.cloud credentials")
    conn = splusdata.Core()
    
    control.info("Querying data")
    df = conn.query(query, publicdata=True)
    control.info(f"Data found. {len(df)} rows.")
    df = df.to_pandas()

    field = df['field'].unique()
    ## IF more than one field is found, the query is wrong
    if len(field) > 1:
        control.critical(f"More than one field found. {field}")
        return
    
    control.info(f"Field {field[0]} found.")
    
    

def gen_dataset_cuts(
    query: str = """
            SELECT 
            TOP 2000
            det.id, det.ra, det.dec, det.field, det.B, det.A, det.flux_radius_50, det.theta, det.fwhm,
            
            r.r_auto
            FROM "idr4_dual"."idr4_detection_image" AS det 
            
            LEFT OUTER JOIN "idr4_dual"."idr4_dual_r" AS r ON r.id = det.id
            
            WHERE 1 = CONTAINS( POINT('ICRS', det.ra, det.dec), 
                    CIRCLE('ICRS', 0.5, 0.4, 1) ) 
                    AND r.r_auto < 21
    """,
    fits_folder : str = "data/",
    arrays_folder : bool = None
):  
    
    if not os.path.exists(fits_folder):
        os.makedirs(fits_folder)
    if arrays_folder and not os.path.exists(arrays_folder):
        os.makedirs(arrays_folder)
    
    control.info("Insert splus.cloud credentials")
    conn = splusdata.Core()
    
    control.info("Querying data")
    df = conn.query(query, publicdata=True)
    control.info(f"Data found. {len(df)} rows.")
    df = df.to_pandas()

    try:
        ## Usually the ID is a byte array
        df['ID'] = df['ID'].apply(lambda x: x.decode('utf-8'))
    except:
        pass

    df.to_csv('data.csv', index=False)
        
    def threadable_splus_stamp(ra, dec, size, band, filename = None, array_file = None):
        if filename is not None:
            if os.path.exists(filename):
                control.debug(f"Stamp for {ra} {dec} already exists.")
                stamp = fits.open(filename)
            else:
                stamp = conn.stamp(ra, dec, size, band)
                stamp.writeto(filename, overwrite=True)
                control.debug(f"Stamp for {ra} {dec} downloaded.")
        else:
            stamp = conn.stamp(ra, dec, size, band)
            control.debug(f"Stamp for {ra} {dec} downloaded.")
        if array_file:
            if os.path.exists(array_file):
                control.debug(f"Array for {ra} {dec} already exists.")
            else:
                np.save(array_file, stamp[1].data)
        
    control.info("Downloading stamps")
    for key, value in df.iterrows():
        fits_filename = os.path.join(fits_folder, f"{value['ID']}.fits.fz")
        array_file = os.path.join(arrays_folder, f"{value['ID']}.npy") if arrays_folder else None
        control.submit(threadable_splus_stamp, value["RA"], value["DEC"], 250, "R", fits_filename, array_file)
    control.wait()
    
    control.info("Finished generating dataset.")
    

if __name__ == "__main__":
    gen_dataset_cuts()