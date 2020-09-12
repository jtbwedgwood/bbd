from typing import Dict, Union
from urllib.parse import urljoin
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import logging

import us
import requests

"""Maps year to congressional district number"""
CD = {
    2019: 116,
    2018: 116,
    2017: 115,
    2016: 115,
    2015: 114,
    2014: 114,
    2013: 113,
    2012: 113,
    2011: 112,
}


class Geography:
    """Geography available for download"""

    TRACT = "tract"
    CD = "cd"
    COUNTY = "county"
    STATE = "state"
    ZCTA = "zcta"
    BLOCK = "block"
    BLOCKGROUP = "blockgroup"


def shapefile_urls(fips: str, year=2019) -> Dict[str, str]:
    try:
        cd = CD[year]
    except KeyError:
        logging.warning(f"Unsupported year: {year}. Urls may be incorrect")
        cd = "xxx"

    base = f"https://www2.census.gov/geo/tiger/TIGER{year}/"
    urls = {
        "tract": urljoin(base, f"TRACT/tl_{year}_{fips}_tract.zip"),  # 2019
        "cd": urljoin(base, f"CD/tl_{year}_us_cd{cd}.zip"),  # 2019
        "county": urljoin(base, f"COUNTY/tl_{year}_us_county.zip"),
        "state": urljoin(base, f"STATE/tl_{year}_us_state.zip"),
        "zcta": urljoin(base, f"ZCTA5/tl_{year}_{fips}_zcta5.zip"),
        "block": urljoin(base, f"TABBLOCK/tl_{year}_{fips}_tabblock10.zip"),  # 14-19
        "blockgroup": urljoin(base, f"BG/tl_{year}_{fips}_bg.zip"),
    }

    return urls


def get_shapefile(
    geography: Geography, save_dir: str, state: Union[int, str], year: int,
) -> str:
    """Download and extract a census shapefile for a specified geography.
    Returns the name of the extracted directory.

    Shapefiles are also available directly from the US Census Bureau:
        https://www.census.gov/cgi-bin/geo/shapefiles/index.php
    """

    # Convert state to fips
    if isinstance(state, int):
        state_lookup = f"{state:02d}"  # Pad with leading zero, e.g. 8 -> "08"
    else:
        state_lookup = state

    us_state = us.states.lookup(state_lookup)

    if us_state is None:
        raise RuntimeError(
            f"Could not find the requested state: {state}."
            f"Looked up: {state_lookup}."
        )

    if us_state.fips is None:
        raise RuntimeError(f"The state of {us_state} does not contain a fips code :(")

    fips = us_state.fips

    # Get the shapefile URL
    url = shapefile_urls(fips, year)[geography]

    # Download and extract
    logging.info(f"downloading... {url}")

    r = requests.get(url, stream=True)
    if not r.ok:
        raise RuntimeError(f"Bad request. Status code: {r.status_code} {url}")

    with ZipFile(BytesIO(r.content)) as z:
        z.extractall(save_dir)

    # Return zip file name stem
    zip_name = url.split("/")[-1]
    return zip_name.split(".")[0]


if __name__ == "__main__":
    folder = Path(__file__).parent / "temp"
    state = "sc"
    year = 2019
    name = get_shapefile(Geography.BLOCK, folder, state, year)
    print(name)