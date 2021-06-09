from bs4 import BeautifulSoup
import re
import os


def find_strings(keywords, search_list):
    """ Searches for strings in a list and returns matches. This will be used to find 
    certain posting details. Some are required like laundry and parking. Others are 
    optional like flooring, rent period, pet info, etc. 

    Parameters 
    ----------
    keywords : list
        A list of strings to search for

    search_list : list
        A list of strings to search in 


    Returns
    -------
    str
        Either the full string from the list or "NA" if doesn't exisit  
    """
    match = []
    for item in search_list:
        for s in keywords:
            if s in item:
                match.append(item)
    if len(match) == 0:
        return "NA"
    elif len(match) == 1:
        return ''.join(match)
    else:
        return match


def clean_if_exists(s):
    """For some posting details such as rent period, app fee, flooring etc., we only need the
    info to the right of the ':'. This function checks if this info is included in post (i.e. not "NA")
    and if so, splits and cleans it.

    Parameters
    ----------
    s : str
        The string to check and clean

    Returns
    -------
    str
        Either "NA" if input string is "NA" or split/stripped string 
    """
    if s != "NA":
        output = s.split(':')[1].strip()
        return output
    else:
        return s


def yes_if_exists(s):
    """For some posting details, such as pets, no smoking, furnished, if they aren't explicitly marked, 
    it doesn't neccessarily mean that's not true for the property. This function checks for the existence 
    of these details (checkbox options when making post) and assigns 'yes' if exists and 'NA' if not.

    Parameters
    ----------
    s : str
        The string to check

    Returns
    -------
    str
        Either 'NA' if input string is 'NA' or 'yes'
    """
    if s != "NA":
        return 'yes'
    else:
        return s


craigslist_data = {}

# get file path for each html file in directory
for file in os.listdir('craigslist'):
    file_path = os.path.join('craigslist', file)
    if not os.path.isfile(file_path):
        continue

    # open html and scrape data
    with open(file_path, encoding='utf-8') as html_file:
        soup = BeautifulSoup(html_file, 'lxml')

    # get unique post ID which will act as the key for each post dictionary
    post_id = soup.find(string=re.compile("post id")).split(':')[1].strip()

    # find posting title text which will include pricing, post title, and maybe neighborhood
    title_text = soup.find('span', class_="postingtitletext")

    price = title_text.find(
        'span', class_="price").text.strip().replace("$", "").replace(",", "")

    post_hood = title_text.find('small')
    if post_hood is not None:
        neighborhood = post_hood.text
    else:
        neighborhood = "NA"

    # get availability date
    available = soup.find(
        class_="housing_movein_now property_date shared-line-bubble").get('data-date')

    # get map and address info
    mapbox = soup.find('div', class_='mapbox')
    latitude = mapbox.find(id='map').get('data-latitude')
    longitude = mapbox.find(id='map').get('data-longitude')
    data_accuracy = mapbox.find(id='map').get('data-accuracy')
    map_address = mapbox.find(class_="mapaddress").text
    if "near" in map_address:
        street_address = map_address.split('near')[0]
    else:
        street_address = map_address

    # posting/updating dates and times
    posting_infos = soup.find('div', class_='postinginfos')
    timing = posting_infos.find_all('time', class_='date timeago')
    datetime = []
    for item in timing:
        datetime.append(item.text)
    # first item in list will be posting datetime
    posted = datetime[0]
    # any additional datetimes will be updates
    if len(datetime) > 1:
        updated = datetime[1]
    else:
        updated = "NA"

    # get body of post
    posting_body = soup.find('section', id="postingbody")

    # get urls for images
    images = []
    imgList = soup.find('div', id='thumbs')
    if imgList is not None:
        for tag in imgList.find_all('a'):
            img_url = tag.get('href')
            images.append(img_url)
    else:
        images = "NA"

    # this gets all the posting details that appear under the map
    attrgroup = soup.find_all('p', class_="attrgroup")
    specs = []
    for group in attrgroup:
        for item in group.find_all("span"):
            specs.append(item.text)

    # required information:
    bedbath = find_strings(["BR"], specs)
    laundry = find_strings(['w/d', 'laundry'], specs)
    parking = find_strings(['parking', 'garage', 'carport'], specs)

    # optional details
    housing_type = ['apartment', 'condo', 'cottage', 'duplex', 'flat', 'house',
                    'in-law', 'loft', 'townhouse', 'manufactured', 'assisted', 'land']
    housing = find_strings(housing_type, specs)

    sqft = find_strings(['ft2'], specs)

    flooring = clean_if_exists(find_strings(['flooring'], specs))

    rent_period = clean_if_exists(find_strings(['rent'], specs))

    app_fee = clean_if_exists(find_strings(['application'], specs))

    broker_fee = clean_if_exists(find_strings(['broker'], specs))

    cats_ok = yes_if_exists(find_strings(['cats'], specs))

    dogs_ok = yes_if_exists(find_strings(['dogs'], specs))

    no_smoking = yes_if_exists(find_strings(['smoking'], specs))

    furnished = yes_if_exists(find_strings(['furnished'], specs))

    wheelchair_access = yes_if_exists(find_strings(["wheelchair"], specs))

    AC = yes_if_exists(find_strings(['air'], specs))

    EV_charging = yes_if_exists(find_strings(['EV'], specs))

    post_details = {
        "title": soup.title.text,
        "price": int(price),
        "neighborhood": neighborhood,
        "map_address": map_address,
        "street_address": street_address,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "data_accuracy": int(data_accuracy),
        "post_date": post_date,
        "updated": updated,
        "available": available,
        "housing_type": housing,
        "bedrooms": bedbath.split('/')[0].strip(),
        "bathooms": bedbath.split('/')[1].strip(),
        "laundry": laundry,
        "parking": parking,
        "sqft": sqft,
        "flooring": flooring,
        "rent_period": rent_period,
        "app_fee": app_fee,
        "broker_fee": broker_fee,
        "cats_ok": cats_ok,
        "dogs_ok": dogs_ok,
        "no_smoking": no_smoking,
        "furnished": furnished,
        "wheelchair_access": wheelchair_access,
        "AC": AC,
        "EV_charging": EV_charging,
        "posting_body": posting_body.text.replace("\n", " "),
        "images": images,
        "url": soup.find('link', rel='canonical').get('href')

    }

    # add post entry to main dictionary
    craigslist_data[post_id] = post_details

print(craigslist_data)

# print(post)
