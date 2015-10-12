# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 23:05:10 2015
Purpose:
Store Barbershop information such as singers, quartets, and quartet championships as related objects, like a database.

This is being developed to help connect data in various pages of www.barbershopwiki.com, and to check for
consistency across multiple pages referencing the same individuals.

@author: Wesely
"""
import re

#should enumerate or something, I guess
TENOR = 'Tenor'
LEAD  = 'Lead'
BASS  = 'Bass'
BARI  = 'Bari'
VERBOSE = False

def part_to_index(part):
    switcher = {
        TENOR: 0,
        LEAD:  1,
        BARI:  2,
        BASS:  4
    }
    return switcher.get(part, "Not Available")

class Quartet:

    quartets_dict = {}

    # if "%s" % (title) not in Quartet.quartets_dict:    
    
    def __init__(self, title):
        self.title = title
        self.members = []
        self.link = '[[{}]]'.format(title)
        self.tenor = None
        self.lead = None
        self.bari = None
        self.bass = None
        self.has_page = False
        self.championships = set([])
        
        Quartet.quartets_dict[title] = self
        
    def has_four_parts(self):
        if (
            self.tenor is not None 
            and self.lead is not None
            and self.bari is not None
            and self.bass is not None
        ):
            return True
        else:
            return False
    def set_has_page(self, has_page):
        self.has_page = has_page
    def add_member(self, quartetter):
        self.members.append(quartetter)
    def add_championship(self, championship):
        self.championships.add(championship)
    def set_link(self, link):
        self.link = link
    def set_tenor(self, quartetter):
        self.tenor = quartetter
    def set_lead(self, quartetter):
        self.lead = quartetter
    def set_bari(self, quartetter):
        self.bari = quartetter
    def set_bass(self, quartetter):
        self.bass = quartetter
    def get_tlbb(self):
        tlbb = []
        tlbb.append(self.tenor)
        tlbb.append(self.lead)
        tlbb.append(self.bari)
        tlbb.append(self.bass)
        
        return tlbb

class Singer:
    singers_dict = {}

    def __init__(self, name):
        self.name = name
        Singer.singers_dict[name] = self
        self.quartets = set([])
        self.quartetter_parts = []
        self.championships = []
    def add_quartet(self,quartet):
        self.quartets.add(quartet)
    def add_quartetter_part(self,quartetter):
        self.quartetter_parts.append(quartetter)
    def add_championship(self, championship):
        self.championships.append(championship)

def get_quartetterID(qtitle, part, sname):
    return "%s|%s|%s" % (qtitle, part, sname)

class Quartetter:
    quartetters_dict = {}
        
    def __init__(self, quartet_title, part, singer_name):
        self.name = singer_name
        self.singer = get_Singer_Object(singer_name)
        self.quartet = get_Quartet_Object(quartet_title)
        self.championships = []
        self.link = '[[{}]]'.format(singer_name)
        
        #update singer and quartet lists/relationships
        self.singer.add_quartet(self.quartet)
        self.singer.add_quartetter_part(self)
        self.quartet.add_member(self)
        
        #set part
        if re.search('[tT]enor.*',part):
            part = TENOR
            if self.quartet.tenor is None:
                self.quartet.set_tenor(self)
        elif re.search('[lL]ead.*',part):
            part = LEAD
            if self.quartet.lead is None:
                self.quartet.set_lead(self)
        elif re.search('[bB]ari.*',part):
            part = BARI
            if self.quartet.bari is None:
                self.quartet.set_bari(self)
        elif re.search('[bB]ass.*',part):   
            part = BASS
            if self.quartet.bass is None:
                self.quartet.set_bass(self)
        self.part = part
            
        #record to dictionary
        quartetterID = get_quartetterID(quartet_title, part, singer_name)
        Quartetter.quartetters_dict[quartetterID] = self
    def set_link(self, link):
        self.link = link
    def set_part(self, part):
        self.part = part
    def set_year(self, year):
        self.year = year
    def add_championship(self, championship):
        self.championships.append(championship)
        self.quartet.add_championship(championship)
        self.singer.add_championship(championship)
        championship.add_quartetter(self)


class Championship:
    championships_dict = {}
    
    def __init__(self, name, year, link):
        self.name = name
        self.year = year
        self.link = link
        self.category = '[[Category:{}]]'.format(name)
        self.quartetters = []
        Championship.championships_dict["%s|%s" % (name, year)] = self
    def set_category(self, category):
        self.category = category
    def add_quartetter(self, quartetter):
        if VERBOSE:
            print('({}) {},{},{}'.format(len(self.quartetters),self.name,self.year,quartetter.name))
        self.quartetters.append(quartetter)
    def get_tlbb(self):
        tlbb = sorted(self.quartetters, key=lambda x: part_to_index(x.part))
        #print('({}) {} {}:'.format(len(tlbb),self.year,self.name))
        #print(' {} {} {} {} {} {} {} {} '.format(tlbb[0].part,tlbb[0].name,tlbb[1].part,tlbb[1].name,tlbb[2].part,tlbb[2].name,tlbb[3].part,tlbb[3].name))
        return tlbb

def get_Championship_Object(name, year, link):
    objId = "%s|%s" % (name, year)
    if objId not in Championship.championships_dict:
        championshipObj = Championship(name, year, link)
    else:
        championshipObj = Championship.championships_dict.get(objId)
    return championshipObj
    
        
def get_Quartet_Object(title):
    if title not in Quartet.quartets_dict:
        quartetObj = Quartet(title)
    else:
        quartetObj = Quartet.quartets_dict.get(title)
    return quartetObj

def get_Singer_Object(name):
    if name not in Singer.singers_dict:
        singerObj = Singer(name)
    else:
        singerObj = Singer.singers_dict.get(name)
    return singerObj
    
def get_Quartetter_Object(quartet_title, part, singer_name):
    qid = get_quartetterID(quartet_title, part, singer_name)
    if qid not in Quartetter.quartetters_dict:
        quartetterObj = Quartetter(quartet_title, part, singer_name)
    else:
        quartetterObj = Quartetter.quartetters_dict.get(qid)
    return quartetterObj

def testcase():
    quartet = 'Young Guys'
    singer = 'Dan Wesely'
    #print(quartet.title)
    #print(singer.name)
    #print(get_quartetterID(quartet.title, 'Bass', singer.name))
    champ_description = 'Description'
    year = '2000'
    champlink = '[[link]]'
    quartetter = get_Quartetter_Object(quartet, 'Bass', singer).add_championship(get_Championship_Object(champ_description,year,champlink))
    if VERBOSE:
        print(len(get_Championship_Object(champ_description,year,champlink).quartetters))
    year = '2001'
    quartetter = get_Quartetter_Object(quartet, 'Bass', singer).add_championship(get_Championship_Object(champ_description,year,champlink))
    if VERBOSE:
        print(len(get_Championship_Object(champ_description,year,champlink).quartetters))

    newsinger = get_Singer_Object('Other Guy')
    quartetter = get_Quartetter_Object(quartet, 'Bari', newsinger)
    if VERBOSE:
        print(quartetter)
    #print(quartetter.part)
    #print(quartetter.quartet.title)
    
#testcase()
