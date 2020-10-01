# views.py is where we build our 'pages'. for example, we have our home page and our
# search results page in here.

from bs4 import BeautifulSoup
from craigslist import CraigslistForSale
from django.db.models import Q
from django.views.generic import TemplateView, ListView
from ebaysdk.finding import Connection as finding
from django_cron import CronJobBase, Schedule
from django.shortcuts import render
from array import *
import requests
import urllib.request
import time
import numpy as np
import pandas as pd
import json
from urllib.request import urlopen

from .models import ComputerPart, GraphicsCards, CPUs, SSDs, HDDs, RAM, Motherboards, powerSupplies, airCoolers, \
    HistoricalTracking, PartList
from .models import waterCoolers
from .facebookapi import getEntries
from datetime import datetime


# 'Home' is our home view, i.e. the page that initially loads before you search

class Home(TemplateView):
    template_name = 'home.html'


# 'Historical' is our historical database view, i.e. displays prices over time
def Historical(request):
    message = 'nothing'
    values = [0, 0, 0, 0, 0, 0, 0]
    values1 = 'nothing'
    model = 'gtx 1080'
    search_models = {
        'watercooler': waterCoolers, 'powersupply': powerSupplies,
        'cpu': CPUs, 'graphics': GraphicsCards, 'hdd': HDDs, 'ram': RAM, 'motherboard': Motherboards,
        'aircooler': airCoolers, 'ssd': SSDs
    }

    if request.method == 'GET':
        params = list(request.GET.values())
        if len(params) > 0:
            values = []
            model = params[2]
            partID = search_models[params[0]].objects.filter(model=params[2]).first().partID
            values1 = list(HistoricalTracking.objects.all().values('partID_' + str(partID)))
            for index, value in enumerate(values1):
                if index >= len(values1) - 7:
                    values.append(float(value['partID_' + str(partID)]))

    cpu = list(CPUs.objects.values_list('manufacturer', flat=True).distinct())
    cpuKeys = {}
    for c in cpu:
        cpuKeys[c] = list(CPUs.objects.filter(manufacturer=c).values_list('model', flat=True).distinct())

    graphics = list(GraphicsCards.objects.values_list('chipsetManufacturer', flat=True).distinct())
    graphicsKeys = {}
    for c in graphics:
        graphicsKeys[c] = list(
            GraphicsCards.objects.filter(chipsetManufacturer=c).values_list('model', flat=True).distinct())

    hdd = list(HDDs.objects.values_list('manufacturer', flat=True).distinct())
    hddKeys = {}
    for c in hdd:
        hddKeys[c] = list(HDDs.objects.filter(manufacturer=c).values_list('model', flat=True).distinct())

    ssd = list(SSDs.objects.values_list('manufacturer', flat=True).distinct())
    ssdKeys = {}
    for c in ssd:
        ssdKeys[c] = list(SSDs.objects.filter(manufacturer=c).values_list('model', flat=True).distinct())

    ram = list(RAM.objects.values_list('manufacturer', flat=True).distinct())
    ramKeys = {}
    for c in ram:
        ramKeys[c] = list(RAM.objects.filter(manufacturer=c).values_list('model', flat=True).distinct())

    motherboard = list(Motherboards.objects.values_list('manufacturer', flat=True).distinct())
    motherboardKeys = {}
    for c in motherboard:
        motherboardKeys[c] = list(
            Motherboards.objects.filter(manufacturer=c).values_list('model', flat=True).distinct())

    airCooler = list(airCoolers.objects.values_list('manufacturer', flat=True).distinct())
    airCoolerKeys = {}
    for c in airCooler:
        airCoolerKeys[c] = list(airCoolers.objects.filter(manufacturer=c).values_list('model', flat=True).distinct())

    waterCooler = list(waterCoolers.objects.values_list('manufacturer', flat=True).distinct())
    waterCoolerKeys = {}
    for c in waterCooler:
        waterCoolerKeys[c] = list(
            waterCoolers.objects.filter(manufacturer=c).values_list('model', flat=True).distinct())

    powerSupply = list(powerSupplies.objects.values_list('manufacturer', flat=True).distinct())
    powerSupplyKeys = {}
    for c in powerSupply:
        powerSupplyKeys[c] = list(
            powerSupplies.objects.filter(manufacturer=c).values_list('model', flat=True).distinct())

    context = {
        'cpu': json.dumps(cpuKeys),
        'graphics': json.dumps(graphicsKeys),
        'hdd': json.dumps(hddKeys),
        'ssd': json.dumps(ssdKeys),
        'ram': json.dumps(ramKeys),
        'motherboard': json.dumps(motherboardKeys),
        'aircooler': json.dumps(airCoolerKeys),
        'watercooler': json.dumps(waterCoolerKeys),
        'powersupply': json.dumps(powerSupplyKeys),
        'message': message,
        'values': values,
        'model': model
    }
    return render(request, 'historical.html', context)


class HistoricalView(TemplateView):
    template_name = 'historical.html'


# this class is our page for search results. After a search, this view appears.
# it also contains the functions that search ebay and craigslist.


class SearchResultsView(ListView):
    template_name = 'search_results.html'

    # not entirely sure what get_queryset is/does, but it's required for a ListView.
    # AFAIK must return a list. ours is object_list.
    # calls the ebay and craigslist search first, so that the DB is updated with the search results
    # before we query the DB.

    def get_queryset(self):
        ComputerPart.objects.filter(
            Q(website__icontains="EBAY") | Q(website__icontains="CRAIGSLIST") | Q(
                website__icontains="FACEBOOK")).delete()

        self.facebook_search()
        self.ebay_search()
        self.craigslist_search()
        # this sets the string 'query' to whatever was typed in the search bar

        query = self.request.GET.get('q')

        # this searches the DB table ComputerParts for any entry where the website field is
        # 'EBAY: ' or 'CRAIGSLIST: '.

        object_list = ComputerPart.objects.filter(
            Q(title__icontains=query) | Q(title__icontains=query))

        return object_list

    def craigslist_search(self):
        #   TODO: prevent duplicate entries into the DB
        # python-craigslist homepage tells how to get site, area, and category
        # the area is where you specify the city for a state. e.g.:
        #           site='colorado', area = 'fort-collins' (or something like that).
        # CraigslistForSale is the API for items for sale. There are others, but
        # they aren't useful for us AFAIK. category 'computer-parts' is a
        # craigslist native category. AFAIK that is the only one related to PC parts.
        # I think that there might be a 'computers' category as well.

        query = self.request.GET.get('q')

        cl = CraigslistForSale(site='newyork', area='', category='syp',
                               filters={'query': query})

        for result in cl.get_results(sort_by='newest', limit=999):
            title = result['name']
            price = result['price']
            price = price.replace("$", '')
            price = price.replace(",", '')
            title_parser(title, price)
            url = result['url']

            # this creates a new entry in the db with the specified values
            # TODO: website = 'CRAIGSLIST: ' in an effort to make the results more readable. Once we have a nice way to
            #   display the parts, we should change it to website = 'craigslist' or 'cl' or something. Same for ebay.

            # basic filtering for craiglist but its not quite working so its commented out
            part = ComputerPart(website='CRAIGSLIST', title=title, price=price, url=url)
            if query in title:
                part.save()  # save the DB
            else:
                pass

    def ebay_search(self):
        keywords = self.request.GET.get('q')  # keywords = input from search bar

        # call/hook into ebay "finding" API. appid is our token/key from the ebay dev account.

        api = finding(appid="JacobSil-PCChopSh-PRD-9ce6fb270-a362195a", config_file=None)
        api_request = {'keywords': keywords, 'sortOrder': 'BestMatch'}  # define the request keywords to be our keywords
        # Also added so that the results from ebay come back in a sorted order
        # This can be easily changed

        # this is where we actually search ebay. you can replace 'findItemsByKeywords' with other types
        # of searches. You'll have to look at the documentation for the API/ebaysdk to find out what those are.

        response = api.execute('findItemsByKeywords', api_request)

        # the API returns an xml document. To get the useful information, we will use BeautifulSoup to parse it.
        # each listing reported by the API begins with an 'item' tag. BeautifulSoup grabs all of the items,
        # and only the items, in the API response. then, we store it in a list, items.

        items = BeautifulSoup(response.content, 'lxml').find_all('item')

        for item in items:
            cat = item.categoryname.string.lower()
            title = item.title.string.lower()
            price = float(item.currentprice.string)
            title_parser(title, price)
            url = item.viewitemurl.string.lower()

            # If the part title does not contain the search keyword it is not added to database
            # Basic filtering

            part = ComputerPart(website='EBAY', title=title, price=price, url=url)  # create new entry
            if keywords in title:
                part.save()  # save the DB
            else:
                pass

    def facebook_search(self):
        keywords = self.request.GET.get('q')
        location = self.request.GET.get('fbl')
        if len(location) < 3:
            location = 'denver'
        results = getEntries(location, keywords)
        keys = list(results.keys())
        for key in keys:
            title = results[key]['title']
            part = ComputerPart(website='FACEBOOK', title=results[key]['title'], price=results[key]['price'],
                                url=results[key]['itemUrl'], pictureUrl=results[key]['imageUrl'],
                                location=results[key]['location'])  # create new entry
            price = part.price.replace("$", '')
            price = price.replace(",", '')
            title_parser(title, price)
            if keywords in title:
                part.save()  # save the DB
            else:
                pass


def log_part(partid, price, table_case):
    if table_case == 0:
        part = GraphicsCards.objects.get(partID=int(partid))
    if table_case == 1:
        part = waterCoolers.objects.get(partID=int(partid))
    if table_case == 2:
        part = airCoolers.objects.get(partID=int(partid))
    if table_case == 3:
        part = powerSupplies.objects.get(partID=int(partid))
    if table_case == 4:
        part = RAM.objects.get(partID=int(partid))
    if table_case == 5:
        part = Motherboards.objects.get(partID=int(partid))
    if table_case == 6:
        part = CPUs.objects.get(partID=int(partid))
    if table_case == 7:
        part = HDDs.objects.get(partID=int(partid))
    if table_case == 8:
        part = SSDs.objects.get(partID=int(partid))

    # card.count = 0
    # card.dailyAvgPrice = 0

    part.count = part.count + 1
    part.dailyTotalPrice = float(part.dailyTotalPrice) + float(price)

    part.save()


def title_parser(title, price):
    title = title.lower()
    # -----Graphics Cards------ #
    if "gtx" in title.lower() or "nvidia" in title.lower():
        if "1060" in title:
            log_part(96, price, 0)

        if "1050ti" in title or "1050 ti" in title:
            log_part(97, price, 0)
        if "1050" in title:
            log_part(98, price, 0)
        if "1070" in title:
            log_part(99, price, 0)
        if "1080" in title:
            if "hd" not in title and "tv" not in title and "monitor" not in title \
                    and "1080p" not in title:
                log_part(100, price, 0)
        if "1660ti" in title or "1660 ti" in title:
            log_part(101, price, 0)
        if "970" in title:
            log_part(102, price, 0)
        if "2060" in title:
            log_part(103, price, 0)
        if "1650" in title:
            log_part(104, price, 0)
    if "amd" in title or "radeon" in title or "rx" in title:
        if "570" in title:
            log_part(105, price, 0)

    # -----Water Coolers------ #
    if "water cooler" in title or "liquid cooler" in title or "cooler" in title:
        if "cooler master" in title:
            if "mounting bracket" not in title:
                if "ML420L RGB" in title:
                    log_part(11, price, 1)
        if "corsair" in title:
            if "mounting bracket" not in title:
                if "h100i" in title:
                    if "platinum" not in title:
                        if "pro" in title or "h100ipro" in title:
                            log_part(15, price, 1)
                    else:
                        log_part(12, price, 1)
                if "h150i" in title:
                    log_part(16, price, 1)
                if "h115i" in title:
                    log_part(21, price, 1)
        if "nzxt" in title:
            if "mounting bracket" not in title:
                if "kraken" in title:
                    if "x62" in title:
                        if "rev 2" in title:
                            log_part(13, price, 1)
                    if "x52" in title:
                        if "rev 2" in title:
                            log_part(14, price, 1)
                    if "z73" in title:
                        log_part(17, price, 1)
                    if "x72" in title:
                        log_part(19, price, 1)
                    if "M22" in title:
                        log_part(22, price, 1)

    # -----Air Coolers----- #

    if "air cooler" in title or "cpu cooler" in title or "cooler" in title:
        if "mounting bracket" not in title:
            if "amd" in title:
                if "Wraith Max" in title:
                    log_part(4, price, 2)
            if "be quiet" in title or "be quiet!" in title:
                if "dark rock" in title:
                    if "4" in title:
                        if "pro" in title:
                            log_part(2, price, 2)
                        else:
                            log_part(8, price, 2)
            if "cooler master" in title or "coolermaster" in title or "cm" in title:
                if "hyper 212" in title:
                    if "evo" in title:
                        log_part(0, price, 2)
                    if "RGB" in title:
                        log_part(1, price, 2)
                    if "Black" in title:
                        log_part(3, price, 2)
            if "noctua" in title:
                if "nh-l9i" in title or "nhl9i" in title or "nh l9i" in title:
                    log_part(9, price, 2)
                if "nh-d15" in title or "nhd15" in title or "nh d15" in title:
                    if "chromax.black" in title or "chromax" in title or "black" in title:
                        log_part(5, price, 2)
                    else:
                        log_part(6, price, 2)
                if "nh-u12s" in title or "nh u12s" in title or "nhu12s":
                    log_part(7, price, 2)

    # -------- Power Supplies -------- #
    if "power supply" in title or "psu" in title or "watt" in title:
        if "corsair" in title:
            if "rmx" in title:
                print("Corsair RMx")
                if "650" in title:
                    log_part(47, price, 3)
                if "850" in title:
                    log_part(48, price, 3)
            if "rm" in title:
                if "rmx" not in title:
                    log_part(43, price, 3)
            if "txm" in title:
                if "gold" in title:
                    log_part(55, price, 3)
            if "cxm" in title:
                log_part(44, price, 3)
        if "cooler master" in title or "coolermaster" in title or "cm" in title:
            if "mwe" in title:
                if "gold" in title:
                    log_part(53, price, 3)
        if "evga" in title:
            if "supernova" in title or "super nova" in title:
                if "GA" in title:
                    log_part(56, price, 3)
                if "g3" in title:
                    log_part(51, price, 3)
            else:
                if "br" in title:
                    log_part(49, price, 3)
                if "gd" in title:
                    log_part(54, price, 3)

    # ----- RAM ----- #
    if "ram" in title or "memory" in title or "random access memory" in title:
        if "corsair" in title:
            if "vengeance" in title:
                if "vengeance LPX" in title or "lpx" in title:
                    if "8 gb" in title or "8 g" in title or "8gb" in title or "1x8 gb" in title \
                            or "1 x 8 gb" in title or "1x8gb" in title or "1 x8gb" in title \
                            or "1 x8 gb" in title or "1x 8gb" in title or "1x 8 gb" in title \
                            or "1 x 8gb" in title:

                        if "2400 mhz" in title or "2400mhz" in title or "2400 m" in title \
                                or "2400 hz" in title or "2400hz" in title or "2400" in title:
                            log_part(41, price, 4)

                    if "16 gb" in title or "16 g" in title or "16gb" in title or "2x8 gb" in title \
                            or "2 x 8 gb" in title or "2x8gb" in title or "2 x8gb" in title \
                            or "2 x8 gb" in title or "2x 8gb" in title or "2x 8 gb" in title \
                            or "2 x 8gb" in title:

                        if "3000 mhz" in title or "3000mhz" in title or "3000 m" in title \
                                or "3000 hz" in title or "3000hz" in title or "3000" in title:
                            log_part(33, price, 4)
                        if "3200 mhz" in title or "3200mhz" in title or "3200 m" in title \
                                or "3200 hz" in title or "3200hz" in title or "3200" in title:
                            log_part(34, price, 4)
                        if "3600 mhz" in title or "3600mhz" in title or "3600 m" in title \
                                or "3600 hz" in title or "3600hz" in title or "3600" in title:
                            log_part(40, price, 4)

                    if "32 gb" in title or "32 g" in title or "32gb" in title or "2x16 gb" in title \
                            or "2 x 16 gb" in title or "2x16gb" in title or "2 x16gb" in title \
                            or "2 x16 gb" in title or "2x 16gb" in title or "2x 16 gb" in title \
                            or "2 x 16gb" in title:

                        if "3200 mhz" in title or "3200mhz" in title or "3200 m" in title \
                                or "3200 hz" in title or "3200hz" in title or "3200" in title:
                            log_part(38, price, 4)
                if "rgb pro" in title or "rgb" in title or "pro" in title:
                    if "16 gb" in title or "16 g" in title or "16gb" in title or "2x8 gb" in title \
                            or "2 x 8 gb" in title or "2x8gb" in title or "2 x8gb" in title \
                            or "2 x8 gb" in title or "2x 8gb" in title or "2x 8 gb" in title \
                            or "2 x 8gb" in title:

                        if "3200 mhz" in title or "3200mhz" in title or "3200 m" in title \
                                or "3200 hz" in title or "3200hz" in title or "3200" in title:
                            log_part(35, price, 4)

                    if "32 gb" in title or "32 g" in title or "32gb" in title or "2x16 gb" in title \
                            or "2 x 16 gb" in title or "2x16gb" in title or "2 x16gb" in title \
                            or "2 x16 gb" in title or "2x 16gb" in title or "2x 16 gb" in title \
                            or "2 x 16gb" in title:

                        if "3200 mhz" in title or "3200mhz" in title or "3200 m" in title \
                                or "3200 hz" in title or "3200hz" in title or "3200" in title:
                            log_part(36, price, 4)

        if "crucial" in title:
            if "kit" in title:
                if "16 gb" in title or "16 g" in title or "16gb" in title or "2x8 gb" in title \
                        or "2 x 8 gb" in title or "2x8gb" in title or "2 x8gb" in title \
                        or "2 x8 gb" in title or "2x 8gb" in title or "2x 8 gb" in title \
                        or "2 x 8gb" in title:
                    if "1600 mhz" in title or "1600mhz" in title or "1600 m" in title \
                            or "1600 hz" in title or "1600hz" in title or "1600" in title:
                        log_part(37, price, 4)

            if "ballistix Sport LT" in title or "ballistix" in title:
                if "16 gb" in title or "16 g" in title or "16gb" in title or "2x8 gb" in title \
                        or "2 x 8 gb" in title or "2x8gb" in title or "2 x8gb" in title \
                        or "2 x8 gb" in title or "2x 8gb" in title or "2x 8 gb" in title \
                        or "2 x 8gb" in title:

                    if "3200 mhz" in title or "3200mhz" in title or "3200 m" in title \
                            or "3200 hz" in title or "3200hz" in title or "3200" in title:
                        log_part(39, price, 4)

        if "timetec" in title:
            if "hynix" in title:
                if "ic" in title:
                    if "8 gb" in title or "8 g" in title or "8gb" in title or "1x8 gb" in title \
                            or "1 x 8 gb" in title or "1x8gb" in title or "1 x8gb" in title \
                            or "1 x8 gb" in title or "1x 8gb" in title or "1x 8 gb" in title \
                            or "1 x 8gb" in title:
                        if "1600 mhz" in title or "1600mhz" in title or "1600 m" in title \
                                or "1600 hz" in title or "1600hz" in title or "1600" in title:
                            log_part(42, price, 4)

    # ----- Motherboards ------ #
    if "motherboard" in title or "mobo" in title:
        if "msi" in title:
            if "b450" in title:
                if "tomahawk" in title:
                    if "max" in title:
                        log_part(57, price, 5)
            if "z390-a" in title or "z390a" in title or "z390 a" in title:
                if "pro" in title:
                    log_part(69, price, 5)

    # ------ CPUs -------- #
    ti = title.lower()
    if "amd" in ti and "laptop" not in ti:
        if "gaming desktop" or "gaming pc" not in ti:
            if "ryzen 3 1200" in ti:
                log_part(129, price, 6)
            if "ryzen 5 1400" in ti:
                log_part(106, price, 6)
            if "ryzen 5 1400x" in ti:
                print("ryzen 5 1400x")
            if "ryzen 5 1500x" in ti:
                log_part(107, price, 6)
            if "ryzen 5 1600" in ti:
                log_part(108, price, 6)
            if "ryzen 5 1600x" in ti:
                log_part(109, price, 6)
            if "ryzen 7 1700" in ti:
                log_part(110, price, 6)
            if "ryzen 7 1700x" in ti:
                log_part(111, price, 6)
            if "ryzen 7 1800x" in ti:
                log_part(112, price, 6)
            if "ryzen threadripper 1900x" in ti:
                log_part(113, price, 6)
            if "ryzen threadripper 1920x" in ti:
                log_part(114, price, 6)
            if "ryzen threadripper 1800x" in ti:
                log_part(115, price, 6)

    if "intel" in ti and "laptop" not in ti:
        if "gaming desktop" not in ti:
            if "gaming pc" not in ti:
                if "i9-9900k" in ti:
                    log_part(116, price, 6)
                if "i7-8086k" in ti:
                    log_part(117, price, 6)
                if "i7-8700k" in ti:
                    log_part(118, price, 6)
                if "i7-8700" in ti:
                    log_part(119, price, 6)
                if "i7-9700k" in ti:
                    log_part(120, price, 6)
                if "i5-8600k" in ti:
                    log_part(121, price, 6)
                if "i5-8500" in ti:
                    log_part(122, price, 6)
                if "i5-8400" in ti:
                    log_part(123, price, 6)
                if "i5-9400F" in ti:
                    log_part(124, price, 6)
                if "i5-9600k" in ti:
                    log_part(125, price, 6)
                if "i3-8350k" in ti:
                    log_part(126, price, 6)
                if "i3-8100" in ti:
                    log_part(127, price, 6)
                if "i3-9350kf" in ti:
                    log_part(128, price, 6)

    # -------HDDs-------- #
    ti = title.lower()
    if "western digital" in ti and "laptop" not in ti:
        if "gaming desktop" or "gaming pc" not in ti:
            if "caviar blue 1tb" in ti:
                log_part(84, price, 7)
            if "caviar blue 500gb" in ti:
                log_part(85, price, 7)
            if "caviar black 1tb" in ti:
                log_part(86, price, 7)
            if "caviar black 2tb" in ti:
                log_part(87, price, 7)
            if "caviar black 500gb" in ti:
                log_part(88, price, 7)
            if "caviar black 6tb" in ti:
                log_part(89, price, 7)
    if "seagate" in ti and "laptop" not in ti:
        if "gaming desktop" or "gaming pc" not in ti:
            if "barracuda 1tb" in ti:
                log_part(90, price, 7)
            if "barracuda compute 2tb" in ti:
                log_part(91, price, 7)
            if "barracuda compute pro 1tb" in ti:
                log_part(92, price, 7)
    if "toshiba" in ti and "laptop" not in ti:
        if "gaming desktop" or "gaming pc" not in ti:
            if "p300 1tb" in ti:
                log_part(93, price, 7)
            if "x300 5tb" in ti:
                log_part(94, price, 7)
            if "x300 4tb" in ti:
                log_part(95, price, 7)

    # -----SSDs------- #
    ti = title.lower()
    if "samsung" in ti and "laptop" not in ti:
        if "gaming desktop" or "gaming pc" not in ti:
            if "860 evo" in ti:
                log_part(23, price, 8)
            if "860 evo 1tb" in ti:
                log_part(25, price, 8)
            if "970 evo 500gb" in ti:
                log_part(27, price, 8)
            if "970 evo 1tb" in ti:
                log_part(30, price, 8)
            if "970 evo plus 1tb" in ti:
                log_part(32, price, 8)
    if "western digital" in ti and "laptop" not in ti:
        if "gaming desktop" or "gaming pc" not in ti:
            if "blue 3d nand 500gb" in ti:
                log_part(24, price, 8)
            if "blue 3d nand 1tb" in ti:
                log_part(26, price, 8)
    if "seagate" in ti and "laptop" not in ti:
        if "gaming desktop" or "gaming pc" not in ti:
            if "firecuda gaming sshd" in ti:
                log_part(28, price, 8)
    if "sandisk" in ti and "laptop" not in ti:
        if "gaming desktop" or "gaming pc" not in ti:
            if "ssd plus" in ti:
                log_part(29, price, 8)
    if "kingston" in ti and "laptop" not in ti:
        if "gaming desktop" or "gaming pc" not in ti:
            if "a400" in ti:
                log_part(31, price, 8)


class UpdateHistorical(CronJobBase):
    RUN_EVERY_MINS = 1440  # 24 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'views.UpdateHistorical'

    def do(self):
        print("Updated historical pricing")
        prices = array('f', [])
        # entry = HistoricalTracking(partID_1=prices[1], )

        # aircoolers
        search_terms = ["Hyper 212", "NH-U12S", "NH-L9I", "NH-D15", "Wraith Max", "Ryzen 1920x", "Ryzen 5 1400", "8700k"
                        , "8700", "8400", "Ryzen 1600x", "Ryzen 1500x", "Ryzen 1800x", "Ryzen 1900x", "Ryzen 1800x"
                        , "Ryzen 1200", "8086k", "Ryzen 1700", "8500", "Ryzen 1700x", "9400F", "8350K", "9350KF"
                        , "Ryzen 1600", "8600K", "8100", "9600K", "9700k", "9900K", "RTX 2060", "RX 570", "GTX 1660ti"
                        , "GTX 1050ti", "GTX 1050", "GTX 1080", "GTX 1070", "GTX 1650", "GTX 970", "GTX 1060"
                        , "Caviar Blue", "Caviar Black", "Toshiba P300", "Toshiba X300", "Seagate Barracuda"
                        , "MSI B450 TOMAHAWK MAX", "MSI Z390-A PRO", "Corsair RM", "Corsair CXM", "EVGA BR", "EVGA BQ"
                        , "MWE Gold", "EVGA GD", "TXM Gold", "EVGA SuperNova GA", "EVGA Supernova G3", "Vengeance LPX"
                        , "Crucial Kit", "Timetec Hynix IC", "Vengeance RGB PRO", "Ballistix Sport LT"
                        , "Samsung 860 Evo", "WD Blue 3D Nand", "Samsung 970 Evo", "Seagate Firecuda SSHD"
                        , "Sandisk SSD PLUS", "Kingston A400", "Samsung 970 Evo Plus", "Corsair H100I RGB"
                        , "ML420L RGB", "Kraken x62 Rev 2", "Kraken X52 Rev 2", "Corsair H100I Pro", "Corsair H150I Pro"
                        , "NZXT Kraken z73", "Corsair H60", "NZXT Kraken X72", "Corsair H100x", "Corsair H115I RGB"
                        , "NZXT Kraken M22"]

        # This loop searches for all parts we are tracking before logging prices to historical db
        for term in search_terms:  # TODO: Search code is copy/pasted. It shouldn't be.
            # ----------EBAY---------- #

            keywords = term
            api = finding(appid="JacobSil-PCChopSh-PRD-9ce6fb270-a362195a", config_file=None)
            api_request = {'keywords': keywords,
                           'sortOrder': 'BestMatch'}
            response = api.execute('findItemsByKeywords', api_request)
            items = BeautifulSoup(response.content, 'lxml').find_all('item')

            for item in items:
                cat = item.categoryname.string.lower()
                title = item.title.string.lower()
                price = float(item.currentprice.string)
                title_parser(title, price)
                url = item.viewitemurl.string.lower()

                part = ComputerPart(website='EBAY', title=title, price=price, url=url)  # create new entry
                if keywords in title:
                    part.save()  # save the DB
                else:
                    pass

            # -------CRAIGSLIST--------- #

            query = term

            cl = CraigslistForSale(site='newyork', area='', category='syp',
                                   filters={'query': query})

            for result in cl.get_results(sort_by='newest', limit=999):
                title = result['name']
                price = result['price']
                price = price.replace("$", '')
                price = price.replace(",", '')
                title_parser(title, price)
                url = result['url']
                part = ComputerPart(website='CRAIGSLIST', title=title, price=price, url=url)
                if query in title:
                    part.save()  # save the DB
                else:
                    pass

            # -------FACEBOOK------- #
            location = 'denver'  # TODO: Location is static. It shouldn't be.
            results = getEntries(location, keywords)
            keys = list(results.keys())
            for key in keys:
                title = results[key]['title']
                part = ComputerPart(website='FACEBOOK', title=results[key]['title'], price=results[key]['price'],
                                    url=results[key]['itemUrl'], pictureUrl=results[key]['imageUrl'],
                                    location=results[key]['location'])  # create new entry
                price = part.price.replace("$", '')
                price = price.replace(",", '')
                title_parser(title, price)
                if keywords in title:
                    part.save()  # save the DB
                else:
                    pass

        for count in range(0, 10):
            airCooler = airCoolers.objects.get(partID=count)
            if float(airCooler.count) != 0:
                prices.append((float(airCooler.dailyTotalPrice) / float(airCooler.count)))
            else:
                prices.append(0)
            airCooler.count = 0
            airCooler.dailyTotalPrice = 0

        # watercoolers
        for count in range(10, 23):
            waterCooler = waterCoolers.objects.get(partID=count)
            if float(waterCooler.count) != 0:
                prices.append(float(waterCooler.dailyTotalPrice) / float(waterCooler.count))
            else:
                prices.append(0)
            waterCooler.count = 0
            waterCooler.dailyTotalPrice = 0

        # Cpus
        for count in range(106, 130):
            cpu = CPUs.objects.get(partID=count)
            if float(cpu.count) != 0:
                prices.append(float(cpu.dailyTotalPrice) / float(cpu.count))
            else:
                prices.append(0)
            cpu.count = 0
            cpu.dailyTotalPrice = 0

        # gpus
        for count in range(96, 106):
            gpu = GraphicsCards.objects.get(partID=count)
            if float(gpu.count) != 0:
                prices.append(float(gpu.dailyTotalPrice) / float(gpu.count))
            else:
                prices.append(0)
            gpu.count = 0
            gpu.dailyTotalPrice = 0
            count = count + 1
        # mobos
        for count in range(57, 84):
            mobo = Motherboards.objects.get(partID=count)
            if float(mobo.count) != 0:
                prices.append(float(mobo.dailyTotalPrice) / float(mobo.count))
            else:
                prices.append(0)
            mobo.count = 0
            mobo.dailyTotalPrice = 0

        # hdds
        for count in range(84, 96):
            hdd = HDDs.objects.get(partID=count)
            if float(hdd.count) != 0:
                prices.append(float(hdd.dailyTotalPrice) / float(hdd.count))
            else:
                prices.append(0)
            hdd.count = 0
            hdd.dailyTotalPrice = 0

        # ssds
        for count in range(23, 33):
            ssd = SSDs.objects.get(partID=count)
            if float(ssd.count) != 0:
                prices.append(float(ssd.dailyTotalPrice) / float(ssd.count))
            else:
                prices.append(0)
            ssd.count = 0
            ssd.dailyTotalPrice = 0
        # psu
        for count in range(43, 57):
            psu = powerSupplies.objects.get(partID=count)
            if float(psu.count) != 0:
                prices.append(float(psu.dailyTotalPrice) / float(psu.count))
            else:
                prices.append(0)
            psu.count = 0
            psu.dailyTotalPrice = 0

        # ram
        for count in range(33, 43):
            ram = RAM.objects.get(partID=count)
            if float(ram.count) != 0:
                prices.append(float(ram.dailyTotalPrice) / float(ram.count))
            else:
                prices.append(0)
            ram.count = 0
            ram.dailyTotalPrice = 0

        entry = HistoricalTracking(date=datetime.date(datetime.now()), partID_0=prices[0], partID_1=prices[1],
                                   partID_2=prices[2], partID_3=prices[3],
                                   partID_4=prices[4], partID_5=prices[5], partID_6=prices[6],
                                   partID_7=prices[7], partID_8=prices[8], partID_9=prices[9], partID_10=prices[10],
                                   partID_11=prices[11], partID_12=prices[12], partID_13=prices[13],
                                   partID_14=prices[14], partID_15=prices[15], partID_16=prices[16],
                                   partID_17=prices[17], partID_18=prices[18], partID_19=prices[19],
                                   partID_20=prices[20],
                                   partID_21=prices[21], partID_22=prices[22], partID_23=prices[23],
                                   partID_24=prices[24],
                                   partID_25=prices[25], partID_26=prices[26], partID_27=prices[27],
                                   partID_28=prices[28],
                                   partID_29=prices[29],
                                   partID_30=prices[30], partID_31=prices[31], partID_32=prices[32],
                                   partID_33=prices[33], partID_34=prices[34], partID_35=prices[35],
                                   partID_36=prices[36],
                                   partID_37=prices[37], partID_38=prices[38], partID_39=prices[39],
                                   partID_40=prices[40], partID_41=prices[41], partID_42=prices[42],
                                   partID_43=prices[43],
                                   partID_44=prices[44],
                                   partID_45=prices[45], partID_46=prices[46], partID_47=prices[47],
                                   partID_48=prices[48], partID_49=prices[49], partID_50=prices[50],
                                   partID_51=prices[51],
                                   partID_52=prices[52], partID_53=prices[53], partID_54=prices[54],
                                   partID_55=prices[55], partID_56=prices[56], partID_57=prices[57],
                                   partID_58=prices[58],
                                   partID_59=prices[59], partID_60=prices[60], partID_61=prices[61],
                                   partID_62=prices[62], partID_63=prices[63], partID_64=prices[64],
                                   partID_65=prices[65],
                                   partID_66=prices[66], partID_67=prices[67], partID_68=prices[68],
                                   partID_69=prices[69], partID_70=prices[70], partID_71=prices[71],
                                   partID_72=prices[72],
                                   partID_73=prices[73], partID_74=prices[74], partID_75=prices[75],
                                   partID_76=prices[76], partID_77=prices[77], partID_78=prices[78],
                                   partID_79=prices[79],
                                   partID_80=prices[80], partID_81=prices[81], partID_82=prices[82],
                                   partID_83=prices[83], partID_84=prices[84], partID_85=prices[85],
                                   partID_86=prices[86],
                                   partID_87=prices[87], partID_88=prices[88], partID_89=prices[89],
                                   partID_90=prices[90], partID_91=prices[91], partID_92=prices[92],
                                   partID_93=prices[93],
                                   partID_94=prices[94], partID_95=prices[95], partID_96=prices[96],
                                   partID_97=prices[97], partID_98=prices[98], partID_99=prices[99],
                                   partID_100=prices[100],
                                   partID_101=prices[101], partID_102=prices[102], partID_103=prices[103],
                                   partID_104=prices[104], partID_105=prices[105], partID_106=prices[106],
                                   partID_107=prices[107],
                                   partID_108=prices[108], partID_109=prices[109], partID_110=prices[110],
                                   partID_111=prices[111], partID_112=prices[112], partID_113=prices[113],
                                   partID_114=prices[114],
                                   partID_115=prices[115], partID_116=prices[116], partID_117=prices[117],
                                   partID_118=prices[118], partID_119=prices[119], partID_120=prices[120],
                                   partID_121=prices[121],
                                   partID_122=prices[122], partID_123=prices[123], partID_124=prices[124],
                                   partID_125=prices[125], partID_126=prices[126], partID_127=prices[127],
                                   partID_128=prices[128],
                                   partID_129=prices[129])
        entry.save()
        print("done")


#  ----- Inserting data into db tables --------  #

#  ---- Graphics Cards ----  #
# https://store.steampowered.com/hwsurvey/videocard/
""""
card = GraphicsCards(chipsetManufacturer='NVIDIA', model='1060', count=0)
card.save()
card = GraphicsCards(chipsetManufacturer='NVIDIA', model='1050ti', count=0)
card.save()
card = GraphicsCards(chipsetManufacturer='NVIDIA', model='1050', count=0)
card.save()
card = GraphicsCards(chipsetManufacturer='NVIDIA', model='1070', count=0)
card.save()
card = GraphicsCards(chipsetManufacturer='NVIDIA', model='1080', count=0)
card.save()
card = GraphicsCards(chipsetManufacturer='NVIDIA', model='1660ti', count=0)
card.save()
card = GraphicsCards(chipsetManufacturer='NVIDIA', model='970', count=0)
card.save()
card = GraphicsCards(chipsetManufacturer='NVIDIA', model='2060', count=0)
card.save()
card = GraphicsCards(chipsetManufacturer='NVIDIA', model='1650', count=0)
card.save()
card = GraphicsCards(chipsetManufacturer='AMD', model='RX 570', count=0)
card.save()
#  ---- SSDs ----  #
#  https://www.amazon.com/Best-Sellers-Computers-Accessories-Internal-Solid-State-Drives/zgbs/pc/1292116011
drive = SSDs(manufacturer='Samsung', model='860 Evo', size=500000000000, count=0)
drive.save()
drive = SSDs(manufacturer='WD Blue', model='3D Nand', size=500000000000, count=0)
drive.save()
drive = SSDs(manufacturer='Samsung', model='860 Evo', size=1000000000000, count=0)
drive.save()
drive = SSDs(manufacturer='WD Blue', model='3D Nand', size=1000000000000, count=0)
drive.save()
drive = SSDs(manufacturer='Samsung', model='970 Evo', size=500000000000, count=0)
drive.save()
drive = SSDs(manufacturer='Seagate', model='FireCuda Gaming SSHD', size=2000000000000, count=0)
drive.save()
drive = SSDs(manufacturer='Sandisk', model='SSD PLUS', size=1000000000000, count=0)
drive.save()
drive = SSDs(manufacturer='Samsung', model='970 Evo', size=1000000000000, count=0)
drive.save()
drive = SSDs(manufacturer='Kingston', model='A400', size=480000000000, count=0)
drive.save()
drive = SSDs(manufacturer='Samsung', model='970 Evo Plus', size=1000000000000, count=0)
drive.save()
#  ---- RAM ----  #
#  https://www.amazon.com/Best-Sellers-Computers-Accessories-Computer-Memory/zgbs/pc/172500
memory = RAM(manufacturer='Corsair', model='Vengeance LPX', size=16000000000,
             memorySplit='2x8', frequency=3000, count=0)
memory.save()
memory = RAM(manufacturer='Corsair', model='Vengeance LPX', size=16000000000,
             memorySplit='2x8', frequency=3200, count=0)
memory.save()
memory = RAM(manufacturer='Corsair', model='Vengeance RGB PRO', size=16000000000,
             memorySplit='2x8', frequency=3200, count=0)
memory.save()
memory = RAM(manufacturer='Corsair', model='Vengeance RGB PRO', size=32000000000,
             memorySplit='2x16', frequency=3200, count=0)
memory.save()
memory = RAM(manufacturer='Crucial', model='Kit', size=16000000000,
             memorySplit='2x8', frequency=1600, count=0)
memory.save()
memory = RAM(manufacturer='Corsair', model='Vengeance LPX', size=32000000000,
             memorySplit='2x16', frequency=3200, count=0)
memory.save()
memory = RAM(manufacturer='Crucial', model='Ballistix Sport LT', size=16000000000,
             memorySplit='2x8', frequency=3200, count=0)
memory.save()
memory = RAM(manufacturer='Corsair', model='Vengeance LPX', size=16000000000,
             memorySplit='2x8', frequency=3600, count=0)
memory.save()
memory = RAM(manufacturer='Corsair', model='Vengeance LPX', size=8000000000,
             memorySplit='1x8', frequency=2400, count=0)
memory.save()
memory = RAM(manufacturer='Timetec', model='Hynix IC', size=8000000000,
             memorySplit='1x8', frequency=1600, count=0)
memory.save()
#  ---- motherboards ----  #
#  FIXME: I don't have the CPU table yet, so the CPU ID is a placeholder value,
#   must match mobos with CPU ID's. Also, only 1 mobo per CPU right now
mobo = Motherboards(cpuID=0, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=1, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=2, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=3, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=4, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=5, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=6, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=7, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=8, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=9, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=10, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=11, manufacturer='MSI', model='B450 TOMAHAWK MAX', count=0)
mobo.save()
mobo = Motherboards(cpuID=12, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=13, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=14, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=15, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=16, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=17, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=18, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=19, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=20, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=21, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=22, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=23, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=24, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=25, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
mobo = Motherboards(cpuID=26, manufacturer='MSI', model='Z390-A PRO', count=0)
mobo.save()
hdd = HDDs(hddID=0, manufacturer='WD', model='Caviar Blue 1TB ', size =1000000000000 , count=0)
hdd.save()
hdd = HDDs(hddID=1, manufacturer='WD', model='Caviar Blue 500Gb ', size =500000000000,  count=0)
hdd.save()
hdd = HDDs(hddID=2, manufacturer='WD', model='Caviar Black 1TB ', size =1000000000000,  count=0)
hdd.save()
hdd = HDDs(hddID=3, manufacturer='WD', model='Caviar Black 2TB ', size =2000000000000,  count=0)
hdd.save()
hdd = HDDs(hddID=4, manufacturer='WD', model='Caviar Black 500Gb ', size =500000000000,  count=0)
hdd.save()
hdd = HDDs(hddID=5, manufacturer='WD', model='Caviar Black 6TB ', size =6000000000000,  count=0)
hdd.save()
hdd = HDDs(hddID=6, manufacturer='Segate', model='Barracuda 1TB', size =1000000000000 , count=0)
hdd.save()
hdd = HDDs(hddID=7, manufacturer='Segate', model='Barracuda Compute 2Tb', size =2000000000000,  count=0)
hdd.save()
hdd = HDDs(hddID=8, manufacturer='Segate', model='Barracuda Compute Pro 1Tb', size =1000000000000,  count=0)
hdd.save()
hdd = HDDs(hddID=9, manufacturer='Toshiba', model='P300', size =1000000000000,  count=0)
hdd.save()
hdd = HDDs(hddID=10, manufacturer='Toshiba', model='X300 5Tb', size =5000000000000,  count=0)
hdd.save()
hdd = HDDs(hddID=11, manufacturer='Toshiba', model='X300 4Tb', size =4000000000000 , count=0)
hdd.save()
# Powersupplies
ps = powerSupplies(supplyID=0, manufacturer='Corsair', model='RM', wattage = 750 , count=0)
ps.save()
ps = powerSupplies(supplyID=1, manufacturer='Corsair', model='CXM', wattage = 550 , count=0)
ps.save()
ps = powerSupplies(supplyID=2, manufacturer='EVGA', model='BR', wattage = 500 , count=0)
ps.save()
ps = powerSupplies(supplyID=3, manufacturer='EVGA', model='BQ', wattage = 600,  count=0)
ps.save()
ps = powerSupplies(supplyID=4, manufacturer='Corsair', model='RMx', wattage = 650,  count=0)
ps.save()
ps = powerSupplies(supplyID=5, manufacturer='Corsair', model='RMx', wattage = 850,  count=0)
ps.save()
ps = powerSupplies(supplyID=6, manufacturer='EVGA', model='BR', wattage = 450,  count=0)
ps.save()
ps = powerSupplies(supplyID=7, manufacturer='Corsair', model='RM', wattage = 650,  count=0)
ps.save()
ps = powerSupplies(supplyID=8, manufacturer='EVGA', model='superNOVA G3', wattage = 750,  count=0)
ps.save()
ps = powerSupplies(supplyID=9, manufacturer='EVGA', model='BR', wattage = 600,  count=0)
ps.save()
ps = powerSupplies(supplyID=10, manufacturer='Cooler Master', model='MWE Gold', wattage = 650,  count=0)
ps.save()
ps = powerSupplies(supplyID=11, manufacturer='EVGA', model='GD', wattage = 600,  count=0)
ps.save()
ps = powerSupplies(supplyID=12, manufacturer='Corsair', model='TXM Gold', wattage = 550,  count=0)
ps.save()
ps = powerSupplies(supplyID=13, manufacturer='EVGA', model='superNova GA', wattage = 650,  count=0)
ps.save()
# Air Coolers
ac = airCoolers(coolerID=0, manufacturer='CoolerMaster', model='Hyper 212 Evo',count=0)
ac.save()
ac = airCoolers(coolerID=1, manufacturer='CoolerMaster', model='Hyper 212 RGB',count=0)
ac.save()
ac = airCoolers(coolerID=2, manufacturer='Be Quiet!', model='Dark Rock Pro 4',count=0)
ac.save()
ac = airCoolers(coolerID=3, manufacturer='CoolerMaster', model='Hyper 212 Black',count=0)
ac.save()
ac = airCoolers(coolerID=4, manufacturer='AMD', model='Wraith Max',count=0)
ac.save()
ac = airCoolers(coolerID=5, manufacturer='Noctua', model='NH-D15 Chromax.BLACK',count=0)
ac.save()
ac = airCoolers(coolerID=6, manufacturer='Noctua', model='NH-D15',count=0)
ac.save()
ac = airCoolers(coolerID=7, manufacturer='Noctua', model='NH-U12S Chromax.BLACK',count=0)
ac.save()
ac = airCoolers(coolerID=8, manufacturer='Be Quiet !', model='Dark Rock 4',count=0)
ac.save()
ac = airCoolers(coolerID=9, manufacturer='Noctua', model='NH-L9I',count=0)
ac.save()
# Water Coolers
wc = waterCoolers(coolerID=0, manufacturer='Corsair', model='H100I RGB',count=0)
wc.save()
wc = waterCoolers(coolerID=1, manufacturer='Cooler Master', model='ML420L RGB',count=0)
wc.save()
wc = waterCoolers(coolerID=2, manufacturer='Corsair', model='H100I RGB SE',count=0)
wc.save()
wc = waterCoolers(coolerID=3, manufacturer='NZXT', model='Kraken X62 Rev 2',count=0)
wc.save()
wc = waterCoolers(coolerID=4, manufacturer='NZXT', model='Kraken X52 Rev 2',count=0)
wc.save()
wc = waterCoolers(coolerID=5, manufacturer='Corsair', model='H100I Pro',count=0)
wc.save()
wc = waterCoolers(coolerID=6, manufacturer='Corsair', model='H150I Pro',count=0)
wc.save()
wc = waterCoolers(coolerID=7, manufacturer='NZXT', model='Kraken z73',count=0)
wc.save()
wc = waterCoolers(coolerID=8, manufacturer='Corsair', model='H60',count=0)
wc.save()
wc = waterCoolers(coolerID=9, manufacturer='NZXT', model='Kraken X72',count=0)
wc.save()
wc = waterCoolers(coolerID=10, manufacturer='Corsair', model='H100x',count=0)
wc.save()
wc = waterCoolers(coolerID=11, manufacturer='Corsair', model='H115I RGB',count=0)
wc.save()
wc = waterCoolers(coolerID=12, manufacturer='NZXT', model='Kraken M22',count=0)
wc.save()
# CPUs
cpu=CPUs(cpuID='0',manufacturer='AMD',model='Ryzen 3 1200',count=0)
cpu.save()
cpu=CPUs(cpuID='1',manufacturer='AMD',model='Ryzen 3 1300x',count=0)
cpu.save()
cpu=CPUs(cpuID='1',manufacturer='AMD',model='Ryzen 5 1400',count=0)
cpu.save()
cpu=CPUs(cpuID='2',manufacturer='AMD',model='Ryzen 5 1500x',count=0)
cpu.save()
cpu=CPUs(cpuID='3',manufacturer='AMD',model='Ryzen 5 1600',count=0)
cpu.save()
cpu=CPUs(cpuID='4',manufacturer='AMD',model='Ryzen 5 1600x',count=0)
cpu.save()
cpu=CPUs(cpuID='5',manufacturer='AMD',model='Ryzen 7 1700',count=0)
cpu.save()
cpu=CPUs(cpuID='6',manufacturer='AMD',model='Ryzen 7 1700x',count=0)
cpu.save()
cpu=CPUs(cpuID='7',manufacturer='AMD',model='Ryzen 7 1800x',count=0)
cpu.save()
cpu=CPUs(cpuID='8',manufacturer='AMD',model='Ryzen TR 1900x',count=0)
cpu.save()
cpu=CPUs(cpuID='9',manufacturer='AMD',model='Ryzen TR 1920x',count=0)
cpu.save()
cpu=CPUs(cpuID='10',manufacturer='AMD',model='Ryzen TR 1800x',count=0)
cpu.save()
cpu=CPUs(cpuID='11',manufacturer='Intel',model='I9-9900K',count=0)
cpu.save()
cpu=CPUs(cpuID='12',manufacturer='Intel',model='I7-8086K',count=0)
cpu.save()
cpu=CPUs(cpuID='13',manufacturer='Intel',model='I7-8700K',count=0)
cpu.save()
cpu=CPUs(cpuID='14',manufacturer='Intel',model='I7-8700',count=0)
cpu.save()
cpu=CPUs(cpuID='15',manufacturer='Intel',model='I7-9700K',count=0)
cpu.save()
cpu=CPUs(cpuID='16',manufacturer='Intel',model='I5-8600K',count=0)
cpu.save()
cpu=CPUs(cpuID='17',manufacturer='Intel',model='I5-8500',count=0)
cpu.save()
cpu=CPUs(cpuID='18',manufacturer='Intel',model='I5-8400',count=0)
cpu.save()
cpu=CPUs(cpuID='19',manufacturer='Intel',model='I5-9400F',count=0)
cpu.save()
cpu=CPUs(cpuID='20',manufacturer='Intel',model='I5-9600K',count=0)
cpu.save()
cpu=CPUs(cpuID='21',manufacturer='Intel',model='I3-8350K',count=0)
cpu.save()
cpu=CPUs(cpuID='22',manufacturer='Intel',model='I3-8100',count=0)
cpu.save()
cpu=CPUs(cpuID='23',manufacturer='Intel',model='I3-9350KF',count=0)
cpu.save()"""
