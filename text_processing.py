from bs4 import BeautifulSoup
import re
import os
import csv


def find_strings(keywords, search_list):
    """ Searches for strings in a list and returns matches. This will be used to find 
    certain posting details from an aggregated list of options that users have when they create the post.
    Some are required like laundry and parking. Others are optional like flooring type, rent period, 
    pet info, AC, etc. 

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

# open csv
with open('CL_housing.csv', 'w', newline='', encoding='utf-8') as csvfile:
    # these were generated from the dictionary keys at the end of all this code and just copied up here
    fieldnames = ['post_id', 'title', 'price', 'neighborhood', 'map_address', 'street_address', 'latitude', 'longitude', 'data_accuracy', 'posted', 'updated', 'available', 'housing_type', 'bedrooms', 'bathooms',
                  'laundry', 'parking', 'sqft', 'flooring', 'rent_period', 'app_fee', 'broker_fee', 'cats_ok', 'dogs_ok', 'no_smoking', 'furnished', 'wheelchair_access', 'AC', 'EV_charging', 'posting_body', 'images', 'url']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # get file path for each html file in directory
    directory = 'craigslist'
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if not os.path.isfile(file_path):
            continue

        # open html and create soup
        with open(file_path, encoding='utf-8') as html_file:
            soup = BeautifulSoup(html_file, 'lxml')

        # get unique post ID 
        post_id = soup.find(string=re.compile("post id")).split(':')[1].strip()

        # get post url
        url = soup.find('link', rel='canonical').get('href')

        # find posting title text which will include pricing, post title, and neighborhood (optional)
        title_text = soup.find('span', class_="postingtitletext")

        # find pricing info, extract text, strip whitespace, remove non-integer characters
        price = title_text.find('span', class_="price").text.strip(
        ).replace("$", "").replace(",", "")

        # if neighborhood is included (doesn't have to be), will be found here in the title text
        post_hood = title_text.find('small')
        if post_hood is not None:
            neighborhood = post_hood.text
        else:
            neighborhood = "NA"

        # get availability date
        # I choose to grab the actual date instead of the text 'available jul 1' for example
        available = soup.find(
            class_="housing_movein_now property_date shared-line-bubble").get('data-date')

        # get map and address info
        mapbox = soup.find('div', class_='mapbox')
        latitude = mapbox.find(id='map').get('data-latitude')
        longitude = mapbox.find(id='map').get('data-longitude')
        # Not sure exactly what data_accuracy means in this context, 
        # but it varies a lot by post, so may be useful later
        data_accuracy = mapbox.find(id='map').get('data-accuracy')

        # some posts just have street address, others include nearby cross streets formatted as 
        # 'street address near street'. We account for both 
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

        # get urls for images if post has them
        images = []
        imgList = soup.find('div', id='thumbs')
        if imgList is not None:
            for tag in imgList.find_all('a'):
                img_url = tag.get('href')
                images.append(img_url)
        else:
            images = "NA"

        # this gets all the posting details that appear under the map. They look like tags, and are
        # the output of the user selecting specific options when they make the post. This gathers them in 
        # a 'specifications' list which we can search through. There are two instances of the class "attrgroup",
        # the first is always just the bed/bath, sqft(if provided), and availability. The second has all 
        # the other apt features. 
        attrgroup = soup.find_all('p', class_="attrgroup")
        specs = []
        for group in attrgroup:
            for item in group.find_all("span"):
                specs.append(item.text)

        # required information:
        bedbath = find_strings(["BR"], specs) 

        # all possible laundry options from drop down menu include either 'w/d', or 'laundry' so searching
        # for just those strings will return all possible matches
        laundry = find_strings(['w/d', 'laundry'], specs)
        # same for parking: there are a number of options but all accounted for by these 3 strings. 
        parking = find_strings(['parking', 'garage', 'carport'], specs)

        # optional details
        # possble housing options
        housing_type = ['apartment', 'condo', 'cottage', 'duplex', 'flat', 'house',
                        'in-law', 'loft', 'townhouse', 'manufactured', 'assisted', 'land']
        housing = find_strings(housing_type, specs)
        sqft = find_strings(['ft2'], specs)

        # the group of features/specifications that are formatted name: details
        # use our clean up function to makes things easier
        flooring = clean_if_exists(find_strings(['flooring'], specs))
        rent_period = clean_if_exists(find_strings(['rent'], specs))
        app_fee = clean_if_exists(find_strings(['application'], specs))
        broker_fee = clean_if_exists(find_strings(['broker'], specs))

        # the group of features that we just want to know if 'yes' or 'unspecified'
        cats_ok = yes_if_exists(find_strings(['cats'], specs))
        dogs_ok = yes_if_exists(find_strings(['dogs'], specs))
        no_smoking = yes_if_exists(find_strings(['smoking'], specs))
        furnished = yes_if_exists(find_strings(['furnished'], specs))
        wheelchair_access = yes_if_exists(find_strings(["wheelchair"], specs))
        AC = yes_if_exists(find_strings(['air'], specs))
        EV_charging = yes_if_exists(find_strings(['EV'], specs))

        # putting it all together in a dictionary. Some variable values get some additional cleaning or
        # type conversions. It's a little bit repetitive as we could have created the values directly in
        # the dictionary instead of defining all the variables above, but I think this is cleaner and 
        # easier to see what is going on
        post_details = {
            "post_id": post_id,
            "title": soup.title.text,
            "price": int(price),
            "neighborhood": neighborhood,
            "map_address": map_address,
            "street_address": street_address,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "data_accuracy": int(data_accuracy),
            "posted": posted.strip(),
            "updated": updated.strip(),
            "available": available.strip(),
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
            "url": url
        }

        # write each post dictionary to row
        writer.writerow(post_details)

csvfile.close()
