#coding:utf-8
from xml.etree import ElementTree as XmlTree
from xml.dom.minidom import Document
import lxml.html
import codecs
import chardet, urllib2
import re
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

doc = Document()
tpMap = {}
domains = set([
        'com.cn',
        'com',
        'cn',
        'jp',
        'info',
        'cc',
        'net',
        'org',
])

def init_tree(url):
    global tree
    html = urllib2.urlopen(url,timeout=30).read()
    mychar = chardet.detect(html)
    content = html
    bianma = mychar['encoding']
    print bianma
    #html=html.decode('utf-8','ignore').encode('utf-8')
    if bianma == 'utf-8' or bianma == 'UTF-8':
        content = html
        print "utf-8"
    elif bianma == 'gbk' or bianma == 'GBK' :
        print "gbk"
        content = html.decode('gbk','ignore').encode('gbk')
    elif bianma == 'gb2312' or bianma == 'GB2312':
        print "gb2312"
        content = html.decode('gb2312','ignore').encode('gb2312')
    tree = lxml.html.document_fromstring(content)
    print content

def getHost(host):
    items = host.split('.')
    for i in range(1,len(items)):
        if ".".join(items[i:]) in domains:
            return ".".join(items[i-1:])
def get_site(url):
    if url[:-1] == '/':
        url = url[:-1]
    url = url[7:]
    pos = url.find('/')
    if pos == -1:
        site = getHost(url)
    else:
        site = getHost(url[:pos])
    return site

def get_top_path(path):
    pos = path[3:].find('/')
    tpath = path[:(pos+3)]
    return tpath


def get_node_text(tree, tpMap, fieldname):
    try:
        if tpMap[fieldname]['path'] == "":
            node_text = ""
            return node_text
        else:
            path = tpMap[fieldname]['path'].split('|')
            node_text = ""
            for p in path:
                print p
                if 'trim_node' in tpMap[fieldname]:
                    tpath= get_top_path(p)
                    trim_node = tpMap[fieldname]['trim_node']
                    trimlist = trim_node.split('|')
                    for node in trimlist:
                        trim_path = tpath + '//' + node
                        for bad in tree.xpath(trim_path):
                            bad.getparent().remove(bad)
                lenth = len(tree.xpath(p))
##                print lenth
                if '@src' in p:
                    p = p[:-5]
                    for i in range(lenth):
                        print tree.xpath(p)[i].attrib['src']
                        if tree.xpath(p)[i].attrib['src'] not in node_text:
                            node_text += tree.xpath(p)[i].attrib['src']+'\n'
                if '@href' in p:
                    p = p[:-6]
                    for i in range(lenth):
                        if tree.xpath(p)[i].attrib['href'] not in node_text:
                            node_text += tree.xpath(p)[i].attrib['href']+'\n'
                if '@alt' in p:
                    p = p[:-5]
                    for i in range(lenth):
                        if tree.xpath(p)[i].attrib['alt'] not in node_text:
                            node_text += tree.xpath(p)[i].attrib['alt']+'\n'
                try:
                    if tpMap[fieldname]['type'] == "src":
                        for i in range(lenth):
                            if tree.xpath(p)[i].attrib['src'] not in node_text:
                                node_text += tree.xpath(p)[i].attrib['src']+'\n'
                    if tpMap[fieldname]['type'] == "href":
                        for i in range(lenth):
                            if tree.xpath(p)[i].attrib['href'] not in node_text:
                                node_text += tree.xpath(p)[i].attrib['href']+'\n'
                    if tpMap[fieldname]['type'] == "alt":
                        for i in range(lenth):
                            if tree.xpath(p)[i].attrib['alt'] not in node_text:
                                node_text += tree.xpath(p)[i].attrib['alt']+'\n'
                    if tpMap[fieldname]['type'] == "raw_text":
                        for i in range(lenth):
                            node_text += lxml.etree.tostring(tree.xpath(p)[i],encoding = "utf-8")                        
                    if tpMap[fieldname]['type'] == "image_text":
                        print "not support"
                except:
                    print ""
                if node_text == "":
                    for i in range(lenth):
                        if tree.xpath(p)[i].text_content() not in node_text:
                            node_text += tree.xpath(p)[i].text_content()
                if 'trim_prefix' in tpMap[fieldname]:
                    trim_prefix = tpMap[fieldname]['trim_prefix']
                    pos = node_text.find(trim_prefix)
                    if pos != -1:
                        lenp = len(trim_prefix)
                        node_text = node_text[(pos+lenp):]
                if 'trim_postfix' in tpMap[fieldname]:
                    trim_postfix = tpMap[fieldname]['trim_postfix']
                    pos = node_text.find(trim_postfix)
                    if pos != -1:
                        node_text = node_text[:pos]
    except:
        node_text = ""
    return (node_text.encode("UTF-8")).strip()
                
def fill_newtree(doc, page, fieldname):
    node = doc.createElement(fieldname)
    text = get_node_text(tree, tpMap, fieldname)
    print fieldname+":"+text
    node_text = doc.createTextNode(text)
    node.appendChild(node_text)
    page.appendChild(node)

def create_newDomTree(url):
    site = get_site(url)
##    parser = XmlTree.XMLParser(encoding="utf-8")
    file = codecs.open('./template/'+site+'.xml',encoding="utf-8").read()
##    xmlDoc = XmlTree.parse('./template/'+site+'.xml',parser=parser)
    xmlRoot = XmlTree.fromstring(file)
##    xmlRoot = xmlDoc.getroot()
    xmlsite = xmlRoot[0]
    global tpMap
    tpMap = {}
    for site_child in xmlsite:
        url_prefix = site_child.attrib
        k = re.match(url_prefix['name'], url)
        if k:
            print k.group(0)
            for field in site_child:
                fieldvalue = field.attrib
                tpMap[fieldvalue['name']] = fieldvalue
    ##create a new dom tree
    global doc
    doc = Document()
    pages = doc.createElement('pages')
    pages.setAttribute('xmlns:xsi',"http://www.w3.org/2001/XMLSchema-instance")
    pages.setAttribute('xsi:noNamespaceSchemaLocation','pages.xsd')
    doc.appendChild(pages)

    page = doc.createElement('page')
    page.setAttribute('url',url)
    page.setAttribute('mfg__tag__type','ucnews')
    pages.appendChild(page)

    fill_newtree(doc, page, 'title')
    fill_newtree(doc, page, 'original_title')
    fill_newtree(doc, page, 'intro')
    fill_newtree(doc, page, 'content')
    fill_newtree(doc, page, 'main_image_url')
    fill_newtree(doc, page, 'image_urls')
    fill_newtree(doc, page, 'main_rich_text')
    fill_newtree(doc, page, 'source_name')
    fill_newtree(doc, page, 'source_url')
    fill_newtree(doc, page, 'pub_time')
    fill_newtree(doc, page, 'first_category')
    fill_newtree(doc, page, 'second_category')
    fill_newtree(doc, page, 'breadcrumb')
    fill_newtree(doc, page, 'image_captions')
    fill_newtree(doc, page, 'tags')
    fill_newtree(doc, page, 'page_urls')
    fill_newtree(doc, page, 'image_content')

    ##write new dom tree to a file
    filename = os.path.basename(url)
    f = codecs.open('urlTemp/'+filename+'.xml', 'w', 'utf-8')
    f.write(doc.toprettyxml(indent = '\t'))
    f.close()

#url="http://news.qq.com/a/20140527/044619.htm"
#url="http://www.ce.cn/xwzx/gnsz/gdxw/201405/27/t20140527_2883205.shtml"
#url="http://www.huxiu.com/article/34291/1.html"
#url="http://www.chinanews.com/gn/2014/05-26/6213875.shtml"
#init_tree(url)
#create_newDomTree(url)
