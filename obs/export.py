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
from string import Template

body_json = ''

api_url_txt = u'https://api.unfoldingword.org/obs/txt/1'
api_url_jpg = u'https://api.unfoldingword.org/obs/jpg/1'
api_test_door43 = u'http://test.door43.org'  # this one is http and not https
api_abs = u'/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1'

MAX_CHAPTERS = 0
#MAX_CHAPTERS = 4
MATCH_ALL = 0
MATCH_ONE = 0

matchAlphaNum = re.compile(ur"[A-Za-z0-9]",re.UNICODE)
matchSignificantTex = re.compile(ur"[A-Za-z0-9\\{}\[\]]",re.UNICODE)
matchPipePattern = re.compile(ur"\s*([|])\s*",re.UNICODE)
matchBoldPattern = re.compile(ur"[*][*]\s*(.*?)\s*[*][*]",re.UNICODE)
matchItalicPattern = re.compile(ur"[/][/]\s*(.*?)\s*[/][/]",re.UNICODE)
matchMonoPattern = re.compile(ur"[\'][\']\s*(.*?)\s*[\'][\']",re.UNICODE)
matchUnderLinePattern = re.compile(ur"__\s*(.*?)\s*__",re.UNICODE)
matchHeadingLevelPattern = re.compile(ur"(\A|[^=])====\s*(.*?)\s*====?([^=]|\Z)",re.UNICODE)
matchRedLetterPattern = re.compile(ur"(\A|[^:/])//(.*?)//([^/]|\Z)",re.UNICODE)
matchBlankLinePattern = re.compile(ur"^\s*$",re.UNICODE)
matchPatternLongURL = re.compile(ur"[\(]*(https*://[/\w\d,\.\?\&_=+-]{41,9999})[\)\.,]*",re.UNICODE)
matchPatternURL = re.compile(ur"[\(]*(https*://[/\w\d,\.\?\&_=+-]+)[\)\.,]*",re.UNICODE)
matchBulletPattern = re.compile(ur"^\s*[\*]\s+(.*)$",re.UNICODE)
matchChapterVersePattern = re.compile(ur"\s+(\d+:\d+)",re.UNICODE)

matchChaptersPattern = re.compile(ur"===CHAPTERS===",re.UNICODE)
matchFrontMatterPattern = re.compile(ur"===FRONT\.MATTER===",re.UNICODE)
matchBackMatterPattern = re.compile(ur"===BACK\.MATTER===",re.UNICODE)
matchMiscPattern = re.compile(ur"<<<[\[]([^<>=]+)[\]]>>>",re.UNICODE)

def checkForStandardKeysJSON():
    global body_json
    #------------------------------  header/footer spacing and body font-face
    if 'textwidth' not in body_json.keys(): body_json['textwidth'] = '308.9pt' # At 72.27 pt/inch this is width of each figure
    if 'topspace' not in body_json.keys(): body_json['topspace'] = '10pt' # nice for en,fr,es
    if 'botspace' not in body_json.keys(): body_json['botspace'] = '12pt' # nice for en,fr,es
    #if 'fontface' not in body_json.keys(): body_json['fontface'] = 'dejavu' # backwards compatible to test changes for first pass only
    #if 'fontface' not in body_json.keys(): body_json['fontface'] = 'pagella' # backwards compatible to test changes for first pass only
    #if 'fontface' not in body_json.keys(): body_json['fontface'] = 'Noto' # this is for production but does not seem to work for Russian
    if 'fontface' not in body_json.keys(): body_json['fontface'] = 'dejavu' # this is for production but does not seem to work for Russian
    if 'direction' not in body_json.keys(): body_json['fontface'] = 'ltr' # Use 'rtl' for Arabic, Farsi, etc.
    #------------------------------  Body font size and baseline
    if 'bodysize' not in body_json.keys(): body_json['bodysize'] = '10.0pt'
    if 'bodybaseline' not in body_json.keys(): body_json['bodybaseline'] = '11.0pt'
    #------------------------------  Table-of-contents size, etc
    if 'tocsize' not in body_json.keys(): body_json['tocsize'] = '12pt'
    if 'licsize' not in body_json.keys(): body_json['licsize'] = '10pt'
    if 'tocbaseline' not in body_json.keys(): body_json['tocbaseline'] = '16pt'
    if 'licbaseline' not in body_json.keys(): body_json['licbaseline'] = '12pt'
    if 'tocperpage' not in body_json.keys(): body_json['tocperpage'] = '26'

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

def tex_load_snippet_file(xtr, entryname):
    tex_url = '/'.join([api_test_door43, entryname])
    snippet_file = '/'.join(['/tmp',entryname])
    getURL(tex_url, snippet_file)
    f = codecs.open(snippet_file, 'r', encoding='utf-8')
    each = f.readlines()
    each = each[1:] # Skip the first line which is the utf-8 coding repeated
    str = u''.join(each)
    f.close()
    occurs = 1
    while ( occurs > 0): ( str, occurs ) = matchMiscPattern.subn(AnotherReplacement,str,MATCH_ALL)
    each = str.split(u'\n')
    while (not matchSignificantTex.search(each[-1])): each.pop()
    str = xtr + (u'\n'+xtr).join(each) + u'\n'
    return str
    
def getTitle(text, format='plain'):
    if format == 'html':
        return u'<h1>{0}</h1>'.format(text)
    elif format == 'md':
        return u'{0}\n=========='.format(text)
    elif format == 'tex':
        return u'    \\startmakeup\n    \\section{{{0}}}\n    \\stopmakeup'.format(text)
    return text

def getImage(xtr, lang, fid, res, format='plain'):
    img_link = '/'.join([api_url_jpg, lang, res, 'obs-{0}-{1}.jpg'.format(
                                                                 lang, fid)])
    if format == 'html':
        return u'<img src="{0}" />'.format(img_link)
    elif format == 'tex':
        return xtr + xtr + xtr + '{{\\externalfigure[{0}]}}'.format(img_link)
    return u''

def getFrame(xtr, text, format, texregname):
    if format == 'html':
        return u'<p>{0}</p>'.format(text)
    elif format == 'md':
        return u'\n{0}\n'.format(text)
    elif format == 'tex':
        return u'\n'.join([
                             xtr + xtr + u'\\placefigure[nonumber]',
                             xtr + xtr + xtr + u'{{\\copy\\{0}}}'.format(texregname)
                          ])
    return text

def getRef(xtr, place_ref_template, text, format='plain'):
    global body_json
    if format == 'html':
        return u'<em>{0}</em>'.format(text)
    elif format == 'md':
        return u'*{0}*'.format(text)
    elif format == 'tex':
        each = place_ref_template.safe_substitute(thetext=text).split(u'\n')
        return xtr + (u'\n'+xtr).join(each) + u'\n'
    return text

def export_matter(lang_message, format, img_res, lang):
    '''
    Exports JSON front/back matter to specificed format.
    '''
    j = u'\n\n'
    if format == 'tex':
        j = u'\n'
    tmpsplit = lang_message.split(u'\n')
    matter = [ ]
    global inItems
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
        single_line = matchUnderLinePattern.sub(ur'\\underbar{\1}',single_line,MATCH_ALL)
        single_line = matchHeadingLevelPattern.sub(ur'\1\\underbar{\\bf \2}\3',single_line,MATCH_ALL)
        single_line = matchBoldPattern.sub(ur'{\\bf \1}',single_line,MATCH_ALL)
        single_line = matchItalicPattern.sub(ur'{\\em \1}',single_line,MATCH_ALL)
        single_line = matchMonoPattern.sub(ur'{\\tt \1}',single_line,MATCH_ALL)
        single_line = matchPipePattern.sub(ur' \\textbar \\space ',single_line,MATCH_ALL)
        single_line = matchPatternLongURL.sub(ur'\\startplacefigure[location=nonumber]{\\startalignment[middle]{\\tfx{{\\goto{\1}[url(\1)]}}}\\stopalignment}\\stopplacefigure',single_line,MATCH_ALL)
        single_line = matchPatternURL.sub(ur'\\startplacefigure[location=nonumber]{\\startalignment[middle]{\\tfx{{\\goto{\1}[url(\1)]}}}\\stopalignment}\\stopplacefigure',single_line,MATCH_ALL)
        single_line = matchChapterVersePattern.sub(ur'~\1',single_line,MATCH_ALL)
        matter.append(single_line)
    return j.join(matter)

def start_of_physical_page(xtr):
    return u'\n'.join([xtr+u'%%START-OF-PHYSICAL-PAGE', xtr+u'\\vtop{'])

def end_of_physical_page(xtr):
    return u'\n'.join([xtr+u'}', xtr+u'%%END-OF-PHYSICAL-PAGE'])

def export(chapters_json, format, img_res, lang):
    global body_json
    '''
    Exports JSON to specificed format.
    '''
    spaces4 = u'    '
    j = u'\n\n'
    output = []
    if format == 'tex':
        j = u'\n'
        calc_vertical_need_snip = tex_load_snippet_file(spaces4,'introTeXtOBS-calculate-vertical-need-snippet.tex')
        calc_leftover_snip = tex_load_snippet_file(spaces4,'introTeXtOBS-calculate-leftover-snippet.tex')
        begin_loop = tex_load_snippet_file(spaces4,'introTeXtOBS-begin-adjust-loop.tex')
        in_leftover_snip = tex_load_snippet_file(spaces4+spaces4,'introTeXtOBS-calculate-leftover-snippet.tex')
        in_adjust_snip = tex_load_snippet_file(spaces4+spaces4,'introTeXtOBS-adjust-spacing-snippet.tex')
        end_loop = tex_load_snippet_file(spaces4,'introTeXtOBS-end-adjust-loop.tex')
        verify_snip = tex_load_snippet_file(spaces4,'introTeXtOBS-verify-vertical-space.tex')
        place_ref_snip = tex_load_snippet_file(spaces4,'introTeXtOBS-place-reference-snippet.tex')
        adjust_one_snip = calc_vertical_need_snip + calc_leftover_snip + verify_snip
        adjust_two_snip = calc_vertical_need_snip + begin_loop + in_leftover_snip + in_adjust_snip + end_loop + calc_leftover_snip + verify_snip
        adjust_one = Template(adjust_one_snip)
        adjust_two = Template(adjust_two_snip)
        place_ref_template = Template(place_ref_snip)
    ixchp = (-1)
    for chp in chapters_json:
        ixchp = 1 +  ixchp
        #if ((MAX_CHAPTERS > 0) and (ixchp >= MAX_CHAPTERS)): break
        if ((MAX_CHAPTERS > 0) and (ixchp >= MAX_CHAPTERS) and (lang != 'fr')): break
        output.append(getTitle(chp['title'], format))
        ixframe = (-1)
        ChapterFrames = chp['frames']
        nframe = len(ChapterFrames) 
        RefTextOnly = chp['ref']
        for fr in ChapterFrames:
            ixframe = 1 + ixframe
            ixlookahead = 1 + ixframe
            is_even = ((ixframe % 2) == 0)
            is_last_page = (is_even and ((ixframe + 2) >= nframe)) or ((not is_even) and ((ixframe + 1) >= nframe))
            page_is_full = (ixlookahead < nframe)
            TextOnly = fr['text']
            TextFrame = getFrame(spaces4, TextOnly, format, 'toptry' if is_even else 'bottry')
            ImageFrame = getImage(spaces4, lang, fr['id'], img_res, format)
            adjust_tex = adjust_two if (page_is_full) else adjust_one
            if format != 'tex':
                output.append(ImageFrame)
                output.append(TextFrame)
            else:
                AlsoReg = u'\\refneed' if (is_last_page) else u'\\EmptyString'
                NeedAlso = u'\\refneed + ' if (is_last_page) else u''
                pageword = u'LAST_PAGE' if (is_last_page) else u'CONTINUED'
                TruthIsLastPage = 'true' if (is_last_page) else 'false'
                if (not is_even):
                    output.append(spaces4 + spaces4 + u'\\vskip \\the\\leftover')
                elif (page_is_full):
                    nextfr = ChapterFrames[ixlookahead]
                    NextTextOnly = nextfr['text']
                    NextImageFrame = getImage(spaces4, lang, nextfr['id'], img_res, format)
                    texdict = dict(pageword=pageword,needalso=NeedAlso,alsoreg=AlsoReg,
                                   topimg=ImageFrame,botimg=NextImageFrame,
                                   lang=lang,fid=fr['id'],isLastPage=TruthIsLastPage,
                                   toptxt=TextOnly,bottxt=NextTextOnly,reftxt=RefTextOnly)
                    output.append(adjust_two.safe_substitute(texdict))
                else:
                    texdict = dict(pageword=pageword,needalso=NeedAlso,alsoreg=AlsoReg,
                                   topimg=ImageFrame,botimg='',
                                   lang=lang,fid=fr['id'],isLastPage=TruthIsLastPage,
                                   toptxt=TextOnly,bottxt='',reftxt=RefTextOnly)
                    output.append(adjust_one.safe_substitute(texdict))
                if (is_even):
                    output.append(start_of_physical_page(spaces4))
                output.append(spaces4 + spaces4 + u''.join([u'\message{FIGURE: ',lang,'-',fr['id'],'}']))
                output.append(TextFrame)
                output.append(ImageFrame)
                if ((not is_even) and (not is_last_page)):
                    output.append(end_of_physical_page(spaces4))
                    output.append(spaces4 + u'\\page[yes]')
        output.append(getRef(spaces4, place_ref_template, RefTextOnly, format))
        output.append(end_of_physical_page(spaces4))
        output.append(spaces4 + u'\\page[yes]')
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
    global body_json
    keyword = matchobj.group(1)
    if keyword in body_json.keys(): return body_json[keyword]
    return 'nothing'

def main(lang, outpath, format, img_res):
    global body_json
    toptmpf = getJSON(lang, 'obs-{0}-front-matter.json', '{0}-front-matter.tmp')
    bottmpf = getJSON(lang, 'obs-{0}-back-matter.json', '{0}-back-matter.tmp')
    lang_top_json = loadJSON(toptmpf, 'd')
    lang_bot_json = loadJSON(bottmpf, 'd')
    output_front = export_matter(lang_top_json['front-matter'], format, img_res, lang_top_json['language'])
    output_back = export_matter(lang_bot_json['back-matter'], format, img_res, lang_bot_json['language'])
    #
    jsonf = 'obs-{0}.json'.format(lang)
    lang_url = '/'.join([api_url_txt, lang, jsonf])
    tmpf = '/tmp/{0}'.format(jsonf)
    getURL(lang_url, tmpf)
    if not os.path.exists(tmpf):
       print "Failed to get JSON file."
       sys.exit(1)
    tmpf = getJSON(lang, jsonf, '{0}-body-matter.tmp')
    body_json = loadJSON(tmpf, 'd')
    checkForStandardKeysJSON()
    output = export(body_json['chapters'], format, img_res, body_json['language'])
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
            single_line = single_line.rstrip('\r\n') # .encode('utf-8')
            if (matchChaptersPattern.search(single_line)): outlist.append(output)
            elif (matchFrontMatterPattern.search(single_line)): outlist.append(output_front)
            elif (matchBackMatterPattern.search(single_line)): outlist.append(output_back)
            else:
                occurs = 1
                while ( occurs > 0): ( single_line, occurs ) = matchMiscPattern.subn(AnotherReplacement,single_line,MATCH_ALL)
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
