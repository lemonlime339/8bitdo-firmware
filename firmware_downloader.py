import requests
import os
import hashlib
from typing import TypedDict, List, Iterable, Dict

# builds a directory structure in the form of
# - <device>
#   - <firmware version>
#       - <firmware>
#       - <readme>

FIRMWARE_LIST_HEADERS: Dict[str, str] = {}
FIRMWARE_LIST_URL = "http://dl.8bitdo.com:8080/firmware/select"

FIRMWARE_BETA_LIST_HEADERS: Dict[str, str] = {
    "beta": "1",
    "isLoadBeta": "1"
}
FIRMWARE_BETA_LIST_URL = "http://beta.8bitdo.com:8080/firmware/select"

EXPORT_BASE_DIR = "./firmware"

TYPE_TO_DEVICE_MAPPINGS = {
    1: "N30pro",
    2: "N30+F30",
    3: "SN30+SF30",
    4: "N30 ArcadeStick",
    5: "F30 Joystick",
    6: "Retro Receiver for Classic",
    7: "Retro Receiver for NES+SFC",
    8: "USB Adapter",
    9: "SN30pro+SF30pro",
    10: "N64",
    13: "N30 Pro 2",
    14: "M30 Modkit",
    15: "N30 Modkit",
    16: "SN30 Modkit",
    17: "SN30 V2",
    18: "N30 NS",
    20: "GBros Adapter",
    21: "USB Adapter for PS classic",
    22: "Retro Receiver for MD+Genesis",
    23: "M30",
    24: "P30 Modkit",
    25: "SN30 Pro+",
    26: "Dogbone Modkit",
    27: "S30 Modkit",
    28: "Lite",
    30: "Zero 2",
    31: "SN30 Pro Android",
    32: "Symphony Arcade",
    33: "Pro 2",
    34: "Arcade Stick",
    35: "Arcade Stick 2.5g Receiver",
    36: "Pro2 Wired for Xbox",
    37: "Pro2 Wired",
    39: "USB Adapter 2",
    40: "Ultimate Wired for Xbox",
    41: "Ultimate",
    42: "Ultimate Adapter",
    43: "Ultimate 2.4g",
    44: "Ultimate 2.4g Adapter",
    45: "Ultimate Wired",
    46: "Lite SE",
    47: "Lite 2"
}

class FirmwareEntry(TypedDict):
    url: str
    device: str
    version: str
    readme: str
    beta: bool
    frombetaserver: bool

def request_firmware_list():
    return requests.post(FIRMWARE_LIST_URL, headers=FIRMWARE_LIST_HEADERS).json()["list"]

def request_beta_firmware_list():
    return requests.post(FIRMWARE_BETA_LIST_URL, headers=FIRMWARE_BETA_LIST_HEADERS).json()["list"]

def _cmp_firmware_entry(a: FirmwareEntry, b: FirmwareEntry):
    return a["device"] == b["device"] \
        and a["version"] == b["version"] \
        and a["beta"] == b["beta"]

def _union_firmware_lists(a: List[FirmwareEntry], b: List[FirmwareEntry]):
    for y in b:
        if any(not _cmp_firmware_entry(x,y) for x in a):
            a.append(y)
    return a
    

def get_firmware_list():
    normal = request_firmware_list()
    beta   = request_beta_firmware_list()

    normal = transform_firmware_request_list(normal, False)
    beta = transform_firmware_request_list(beta, True)

    return _union_firmware_lists(normal, beta)


def version_to_string(v):
    return "%.2f" % v

def filepathname_to_url(f, beta):
    return requests.compat.urljoin(FIRMWARE_LIST_URL if not beta else FIRMWARE_BETA_LIST_URL, f)

def transform_firmware_request_list(firmware_list, from_beta_server) -> List[FirmwareEntry]:
    """
    returns a list of the firmwares: url, device, version, readme
    """
    return list({
        "url": filepathname_to_url(i['filePathName'], from_beta_server),
        "device": TYPE_TO_DEVICE_MAPPINGS[i["type"]],
        "version": version_to_string(i['version']),
        "readme": i["readme_en"].replace('\r', ''),
        "beta": i["beta"] != '',
    } for i in firmware_list)

def export_list(l: List[FirmwareEntry]):
    length = len(l)
    for count, ent in enumerate(l, start=1):
        version = ent["version"] + ('-beta' if ent["beta"] else '')
        new_dir = os.path.join(EXPORT_BASE_DIR, ent["device"], version)

        print(f"Processing: {new_dir} [{count}/{length}]")

        os.makedirs(new_dir, exist_ok=True)
        with open(os.path.join(new_dir, "readme.txt"), "w") as readme_file:
            readme_file.write(ent["readme"] + '\n')
        firmware_resp = requests.get(ent['url'])   
        firmware_data = firmware_resp.content
        with open(os.path.join(new_dir, ent['version']), "wb") as firmware_file:
            firmware_file.write(firmware_data)

if __name__ == "__main__":
    firmware_list = get_firmware_list()
    export_list(firmware_list)
