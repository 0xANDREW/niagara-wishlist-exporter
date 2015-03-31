import getpass
import pickle
import os
import csv

import requests
from bs4 import BeautifulSoup as bs4

PICKLE_FILE = 'session-pickled'
BASE_URL = 'http://www.niagaracycle.com'
LOGIN_POST_PATH = '/login.php?action=check_login'
WISHLIST_PATH = '/wishlist.php'

# Pickle session object to file
def dump_session(session):
    with open(PICKLE_FILE, 'w') as f:
        pickle.dump(session, f)

# Load session object from pickled file, create one if the file is invalid
def load_session():
    if os.path.exists(PICKLE_FILE):
        try:
            with open(PICKLE_FILE) as f:
                return pickle.load(f)
        except:
            return requests.Session()

    else:
        with open(PICKLE_FILE, 'a'):
            os.utime(PICKLE_FILE, None)
            
        return requests.Session()

# Check if redirected to login page, also set initial cookie
def is_logged_in(session):
    r = session.get(BASE_URL + WISHLIST_PATH)

    dump_session(session)

    return len(r.history) == 0

# Log in, save session
def login(session):
    email = raw_input('Email: ')
    password = getpass.getpass('Password: ')

    session.post(BASE_URL + LOGIN_POST_PATH, {
        'login_email': email,
        'login_pass': password
    })

    dump_session(session)

# Get list of wishlists from account    
def get_wishlists(session):
    r = session.get(BASE_URL + WISHLIST_PATH)
    soup = bs4(r.content)
    rv = []

    rows = soup.select('#wishlistsform table tr')

    for tr in rows:
        links = tr.select('a')

        if len(links) > 0:
            rv.append({
                'name': links[0].text,
                'path': links[0]['href']
            })

    return rv

# Allow user to select wishlist
def select_wishlist(lists):
    ct = 1

    for w in lists:
        print '[%d] %s' % (ct, w['name'])
        ct += 1

    num = int(raw_input('Select: '))

    return lists[num - 1]

# Write wishlist to CSV
def get_wishlist_csv(wl, session):
    csv_filename = '%s.csv' % wl['name'].replace(' ', '_')
    r = session.get('%s/%s' % (BASE_URL, wl['path']))
    soup = bs4(r.content)
    items = soup.select('ul.ProductList li')
    item_map = {}
    total = 0

    for li in items:
        link = li.select('.ProductDetails a')[0]
        name = link.text
        url = link['href']
        price = li.select('.ProductDetails em')[0].text

        if url not in item_map:
            item_map[url] = {
                'qty': 1,
                'name': name,
                'url': url,
                'price': price
            }
        else:
            item_map[url]['qty'] += 1

        total += float(price[1:])

    with open(csv_filename, 'wb') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow([ 'Name', 'Price', 'Qty', 'URL', 'Notes' ])

        for item in item_map:
            v = item_map[item]
            writer.writerow([ v['name'], v['price'], v['qty'], v['url']])

        writer.writerow([ '', '$%.02f' % total ])

if __name__ == '__main__':
    session = load_session()

    if not is_logged_in(session):
        login(session)

    lists = get_wishlists(session)
    wl = select_wishlist(lists)

    get_wishlist_csv(wl, session)
    
