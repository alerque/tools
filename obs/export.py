#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#

'''
Exports OBS for given language to specified format.
'''

import os
import re
import sys
import json
import codecs
import shutil
import urllib2
import argparse

lang_top_json = ''
lang_bot_json = ''
lang_json = ''

api_url_txt = u'https://api.unfoldingword.org/obs/txt/1'
api_url_jpg = u'https://api.unfoldingword.org/obs/jpg/1'
api_test_door43 = u'http://test.door43.org'  # this one is http and not https
api_abs = u'/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1'

MATCH_ALL = 0
MATCH_ONE = 0

def checkForStandardKeysJSON():
    global lang_json
    #
    if 'topspace' not in lang_json.keys(): lang_json['topspace'] = '10pt' # nice for en,fr,es
    if 'botspace' not in lang_json.keys(): lang_json['botspace'] = '12pt' # nice for en,fr,es
    #if 'fontface' not in lang_json.keys(): lang_json['fontface'] = 'pagella' # backwards compatible to test changes for first pass only
    if 'fontface' not in lang_json.keys(): lang_json['fontface'] = 'lato' # this is for production
    #
    if 'bodysize' not in lang_json.keys(): lang_json['bodysize'] = '8.5pt'
    if 'tocsize' not in lang_json.keys(): lang_json['tocsize'] = '12pt'
    if 'licsize' not in lang_json.keys(): lang_json['licsize'] = '8pt'
    #
    if 'bodybaseline' not in lang_json.keys(): lang_json['bodybaseline'] = '11pt'
    if 'tocbaseline' not in lang_json.keys(): lang_json['tocbaseline'] = '16pt'
    if 'licbaseline' not in lang_json.keys(): lang_json['licbaseline'] = '12pt'
    #
    if 'tocperpage' not in lang_json.keys(): lang_json['tocperpage'] = '22'

def writeFile(outfile, p):
    makeDir(outfile.rpartition('/')[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(p)
    f.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def getURL(url, outfile):
    try:
        request = urllib2.urlopen(url)
    except:
        print '  => ERROR retrieving {0}\nCheck the URL'.format(url)
        return
    with open(outfile, 'wb') as fp:
        shutil.copyfileobj(request, fp)

def loadJSON(f, t):
    if os.path.isfile(f):
        return json.load(open(f, 'r'))
    if t == 'd':
      return json.loads('{}')
    else:
      return json.loads('[]')

def getImage(lang, fid, res, format='plain'):
    img_link = '/'.join([api_url_jpg, lang, res, 'obs-{0}-{1}.jpg'.format(
                                                                 lang, fid)])
    if format == 'html':
        return u'<img src="{0}" />'.format(img_link)
    elif format == 'tex':
        return u'  {{\\externalfigure[{0}]}}'.format(img_link)
    return u''

def getTitle(text, format='plain'):
    if format == 'html':
        return u'<h1>{0}</h1>'.format(text)
    elif format == 'md':
        return u'{0}\n=========='.format(text)
    elif format == 'tex':
        return u'\\startmakeup\n\\section{{{0}}}\n\\stopmakeup'.format(text)
    return text

def getFrame(text, format='plain'):
    if format == 'html':
        return u'<p>{0}</p>'.format(text)
    elif format == 'md':
        return u'\n{0}\n'.format(text)
    elif format == 'tex':
        return u'\n\\placefigure[nonumber]\n  {{{0} \\blank[small, flexible]}}'.format(text)
    return text

def getRef(text, format='plain'):
    if format == 'html':
        return u'<em>{0}</em>'.format(text)
    elif format == 'md':
        return u'*{0}*'.format(text)
    elif format == 'tex':
        return u'\\startplacefigure[location=nonumber]\n  {{\\startalignment[middle] {{ \\tfx {{{{\\em {0}}}}}}} \\stopalignment }}\n\\stopplacefigure'.format(text)
    return text

def export_matter(lang_message, format, img_res, lang):
    global inItems
    global MATCH_ALL
    global MATCH_ONE
    matchPipePattern = re.compile(ur"\s*([|])\s*",re.UNICODE)
    matchBoldPattern = re.compile(ur"[*][*]\s*(.*?)\s*[*][*]",re.UNICODE)
    matchUnderlinePattern = re.compile(ur"(\A|[^=])====\s*(.*?)\s*====([^=]|\Z)",re.UNICODE)
    matchRedLetterPattern = re.compile(ur"(\A|[^:/])//(.*?)//([^/]|\Z)",re.UNICODE)
    matchBlankLinePattern = re.compile(ur"^\s*$",re.UNICODE)
    matchPatternLongURL = re.compile(ur"(http://[/\w\d,\._=+-]{41,9999})",re.UNICODE)
    matchPatternURL = re.compile(ur"(http://[/\w\d,\._=+-]+)",re.UNICODE)
    matchBulletPattern = re.compile(ur"^\s*[\*]\s+(.*)$",re.UNICODE)
    matchChapterVersePattern = re.compile(ur"\s+(\d+:\d+)$",re.UNICODE)
    '''
    Exports JSON front/back matter to specificed format.
    '''
    j = u'\n\n'
    if format == 'tex':
        j = u'\n'
    tmpsplit = lang_message.split(u'\n')
    matter = [ ]
    inItems = 0
    def AnotherItem(matchobj):
        global inItems
        inItems += 1
        ans = u'    \\item{' + matchobj.group(1) + u'}'
        if (inItems == 1): ans = u'    \\startitemize\n' + ans
        return ans
    for single_line in tmpsplit:
        copy = single_line
        single_line = matchBlankLinePattern.sub(ur'    \\blank',single_line,MATCH_ALL)
        (single_line, occurrences) = matchBulletPattern.subn(AnotherItem,single_line,MATCH_ONE)
        if ((inItems > 0) and (occurrences == 0)):
            inItems = 0
            single_line = u'    \\stopitemize\n' + single_line
        if (copy == single_line): single_line = u'    \\noindentation ' + single_line
        single_line = matchRedLetterPattern.sub(ur'\1\\color[middlered]{\2}\3',single_line,MATCH_ALL)
        single_line = matchUnderlinePattern.sub(ur'\1\\underbar{\2}\3',single_line,MATCH_ALL)
        single_line = matchBoldPattern.sub(ur'{\\bf \1}',single_line,MATCH_ALL)
        single_line = matchPipePattern.sub(ur' \\textbar \\space ',single_line,MATCH_ALL)
        single_line = matchPatternLongURL.sub(ur'\\goto{\\midaligned \1}[url(\1)]',single_line,MATCH_ALL)
        single_line = matchPatternURL.sub(ur'\\goto{\1}[url(\1)]',single_line,MATCH_ALL)
        single_line = matchChapterVersePattern.sub(ur'~\1',single_line,MATCH_ALL)
        matter.append(single_line)
        #print u''.join([ u'copy=',copy ]).encode('utf-8')
        #print u''.join([ u'single_line=',single_line ]).encode('utf-8')
    return j.join(matter)

def export(lang_json, format, img_res, lang):
    '''
    Exports JSON to specificed format.
    '''
    j = u'\n\n'
    if format == 'tex':
        j = u'\n'
    output = []
    for chp in lang_json:
        output.append(getTitle(chp['title'], format))
        for fr in chp['frames']:
            if format == 'tex':
                output.append(getFrame(fr['text'], format))
                output.append(getImage(lang, fr['id'], img_res, format))
            else:
                output.append(getImage(lang, fr['id'], img_res, format))
                output.append(getFrame(fr['text'], format))
        output.append(getRef(chp['ref'], format))
    return j.join(output)

def getJSON(lang,entry,tmpent):
    anyJSONe = entry.format(lang)
    anyJSONf = '/'.join([api_url_txt, lang, anyJSONe])
    anytmpf = '/'.join(['/tmp', tmpent]).format(lang)
    getURL(anyJSONf, anytmpf)
    if not os.path.exists(anytmpf):
        print "Failed to get JSON {0} file into {1}.".format(anyJSONe,anytmpf)
        sys.exit(1)
    return anytmpf
    
def AnotherReplacement(matchobj):
    global lang_json
    keyword = matchobj.group(1)
    if keyword in lang_json.keys(): return lang_json[keyword]
    return 'nothing'

def main(lang, outpath, format, img_res):
    global MATCH_ALL
    global MATCH_ONE
    global lang_top_json
    global lang_bot_json
    global lang_json
    #
    matchChaptersPattern = re.compile(ur"===CHAPTERS===",re.UNICODE)
    matchFrontMatterPattern = re.compile(ur"===FRONT\.MATTER===",re.UNICODE)
    matchBackMatterPattern = re.compile(ur"===BACK\.MATTER===",re.UNICODE)
    matchMiscPattern = re.compile(ur"<<<[\[]([^<>=]+)[\]]>>>",re.UNICODE)
    #
    toptmpf = getJSON(lang, 'obs-{0}-front-matter.json', '{0}-front-matter.tmp')
    bottmpf = getJSON(lang, 'obs-{0}-back-matter.json', '{0}-back-matter.tmp')
    lang_top_json = loadJSON(toptmpf, 'd')
    lang_bot_json = loadJSON(bottmpf, 'd')
    #
    output_front = export_matter(lang_top_json['front-matter'], format, img_res, lang_top_json['language'])
    output_back = export_matter(lang_bot_json['back-matter'], format, img_res, lang_bot_json['language'])
    #
    jsonf = 'obs-{0}.json'.format(lang)
    lang_abs = os.path.join(api_abs, lang, jsonf)
    if os.path.exists(lang_abs):
        lang_json = loadJSON(lang_abs, 'd')
    else:
        #lang_url = '/'.join([api_url_txt, lang, jsonf])
        #tmpf = '/tmp/{0}'.format(jsonf)
        #getURL(lang_url, tmpf)
        #if not os.path.exists(tmpf):
        #   print "Failed to get JSON file."
        #   sys.exit(1)
        tmpf = getJSON(lang, jsonf, '{0}-body-matter.tmp')
        lang_json = loadJSON(tmpf, 'd')
    checkForStandardKeysJSON()
    output = export(lang_json['chapters'], format, img_res, lang_json['language'])
    #
    if format == 'tex':
        outlist = []
        tex_url = '/'.join([api_test_door43, 'introTeXtOBS.tex'])
        tmp_texF = '/tmp/introTeXtOBS.tex'
        getURL(tex_url, tmp_texF)
        if not os.path.exists(tmp_texF):
            print "Failed to get TeX template."
            sys.exit(1)
        template = codecs.open(tmp_texF, 'r', encoding='utf-8').readlines()
        for single_line in template:
            single_line = single_line.rstrip('\r\n')
            if (matchChaptersPattern.search(single_line)): outlist.append(output)
            elif (matchFrontMatterPattern.search(single_line)): outlist.append(output_front)
            elif (matchBackMatterPattern.search(single_line)): outlist.append(output_back)
            else:
                ( single_line, occurrences ) = matchMiscPattern.subn(AnotherReplacement,single_line,MATCH_ALL)
                while ( occurrences > 0):
                    ( single_line, occurrences ) = matchMiscPattern.subn(AnotherReplacement,single_line,MATCH_ALL)
                outlist.append(single_line)
        full_output = u'\n'.join(outlist)
        writeFile(outpath, full_output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--output', dest="outpath", default=False,
        required=True, help="Output path")
    parser.add_argument('-l', '--language', dest="lang", default=False,
        required=True, help="Language code")
    parser.add_argument('-f', '--format', dest="format", default=False,
        required=True, help="Desired format: html, md, tex, or plain")
    parser.add_argument('-r', '--resolution', dest="img_res", default='360px',
        help="Image resolution: 360px, or 2160px")

    args = parser.parse_args(sys.argv[1:])
    main(args.lang, args.outpath, args.format, args.img_res)
