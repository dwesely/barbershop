# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 23:05:10 2015

Parses xml from barbershopwiki.com to pull out quartet singer names and parts

Export pages of "Quartets" category as Barbershop+Wiki+Project-quartets.xml
Export pages of "List of Champions" category as Barbershop+Wiki+Project-listofchampions.xml

@author: Wesely
"""
import re
import barbershop

VERBOSE = False

def cleanNameString(str):
    # Correct minor formatting issues with name strings
    cleanedStr = str.replace('&quot;','"').replace(', Jr',' Jr.').replace(', Sr',' Sr.').replace('r.','r').replace(' ,',',').strip(' \t\n\r')
    if VERBOSE and str != cleanedStr:
        print('({}) -> ({})'.format(str,cleanedStr))
    return cleanedStr
        
def parseQuartetTitle(str):
    return re.search(r'(?<=\>)[^<]*',str).group(0)

def getChampLinkName(champ_description):
    #print(champ_description)
    champSplit = champ_description.find('Champ')
    quartSplit = champ_description.find('Quart')
    if champSplit>0 and quartSplit>0:
        champdescriptionsplit = min(champSplit, quartSplit)
    elif champSplit>0:
        champdescriptionsplit = champSplit
    elif quartSplit>0:
        champdescriptionsplit = quartSplit
    else:
        return(champ_description.strip(' \t\n\r'))
    #print(champ_description[:champdescriptionsplit])
    return(champ_description[:champdescriptionsplit].strip(' \t\n\r'))
        
qsidx = 0
maxlengthforjunktext = 150;

quartetList        = []
singerList         = []
quartetterList     = []
pagesWithNoSingers = []
textWithParens     = re.compile(r'(?:[^,(]|\([^)]*\))+')

#Open file for results summary
bswikihomefile = open('bswikihome.txt','w')


#Parse quartet file
bsfile = open('Barbershop+Wiki+Project-quartets.xml','r+')
print('Parsing quartets...')

#Compile regex

# Parts are typically identified with Tenor/Lead/Bari/Bass
partlineRegex = re.compile(r'''
    ^.{0,10}                    # Spacers
    (Tenor|Bass|Lead|Bari\w*)   # Part
    [/A-Za-z]*[ -:]*            # Other info/separator
    ([^(,<]*)                   # Name
    \D*[ (]*                    # Separator
    ([-, 0-9]*)                 # Year(s)
    ''', re.VERBOSE)
    
# Some quartets have singers rotate out over the years, so parts may have
# multiple singers listed under the same part
addlpartRegex = re.compile(r'''
    (\w+[-:])*          # Part
    ([^(,]*[A-Za-z]*)   # Name
    [ (]*               # Separator
    ([-, 0-9]*)         # Year(s)
    ''', re.VERBOSE)

# Year and Quartet titles are located in the List of Champions pages
yearqtitleRegex = re.compile(r'''
    \|\s*               # First column separator
    (\d+|\d+ \w+)       # Date/Date with season
    ]*\s*\|{2}\s*       # Second column separator and formatting quotes
    \'*([^\|]*)         # Quartet title
    ''', re.VERBOSE)

# TLBB in comma format
namelistRegex = re.compile(r'''
    ^[|]\s*                 # Table separator
    ([^,\|]*[|]*[^,\|]*)    # Tenor
    [,]\s*                  # Separator
    ([^,]*)                 # Lead
    [,]\s*                  # Separator
    ([^,]*)                 # Bari
    [,]\s*                  # Separator
    ([^,]*)                 # Bass
    ''', re.VERBOSE)

allpages = re.split(r'<page>',bsfile.read())
for page in allpages:
    qtitle  = ''
    mypart  = ''
    mylink  = ''
    myyears = ''    
    thisQuartetter = []
    
    alllines = re.split(r'\n',page)
    for line in alllines:
        if line.find('<title>')>0:
            qtitle = parseQuartetTitle(line)
        elif line.startswith("      <comment"):
            continue
        else:
            splitlines = re.split(r'[*]|==',line)
            for splitline in splitlines:
                if len(splitline)>maxlengthforjunktext:
                    continue

                splitline = splitline.replace("..."," ")
                partline = partlineRegex.search(splitline)
                if partline:
                    if partline.group(1):
                        mypart = partline.group(1).strip(' \t\n\r')
                    else:
                        mypart = ''
                    if partline.group(2):
                        myname = cleanNameString(partline.group(2))
                        if re.match('[\[]',myname):
                            mylink = myname
                            myname = re.search(r'[[]+([^\|\]]*)',myname).group(1).strip(' \t\n\r')
                        else:
                            mylink = '[[{}]]'.format(myname)
                    else:
                        myname = ''
                        mylink = ''
                    if partline.group(3):
                        myyears = partline.group(3).strip(' \t\n\r')
                    else:
                        myyears = ''

                    if re.search(r'[,]',splitline):
                        if VERBOSE:
                            print(splitline)
                        commagroups = textWithParens.findall(cleanNameString(splitline))
                        for commagroup in commagroups:
                            addlpart = addlpartRegex.search(commagroup)
                            if addlpart:
                                if addlpart.group(2):
                                    myname = cleanNameString(addlpart.group(2))
                                    if  re.match('[\[]',myname):
                                        mylink = myname
                                        myname = re.search(r'[[]+([^\|\]]*)',myname).group(2).strip(' \t\n\r')
                                    else:
                                        mylink = '[[{}]]'.format(myname)
                                    thisQuartetter = barbershop.get_Quartetter_Object(qtitle,mypart,myname)
                                else:
                                    myname = ''
                                    mylink = ''
                                if addlpart.group(3):
                                    myyears = addlpart.group(3).replace('"','&quot;')
                                    thisQuartetter.set_year(myyears)
                                else:
                                    myyears = ''
                    else:
                        if myname is not '':
                            thisQuartetter = barbershop.get_Quartetter_Object(qtitle,mypart,myname)
                            thisQuartetter.set_year = myyears
    if thisQuartetter == []:
        if VERBOSE:
            print('[[{}]] has no singers listed.'.format(qtitle))
        pagesWithNoSingers.append(barbershop.get_Quartet_Object(qtitle))
for quartet in barbershop.Quartet.quartets_dict.values():
    quartet.set_has_page(True)
    if VERBOSE:
        if quartet.has_four_parts():
            print('{}:\n\t{}, {}, {}, {}'.format(quartet.title,quartet.tenor.name,quartet.lead.name,quartet.bari.name,quartet.bass.name))

print('Quartets that currently have pages in the wiki:\n*{} Quartets identified.'.format(len(barbershop.Quartet.quartets_dict.values())))
print('*{} Singers identified.'.format(len(barbershop.Singer.singers_dict.values())))

bsfile.close()


#Parse the List of Champions pages
bsfile = open('Barbershop+Wiki+Project-listofchampions.xml','r+')
#TODO: If the name has a link to a quartet instead of to the name page, strip the quartet link
#TODO: Add empty championships to quartets
allpages = re.split(r'<page>',bsfile.read())
champlistsWithoutSingers = set([])
bswikihomefile.write('\n==== Table of Latest Recorded Championship Details ====\n{| border="1" class="wikitable sortable"\n!  Championship\n!  Earliest Year Recorded\n!  Latest Year Recorded\n!  % With Quartetters')
for page in allpages:
    alllines           = re.split(r'\n',page)
    champ_description  = ''
    champlinkname      = ''
    champlink          = ''
    tenor              = ''
    lead               = ''
    bari               = ''
    bass               = ''
    year               = ''
    qtitle             = ''
    thisQuartetter     = []
    hasQuartetters     = False
    hasAnyQuartetters  = False
    earliestYearRecorded = ''
    latestYearRecorded = ''
    withQuartettersCount = 0
    
    starttlbbtable = False
    for line in alllines:
        #print(line.find('<title>'))
        if line.find('<title>')>0:
            #print(line)
            champ_description = re.search(r'(?<=\>)[^<]+',line).group(0)
            if champ_description == 'IABS International Quartet Champions':
                print('\n')
            #print(champ_description)
            champlinkname = getChampLinkName(champ_description)
        elif line.startswith("      <comment"):
            continue
            #print('Skipped comment')
        elif line.find('Tenor, Lead, Bari')>0 or line.find('Tenor,Lead,Bari')>0:
            starttlbbtable = True
        elif starttlbbtable:

            if (champ_description == 'IABS International Quartet Champions') and (year == '2010'):
                print('\n')
            if line.strip(' \n\r\t')=='|-':
                #New table row, clear out the variables
                tenor              = ''
                lead               = ''
                bari               = ''
                bass               = ''
                year               = ''
                qtitle             = ''
                thisQuartetter     = []

            yearqtitle = yearqtitleRegex.search(line.replace("'''",""))
            #if a year/qtitle is found, print last year/qtitle/singerlist
            if yearqtitle:
                #if no quartetters were found for previous year, save the quartet anyway
                #if not hasQuartetters:
                #    if (qtitle != '') and (year != ''):
                #        qObj = barbershop.get_Quartet_Object(qtitle)
                #        if qObj.has_four_parts():
                #            #print(qObj.get_tlbb()) 
                #            print('{} has parts, but none listed in {}'.format(qtitle,champlink))
                #        #print(champ_description + year + qtitle)
                #        #barbershop.get_Quartet_Object(qtitle).add_championship(barbershop.get_Championship_Object(champ_description,year,champlink))

                hasQuartetters = False
                year = yearqtitle.group(1)                
                if year>latestYearRecorded:
                    latestYearRecorded = year
                if earliestYearRecorded == '' or year < earliestYearRecorded:
                    earliestYearRecorded = year
                qtitle = yearqtitle.group(2).strip(' \t\n\r[]')
                champlink = '[[{}|{} {}]]'.format(champ_description,year,champlinkname)
                champObj = barbershop.get_Championship_Object(champ_description,year,champlink)
                #print('\n{},{},'.format(yearqtitle.group(1),yearqtitle.group(2))  )              
            splitlines = re.split(r'[\|]{2}',line.replace(' ,',',').replace('&quot;','"'))
            for splitline in splitlines:     
                
                namelist = namelistRegex.search(cleanNameString(splitline))
                if namelist:
                    hasQuartetters = True
                    hasAnyQuartetters = True
                    withQuartettersCount = withQuartettersCount + 1
                    tenor = namelist.group(1).strip(' \t\n\r')
                    lead  = namelist.group(2).strip(' \t\n\r')
                    bari  = namelist.group(3).strip(' \t\n\r')
                    bass  = namelist.group(4).strip(' \t\n\r')
                    thisQuartetter = barbershop.get_Quartetter_Object(qtitle,'Tenor',tenor).add_championship(champObj)
                    thisQuartetter = barbershop.get_Quartetter_Object(qtitle,'Lead' ,lead ).add_championship(champObj)
                    thisQuartetter = barbershop.get_Quartetter_Object(qtitle,'Bari' ,bari ).add_championship(champObj)
                    thisQuartetter = barbershop.get_Quartetter_Object(qtitle,'Bass' ,bass ).add_championship(champObj)
                    tlbb = champObj.get_tlbb()
                    if VERBOSE:
                        print('({}) {} {}'.format(len(tlbb),champObj.year,champObj.name))
    if not hasAnyQuartetters:
        if champlink == '':
            champlink = '[[{}]]'.format(champ_description)        
        champlistsWithoutSingers.add(barbershop.get_Championship_Object(champ_description,year,champlink))
    else:
        if earliestYearRecorded and latestYearRecorded:
            percentComplete = 100*withQuartettersCount/(1+float(re.sub("[^0-9^.]", "", latestYearRecorded))-float(re.sub("[^0-9^.]", "", earliestYearRecorded)))
        else:
            print('No years identified: {}'.format(champ_description))
            percentComplete = -1
        bswikihomefile.write('\n|-\n| [[{}]] || {} || {} || {:.0f}%'.format(champ_description,earliestYearRecorded,latestYearRecorded,percentComplete))
bswikihomefile.write('\n|}')

bsfile.close()

#Identify List of CHampions pages without individual singers listed
bswikihomefile.write('\n\n==== Champ lists without singers listed ====')
for champObj in sorted(champlistsWithoutSingers, key=lambda x: x.name):
    if champObj.name.find('horus')>0 or len(champObj.name)<1:
        continue
    else:
        bswikihomefile.write('\n*[[{}]] lists no singers.'.format(champObj.name))


#This section generates stub pages for quartets
xmloutfile = open('xmlpagesout.xml','w')
for quartet in barbershop.Quartet.quartets_dict.values():
    if quartet.has_page:
        if VERBOSE:
            if quartet.has_four_parts():
                print('[[{}]]: {}, {}, {}, {}'.format(quartet.title,quartet.tenor.name,quartet.lead.name,quartet.bari.name,quartet.bass.name))
    else:
        if VERBOSE:
            if quartet.has_four_parts():
                print('({}) [[{}]]: {}, {}, {}, {}'.format(len(quartet.members), quartet.title,quartet.tenor.name,quartet.lead.name,quartet.bari.name,quartet.bass.name))
                tlbb = quartet.get_tlbb()
                for quartetter in quartet.members:
                    try:
                        b=tlbb.index(quartetter)
                    except ValueError:
                        print('{}: {}'.format(quartetter.part,quartetter.name))
        #print a wiki page
        xmlheader = '\n\n<page><title>{}</title><revision><text>'.format(quartet.title)
        xmloutfile.write(xmlheader)
        header = '__NOTOC__\n\n= {} (Template) =\n[[Image:{}.jpg|thumb|{}]]'.format(quartet.title,quartet.title,quartet.title)
        xmloutfile.write(header)        
        bio = "\n\n''(Bio goes here. This stub was generated using existing quartet pages and championship records pages. Please add a bio for this quartet, a picture if available, and check the pages linked below to create links back to this page.)''"
        xmloutfile.write(bio)
        if len(quartet.championships)>0:
            contests = '\n== Contest Placement =='
            xmloutfile.write(contests)
            for championship in quartet.championships:
                thisContest = '\n\n=== {} ===\n\n{{| class="contesttable" border="1"'.format(championship.name)
                xmloutfile.write(thisContest)
                xmloutfile.write('|}}')
                # for loop over years to create year tables: ! 19xx || 19xx || 19xx\n|-\n| 4th || 4th || 1st \n|}
            
        district = '' #=== District ===\nRepresents the [[Southwestern District]].
        recordings = "\n\n== Recordings ==\n\n''Please check a database like freedb.org for relevant discography.''"
        xmloutfile.write(recordings)
        tracks = '\n\n=== Album Title (19xx) ===\n{| class="wikitable sortable" border="1" \n! ''''Track''''\n! ''''Title''''\n|-\n| 1 || Track title 1 of 5\n|-\n| 2 || Track title 2 of 5\n|-\n| 3 || Track title 3 of 5\n|-\n| 4 || Track title 4 of 5\n|-\n| 5 || Track title 5 of 5 '
        xmloutfile.write(tracks)
        xmloutfile.write('\n|}')
        members = '\n\n= Members ='
        xmloutfile.write(members)
        if len(quartet.championships)>0:
            champions = '\n\n== Champions =='
            xmloutfile.write(champions)
            if quartet.has_four_parts():
#                print(quartet.title)
                for championship in quartet.championships:
                    tlbb = championship.get_tlbb()
                    thischampionship = '\n\n=== {} ==='.format(championship.link)
                    xmloutfile.write(thischampionship)
                    champsingers = '\n*Tenor: [[{}]]\n*Lead: [[{}]]\n*Bari: [[{}]]\n*Bass: [[{}]]'.format(quartet.tenor.name,quartet.lead.name,quartet.bari.name,quartet.bass.name)
                    xmloutfile.write(champsingers)
        otherMembers = '\n== Other Members =='
        xmloutfile.write(otherMembers)
        #loop for remaining members associated with this quartet
        categories = '\n\n[[Category:Quartets]][[Category:Stub]]'
        xmloutfile.write(categories)
        #get unique values and print categories
        champcat = []
        for championship in quartet.championships:
            champcat.append(championship.category)
        for category in set(champcat):
            xmloutfile.write(category)
        xmlfooter = '\n</text></revision></page>'
        xmloutfile.write(xmlheader)
        xmloutfile.write('\n')

#Identify individual quartet pages that have no singers identified in them
bswikihomefile.write('\n\n==== Quartet pages without singers listed ({}) ===='.format(len(pagesWithNoSingers)))
for quartet in sorted(pagesWithNoSingers, key=lambda x: x.title):
    if len(quartet.members)>0:
        bswikihomefile.write('\n[[{}]] has {} members:'.format(quartet.title,len(quartet.members)))
        for quartetter in quartet.members:
            bswikihomefile.write('\n*{} - {} (Championship: {})'.format(quartetter.part, quartetter.name, quartetter.championships[0].link))

#Identify quartets that have the most awards
bswikihomefile.write('\n\n==== Quartets with the most awards ====')
topten = 0
for quartet in sorted(barbershop.Quartet.quartets_dict.values(), key=lambda x: len(x.championships), reverse=True):
    if topten<10:
        topten = topten+1
        bswikihomefile.write('\n[[{}]] has {} awards:'.format(quartet.title,len(quartet.championships)))
        for championship in sorted(quartet.championships, key=lambda x: x.year, reverse=True):
            bswikihomefile.write('\n*{}'.format(championship.link))

bswikihomefile.write('\n\n==== Quartets with the most types of awards ====')
topten = 0
for quartet in sorted(barbershop.Quartet.quartets_dict.values(), key=lambda x: x.get_unique_championship_count(), reverse=True):
    if topten<10:
        topten = topten+1
        bswikihomefile.write('\n[[{}]] has {} awards:'.format(quartet.title,len(quartet.championships)))
        for championship in sorted(quartet.championships, key=lambda x: x.year, reverse=True):
            bswikihomefile.write('\n*{}'.format(championship.link))


#Identify singers that have the most awards
bswikihomefile.write('\n\n==== Singers with the most awards ====')
topten = 0
for singer in sorted(barbershop.Singer.singers_dict.values(), key=lambda x: len(x.championships), reverse=True):
    if (topten<10 and not singer.name.find('_')>0): #or (singer.name == '[[Morris "Mo" Rector|Mo Rector]]'):
        topten = topten+1
        bswikihomefile.write('\n[[{}]] has {} awards:'.format(singer.name,len(singer.championships)))
        for championship in sorted(singer.championships, key=lambda x: x.year, reverse=True):
            for thissinger in championship.quartetters:
                if thissinger.name == singer.name:
                    bswikihomefile.write('\n*{} with [[{}]] ({})'.format(championship.link, thissinger.quartet.title, thissinger.part))

bswikihomefile.write('\n\n==== Singers with the most types of awards ====')
topten = 0
for singer in sorted(barbershop.Singer.singers_dict.values(), key=lambda x: x.get_unique_championship_count(), reverse=True):
    if (topten<10 and not singer.name.find('_')>0): 
        topten = topten+1
        bswikihomefile.write('\n[[{}]] has {} awards:'.format(singer.name,len(singer.championships)))
        for championship in sorted(singer.championships, key=lambda x: x.year, reverse=True):
            for thissinger in championship.quartetters:
                if thissinger.name == singer.name:
                    bswikihomefile.write('\n*{} with [[{}]] ({})'.format(championship.link, thissinger.quartet.title, thissinger.part))

#Identify the singers that have been members of the most quartets.
bswikihomefile.write('\n\n==== Singers in the most quartets ====')
topten = 0
for singer in sorted(barbershop.Singer.singers_dict.values(), key=lambda x: len(x.quartets), reverse=True):
    if topten<10 and not singer.name.find('_')>0:
        topten = topten+1
        bswikihomefile.write('\n[[{}]] was in {} quartets:'.format(singer.name,len(singer.quartets)))
        for quartet in sorted(singer.quartets, key=lambda x: x.title):
            bswikihomefile.write('\n*[[{}]]'.format(quartet.title))

#List all singers
dbsingerfile = open('db_singer.txt','w')
dbsingerfile.write('Name,Link,Partlist')

for singer in sorted(barbershop.Singer.singers_dict.values(), key=lambda x: x.name):
    dbsingerfile.write('\n{},[[{}]],'.format(singer.name,singer.name))
    for quartetter in singer.quartetter_parts:
        dbsingerfile.write('{} '.format(quartetter.part))

dbsingerfile.close()


#Identify quartets with a large number of singers which may indicate 
#a need for disambiguation pages
disambiguationThresholdSingerCount = 7
potential_disambiguation_list = []
for quartet in barbershop.Quartet.quartets_dict.values():
    if len(quartet.members) > disambiguationThresholdSingerCount:
        potential_disambiguation_list.append(quartet)
        if VERBOSE:
            for quartetter in quartet.members:
                print('{} ({}): {}'.format(quartetter.quartet.title,quartetter.part,quartetter.name))

bswikihomefile.write('\n\n==== Potential disambiguation pages needed ({}) ===='.format(len(potential_disambiguation_list)))
topten = 0
with open('potentialDisambiguation.txt','w') as disambout:
    for quartet in sorted(potential_disambiguation_list, key=lambda x: len(x.members), reverse=True):
        if topten<10:
            bswikihomefile.write('\n({}) [[{}]]'.format(len(quartet.members),quartet.title))
        disambout.write('\n({}) [[{}]]'.format(len(quartet.members),quartet.title))
        for quartetter in quartet.members:
            if len(quartetter.championships)>0:
                champlink = quartetter.championships[0].link
            else:
                champlink = 'None'
            if topten<10:
                bswikihomefile.write('\n*{} - {} (Championship: {})'.format(quartetter.part, quartetter.name, champlink))
            disambout.write('\n*{} - {} (Championship: {})'.format(quartetter.part, quartetter.name, champlink))
        topten = topten+1
disambout.close()

#Write each quartet that has any singers identified
with open('fullQuartetList.txt','w') as fullQuartetList:
    for quartet in sorted(barbershop.Quartet.quartets_dict.values(), key=lambda x: x.title):
        fullQuartetList.write('\n\n[[{}]] has {} members:'.format(quartet.title,len(quartet.members)))
        if len(quartet.members)>0:
            for quartetter in quartet.members:
                fullQuartetList.write('\n*{} - {} ('.format(quartetter.part, quartetter.name))
                counter = 0;
                for championship in quartetter.championships:
                    if counter > 0:
                        fullQuartetList.write(',')
                    else:
                         counter = counter + 1   
                    champlink = championship.link
                    fullQuartetList.write('{}'.format(champlink))
                fullQuartetList.write(')')
fullQuartetList.close()

print('Quartets, including those listed in the ''List of Champions'' category:\n*{} Quartets identified.'.format(len(barbershop.Quartet.quartets_dict.values())))
print('*{} Singers identified.'.format(len(barbershop.Singer.singers_dict.values())))

xmloutfile.close()
bswikihomefile.close()
print('Complete.')
