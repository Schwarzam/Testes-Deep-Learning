from dataclasses import dataclass

import splusdata
from tqdm import tqdm

import numpy as np
from astropy.io import fits

from src.auxiliar import *
import os

from src.log import control

def gen_dataset(
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
    df = conn.query(query)
    df = df.to_pandas()

    try:
        ## Usually the ID is a byte array
        df['ID'] = df['ID'].apply(lambda x: x.decode('utf-8'))
    except:
        pass

    df.to_csv('data.csv', index=False)
    stamps = []

    @dataclass
    class Mem_stamps_list:
        def __init__(self):
            self.stamps = {}
            self.count = 0
        
        def threadable_splus_stamp(self, ra, dec, size, band, res_identifier, filename = None, array_file = None):
            
            if
            
            if filename in not None and os.path.exists(filename):
            if os.path.exists(filename):
                stamp = fits.open(filename)
            else:
                stamp = conn.stamp(ra, dec, size, band)
                stamp.writeto(filename, overwrite=True)
            
            self.stamps[res_identifier] = stamp
            
            self.count += 1
            control.info(f"Stamp for {res_identifier} downloaded. {self.count}/{len(df)}")
    
    mem_list = Mem_stamps_list()
    
    control.info("Downloading stamps")
    for key, value in df.iterrows():
        res_id = value["ID"]
        fits_filename = os.path.join(fits_folder, f"{value['ID']}.fits.fz")
        control.submit(mem_list.threadable_splus_stamp, value["RA"], value["DEC"], 250, "R", res_id, fits_filename)
    control.wait()
    
    control.info("Saving data if not exists")
    for key, value in tqdm(df.iterrows()):
        
        # value["ID"] is the res_id from the threads
        stamp = mem_list.stamps[value["ID"]]
    
        if arrays_folder:
            array_file = os.path.join(arrays_folder, f"{value['ID']}.npy")
            if not os.path.exists(array_file, f"{value['ID']}.npy"):
                np.save(array_file, stamp[1].data)
        
        ## Close all stamps
        stamp.close()

    return df, stamps

if __name__ == "__main__":
    gen_dataset()